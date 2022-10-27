import pickle

from typing import *
from BaseDatabase import BaseDatabase


class Database(BaseDatabase):
    def __init__(self):
        super().__init__()
        with open("database", "wb") as database_file:
            database_file.write(b"")

    def write_database(self):
        """ Write self.database to a file using pickle """
        with open("database", "wb") as database_file:
            data = pickle.dumps(self.database)
            database_file.write(data)
        self.read_database()

    def read_database(self):
        """ Read database file with pickle and set self.database """
        with open("database", "rb") as database_file:
            try:
                dic = pickle.load(database_file)
            except EOFError:
                dic = {}
        ok = self.set_database(dic)
        while not ok:
            ok = self.set_database(dic)

    def get_database(self) -> dict:
        """ Override & read from database before returning the database"""
        self.read_database()
        return super().get_database()

    def __setitem__(self, key: Hashable, val: Any) -> bool:
        """ Override & add read & write database with pickle """
        self.read_database()
        ok = super().__setitem__(key, val)
        self.write_database()
        return ok

    def set_value(self, key: Hashable, val: Any) -> bool:
        """ Override & add read & write database with pickle """
        return self.__setitem__(key, val)

    def pop(self, key: Hashable) -> Any:
        """ Override & add read & write database with pickle """
        self.read_database()
        val = super().pop(key)
        self.write_database()
        return val

    def __getitem__(self, key: Hashable) -> Any:
        """ Override & add read database with pickle """
        self.read_database()
        return super().__getitem__(key)

    def get_value(self, key: Hashable) -> Any:
        """ Override & add read database with pickle """
        return self.__getitem__(key)
