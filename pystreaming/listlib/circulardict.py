from collections import OrderedDict
from collections.abc import KeysView
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


class CircularOrderedDict(Generic[K, V]):
    def __init__(self, maxsize: int) -> None:
        """A dictionary that never exceeds a given size. If the size limit is reached,
        the least recently inserted element is removed.

        Args:
            maxsize (int): Maximum size of the dictionary.

        Raises:
            ValueError: Raised if maxsize argument is not a positive integer.
        """
        if maxsize <= 0:
            raise ValueError("Maxsize must be greater than zero")
        self.dict: OrderedDict[K, V] = OrderedDict()
        self.maxsize = maxsize

    def pop_front(self) -> tuple[K, V]:
        """Pop key, value pair from front of dictionary.

        Returns:
            tuple: (key, value)
        """
        return self.dict.popitem(last=False)

    def insert_end(self, key: K, value: V) -> None:
        """Insert key-value pair into end of dictionary. If the key already
        exists, the key-value pair will be moved to the end of the dictionary
        and the value will be updated.

        Args:
            key (K): Key in key-value pair.
            value (V): Value in key-value pair.
        """
        if key in self.dict:
            self.dict.pop(key)
        self.dict[key] = value
        if len(self.dict) > self.maxsize:
            self.dict.popitem(last=False)

    def delete(self, key: K) -> None:
        """Delete an entry from the dictionary

        Args:
            key (pyobj): Key to delete.
        """
        del self.dict[key]

    def keys(self) -> KeysView[K]:
        """Retrieve all keys in the dictionary, from earliest to latest.

        Returns:
            KeysView[K]: Iterable object of keys.
        """
        return self.dict.keys()

    def __len__(self) -> int:
        """Number of key-value pairs in the dictionary.

        Returns:
            int: Number of k-v pairs.
        """
        return len(self.dict)

    def __setitem__(self, key: K, value: V) -> None:
        """Update a key-value pair, without changing its position in the
        dictionary.

        Args:
            key (K): Key in the key-value pair.
            value (V): Value in key-value pair.

        Raises:
            KeyError: Key was not found in the dictionary.
        """
        if key not in self.dict:
            raise KeyError(str(key) + " use insert_end to add an element")
        self.dict[key] = value

    def __getitem__(self, key: K) -> V:
        """Retrieve a value from the dictionary.

        Args:
            key (pyobj): Key in the key-value pair.

        Returns:
            pyobj: Value in the key-value pair, if the key exists.
        """
        return self.dict[key]

    def __repr__(self) -> str:
        return self.dict.__repr__()
