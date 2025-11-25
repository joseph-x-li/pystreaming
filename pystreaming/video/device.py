import multiprocessing as mp
from collections.abc import Callable
from typing import Any


class Device:
    def __init__(
        self,
        dfunc: Callable[..., None],
        dkwargs: dict[str, Any],
        nproc: int,
    ) -> None:
        """Background running device.

        Args:
            dfunc (function): Function to run in background.
                Must have 'shutdown' and 'barrier' as arguments.
            dkwargs (dict): Kwargs to pass to dfunc.
            nproc (int): Number of background processes to launch.
        """
        assert isinstance(dkwargs, dict)  # we only pass in arguments as kwargs
        assert nproc > 0
        self.dfunc, self.dkwargs, self.nproc = dfunc, dkwargs, nproc
        self.barrier = mp.Barrier(nproc + 1, timeout=3)
        self.shutdown = mp.Event()
        dkwargs["barrier"] = self.barrier
        dkwargs["shutdown"] = self.shutdown
        self.processes: list[mp.Process] = []

    def start(self) -> None:
        """Start background processes. Does nothing if already started."""
        if self.processes != []:
            return
        for _ in range(self.nproc):
            self.processes.append(mp.Process(target=self.dfunc, kwargs=self.dkwargs))
        for ps in self.processes:
            ps.daemon = True
            ps.start()
        try:
            self.barrier.wait()
        except mp.BrokenBarrierError:  # type: ignore[attr-defined]
            # Clean up processes if barrier times out
            self.shutdown.set()
            for ps in self.processes:
                ps.join(timeout=1)
            self.processes = []
            self.shutdown.clear()
            raise RuntimeError(
                "Failed to start device processes: barrier timeout. "
                "Processes may have failed to initialize."
            ) from None

    def stop(self) -> None:
        """Stop background processes. Does nothing if already stopped."""
        if self.processes == []:
            return
        self.shutdown.set()
        for ps in self.processes:
            ps.join(timeout=5)
            if ps.is_alive():
                # Process didn't terminate gracefully, force terminate
                ps.terminate()
                ps.join(timeout=1)
                if ps.is_alive():
                    # Still alive, kill it
                    ps.kill()
                    ps.join()
        self.processes = []
        self.shutdown.clear()
