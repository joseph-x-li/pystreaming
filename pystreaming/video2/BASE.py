import multiprocessing as mp


class Device:
    def __init__(self, dfunc, dkwargs, nproc):
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
        self.processes = []

    def start(self):
        """Start background processes. Does nothing if already started."""
        if self.processes != []:
            return
        for _ in range(self.nproc):
            self.processes.append(mp.Process(target=self.dfunc, kwargs=self.dkwargs))
        for ps in self.processes:
            ps.daemon = True
            ps.start()
        self.barrier.wait()

    def stop(self):
        """Stop background processes. Does nothing if already stopped."""
        if self.processes == []:
            return
        self.shutdown.set()
        for ps in self.processes:
            ps.join()
        self.processes = []
        self.shutdown.clear()
