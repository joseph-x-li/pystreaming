from collections import OrderedDict
from typing import Any, Tuple


class CircularOrderedDict:
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
        self.dict: OrderedDict[Any, Any] = OrderedDict()
        self.maxsize = maxsize

    def pop_front(self) -> Tuple[Any, Any]:
        """Pop key, value pair from front of dictionary.

        Returns:
            tuple: (key, value)
        """
        return self.dict.popitem(last=False)

    def insert_end(self, key: Any, value: Any) -> None:
        """Insert key-value pair into end of dictionary. If the key already
        exists, the key-value pair will be moved to the end of the dictionary
        and the value will be updated.

        Args:
            key (pyobj): Key in key-value pair.
            value (pyobj): Value in key-value pair.
        """
        if key in self.dict:
            self.dict.pop(key)
        self.dict[key] = value
        if len(self.dict) > self.maxsize:
            self.dict.popitem(last=False)

    def delete(self, key: Any) -> None:
        """Delete an entry from the dictionary

        Args:
            key (pyobj): Key to delete.
        """
        del self.dict[key]

    def keys(self) -> Any:  # Returns odict_keys which is not easily typed
        """Retrieve all keys in the dictionary, from earliest to latest.

        Returns:
            odict_keys: Iterable object of keys.
        """
        return self.dict.keys()

    def __len__(self) -> int:
        """Number of key-value pairs in the dictionary.

        Returns:
            int: Number of k-v pairs.
        """
        return len(self.dict)

    def __setitem__(self, key: Any, value: Any) -> None:
        """Update a key-value pair, without changing its position in the
        dictionary.

        Args:
            key (pyobj): Key in the key-value pair.
            value (pyobj): Value in key-value pair.

        Raises:
            KeyError: Key was not found in the dictionary.
        """
        if key not in self.dict:
            raise KeyError(str(key) + " use insert_end to add an element")
        self.dict[key] = value

    def __getitem__(self, key: Any) -> Any:
        """Retrieve a value from the dictionary.

        Args:
            key (pyobj): Key in the key-value pair.

        Returns:
            pyobj: Value in the key-value pair, if the key exists.
        """
        return self.dict[key]

    def __repr__(self) -> str:
        return self.dict.__repr__()
