class Empty(Exception):
    """Raised when trying to pop from an empty queue"""

    def __init__(self, calltype):
        super().__init__(f"Tried to pop from an empty {calltype}")


class CircularList:
    """Fixed size list with push-overwrite capabilities."""

    def __init__(self, maxsize=10):
        """Initialize a Circular List with maximum size.

        Args:
            maxsize (int, optional): Maximum number of elements the list
                can store before it begins to overwrite old elements.
                Defaults to 10.

        Raises:
            ValueError: Raised if maxsize argument is not a positve integer.
        """
        if maxsize <= 0:
            raise ValueError("Maxsize must be greater than zero")

        self._front = 0  # inclusive
        self._back = 0  # exclusive
        self.size = 0

        self.maxsize = maxsize
        self._array = [None] * maxsize

    def push(self, item):
        """Push an element FIFO (queue) style.

        Args:
            item (pyobj): Object to push.
        """
        if self.size == self.maxsize:  # overwrite old elements
            assert self._front == self._back
            self._array[self._back] = item
            self._back = (self._back + 1) % self.maxsize
            self._front = (self._front + 1) % self.maxsize
        else:
            self._array[self._back] = item
            self._back = (self._back + 1) % self.maxsize
            self.size += 1

    def pop(self):
        """Pop an element off FIFO (queue) style.

        Raises:
            Empty: Raised when there are no elements in the queue.

        Returns:
            pyobj: The first element in the list.
        """
        if self.size == 0:
            raise Empty(self.__class__.__name__)
        else:
            ret = self._array[self._front]
            self.size -= 1
            self._front = (self._front + 1) % self.maxsize
            return ret

    def __len__(self):
        return self.size

    def __getitem__(self, idx):
        """Gets the nth element of the list.
        Elements at the front of the list (would be popped off) are at index 0.

        Args:
            idx (int): Index desired to be modified.

        Raises:
            IndexError: Raise if the index is out of range.

        Returns:
            pyobj: The object desired.
        """
        if idx >= self.size or idx < 0:
            raise IndexError(f"list index {idx} out of range: [0, {self.size})")
        return self._array[(self._front + idx) % self.maxsize]

    def __setitem__(self, idx, new_val):
        """Sets the nth element of the list.
        Elements at the front of the list (would be popped off) are at index 0.

        Args:
            idx (int): Index desired to be modified.
            new_val (pyobj): New object to emplace.

        Raises:
            IndexError: Raise if the index is out of range.
        """
        if idx >= self.size or idx < 0:
            raise IndexError(f"list index {idx} out of range: [0, {self.size})")
        self._array[(self._front + idx) % self.maxsize] = new_val

    def __repr__(self):
        return self._array.__repr__() + f" front: {self._front} back: {self._back}"

    def full(self):
        """Check whether the current list size is the maximum size.

        Returns:
            boolean: True if full else False.
        """
        return self.size == self.maxsize
