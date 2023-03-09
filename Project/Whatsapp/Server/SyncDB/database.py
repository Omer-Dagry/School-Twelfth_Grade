from typing import *


class Database:
    __slots__ = ("__database", "__dict__")

    def __init__(self):
        self.__database = {}

    def set_database(self, dic: dict) -> bool:
        """ set self.__database """
        self.__database = dic
        return True

    def get_database(self) -> dict:
        """ get self.__database """
        return self.__database

    def __setitem__(self, key: Hashable, val: Any):
        """ add key: val """
        self.__database[key] = val

    def safe_set(self, key: Hashable, val: Any) -> bool:
        """ add key: val, only if key is not already in database """
        if key in self.__database:
            return False
        self.__database[key] = val
        return True

    def __getitem__(self, key: Hashable) -> Any:
        """ get the val of key """
        if key in self.__database.keys():
            val = self.__database[key]
            return val
        else:
            raise KeyError(f"{key} isn't a key in the __database.")

    def pop(self, key: Hashable) -> Any:
        """ remove key and self.__database[key] value """
        if key in self.__database.keys():
            return self.__database.pop(key)
        else:
            raise KeyError(f"{key} isn't a key in the __database.")

    def get(self, key: Hashable) -> Any | None:
        """ get a value, if it doesn't exist, return None."""
        return self.__database.get(key)

    def __contains__(self, key: Hashable) -> bool:
        """ return True if key exists in __database else False """
        return key in self.__database


_ = Database()
_["hello"] = 5  # check set_value
assert _["hello"] == 5  # check get_value
assert _.pop("hello") == 5  # check pop_value
_.set_database({"hi": 6, "bye": 5})  # check set_database
assert _.get_database() == {"hi": 6, "bye": 5}  # check get_database
del _
