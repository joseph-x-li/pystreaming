from threading import Lock
from collections import OrderedDict
from orderedset import OrderedSet


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
        """
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
            Empty: Raised when there are no elements in the queue

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
            IndexError: Raise if the index is out of range

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
            IndexError: Raise if the index is out of range
        """
        if idx >= self.size or idx < 0:
            raise IndexError(f"list index {idx} out of range: [0, {self.size})")
        self._array[(self._front + idx) % self.maxsize] = new_val

    def __repr__(self):
        return self._array.__repr__() + f" front: {self._front} back: {self._back}"

    def full(self):
        """Check whether the current list size is the maximum size

        Returns:
            boolean: True if full else False
        """
        return self.size == self.maxsize


# Classes below are either unneeded or need to be updated.


class BufferedCList(CircularList):
    """Subclass of CircularList that introduces the concept of a frame buffer"""

    def __init__(self, *args, buffer=5, **kwargs):
        super().__init__(*args, **kwargs)
        if buffer >= self.maxsize:
            raise ValueError(
                f"buffer:{buffer} must be strictly less than maxsize: {self.maxsize}"
            )
        self.threshold = self.maxsize - buffer

    def at_threshold(self):
        return self.size >= self.threshold


class SafeCList(CircularList):
    """A thread-safe wrapper of the base class CircularList"""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.access_lock = Lock()

    def push(self, item):
        with self.access_lock:
            super().push(item)

    def pop(self):
        with self.access_lock:
            return super().pop()

    def __getitem__(self, idx):
        with self.access_lock:
            return super().__getitem__(idx)

    def __setitem__(self, idx, new_val):
        with self.access_lock:
            super().__setitem__(idx, new_val)


class CircularOrderedDict:
    def __init__(self, maxsize):
        self.dict = OrderedDict()
        self.maxsize = maxsize

    def pop_front(self):
        return self.dict.popitem(last=False)

    def insert_end(self, key, value):
        # Insert key-value pair. If key exists, it is moved to the back and updated.
        if key in self.dict:
            self.dict.pop(key)
        self.dict[key] = value
        if len(self.dict) > self.maxsize:
            self.dict.popitem(last=False)

    def delete(self, key):
        del self.dict[key]

    def keys(self):
        return self.dict.keys()

    def __len__(self):
        return len(self.dict)

    def __setitem__(self, key, value):
        if key not in self.dict:
            raise KeyError(key) + " use insert_end to add an element"
        self.dict[key] = value

    def __getitem__(self, key):
        return self.dict[key]

    def __repr__(self):
        return self.dict.__repr__()


class BufferedCOD(CircularOrderedDict):
    def __init__(self, *args, buffer=5, **kwargs):
        super().__init__(*args, **kwargs)
        assert 0 <= buffer and buffer < self.maxsize
        self.threshold = self.maxsize - buffer

    def pop_front(self):
        if len(self.dict) > self.threshold:
            return super().pop_front()
        return None


class CircularOrderedSet(OrderedSet):
    def __init__(self, maxsize):
        super().__init__()
        self.maxsize = maxsize

    def push(self, item):
        if item in self:
            self.remove(item)
        self.add(item)
        while len(self) > self.maxsize:
            self.pop(last=False)
