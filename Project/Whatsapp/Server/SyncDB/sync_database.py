import os
import pickle
import threading
import multiprocessing

from typing import *
from .file_database import FileDatabase


class SyncDatabase:
    def __init__(self, database: FileDatabase, mode: bool, max_reads_together: int = 10):
        """ mode: True -> multiprocessing, False -> threading """
        #
        # check that database is FileDatabase
        if not isinstance(database, FileDatabase):
            raise ValueError("the arg '__database' is an instance of FileDatabase.")
        # check that the mode is valid
        if not isinstance(mode, bool):
            raise ValueError("the arg 'mode' can be True or False, False for threads, True for processes.")
        # set params
        self.__database = database
        self.__mode = mode
        self.__max_reads_together = max_reads_together
        # set semaphores according to mode
        if self.__mode:
            self.__edit_lock = multiprocessing.Lock()
            self.__semaphore = multiprocessing.Semaphore(self.__max_reads_together)
        else:
            self.__edit_lock = threading.Lock()
            self.__semaphore = threading.Semaphore(self.__max_reads_together)

    def keys(self):
        """ get all keys """
        self.__semaphore.acquire()
        keys = self.__database.get_database().keys()
        self.__semaphore.release()
        return keys

    def values(self):
        """ get all values """
        self.__semaphore.acquire()
        values = self.__database.get_database().values()
        self.__semaphore.release()
        return values

    def items(self):
        """ get all keys and values """
        self.__semaphore.acquire()
        items = self.__database.get_database().items()
        self.__semaphore.release()
        return items

    def __setitem__(self, key: Hashable, val: Any) -> bool:
        """ set a value """
        # pickup edit lock
        self.__edit_lock.acquire()
        # acquire all the semaphore
        for _ in range(self.__max_reads_together):
            self.__semaphore.acquire()
        # here there is no one reading and or writing, so we can set key: val
        ok = self.__database[key] = val
        # release the edit lock
        self.__edit_lock.release()
        # release all the semaphore
        for _ in range(self.__max_reads_together):
            self.__semaphore.release()
        return ok

    def safe_set(self, key: Hashable, val: Any) -> bool:
        """ add key: val, only if key is not already in database """
        # pickup edit lock
        self.__edit_lock.acquire()
        # acquire all the semaphore
        for _ in range(self.__max_reads_together):
            self.__semaphore.acquire()
        # here there is no one reading and or writing, so we can set key: val if key not already in database
        if key not in self.__database:
            result = False
        else:
            result = True
            self.__database[key] = val
        # release the edit lock
        self.__edit_lock.release()
        # release all the semaphore
        for _ in range(self.__max_reads_together):
            self.__semaphore.release()
        return result

    def add(self, key: Hashable, val: list[Any]):
        """
            extends the list of current_val with val
            (if current_val isn't a list it will become [current_val] and then it will be extended)

            key: current_val -> key: [current_val, *val]
            key: [current_values, ...] -> key: [current_values, ..., *val]
        """
        # pickup edit lock
        self.__edit_lock.acquire()
        # acquire all the semaphore
        for _ in range(self.__max_reads_together):
            self.__semaphore.acquire()
        current_val = self.__database[key]
        if not isinstance(current_val, list):
            current_val = [current_val]
        current_val.extend(val)
        self.__database[key] = current_val
        # release the edit lock
        self.__edit_lock.release()
        # release all the semaphore
        for _ in range(self.__max_reads_together):
            self.__semaphore.release()

    def remove(self, key: Hashable, val: Any) -> bool:
        """
            removes val from the list of current_val
            (if current_val isn't a list it will become [current_val])

            key: current_val -> key: [current_val]
            key: [current_values, ...] -> key: [current_values, ...]
            if val in current_val -> remove val
            :return: True if val was in the list of values and was removed else False
        """
        # pickup edit lock
        self.__edit_lock.acquire()
        # acquire all the semaphore
        for _ in range(self.__max_reads_together):
            self.__semaphore.acquire()
        current_val = self.__database[key]
        if not isinstance(current_val, list):
            current_val = [current_val]
        if val not in current_val:
            result = False
        else:
            result = True
            current_val.remove(val)
            self.__database[key] = current_val
        # release the edit lock
        self.__edit_lock.release()
        # release all the semaphore
        for _ in range(self.__max_reads_together):
            self.__semaphore.release()
        return result

    def __getitem__(self, key: Hashable) -> Any:
        """ get a value """
        self.__semaphore.acquire()
        try:
            val = self.__database[key]
        # make sure that the lock is released even if KeyError raised
        except KeyError:
            self.__semaphore.release()
            raise
        # release the lock
        self.__semaphore.release()
        return val

    def pop(self, key: Hashable) -> Any:
        """ remove a value """
        # pickup edit lock
        self.__edit_lock.acquire()
        # acquire all the semaphore
        for _ in range(self.__max_reads_together):
            self.__semaphore.acquire()
        # here there is no one reading and or writing, so we can pop the key
        try:
            val = self.__database.pop(key)
        # make sure that the lock is released even if KeyError raised
        except KeyError:
            self.__edit_lock.release()
            # release all the semaphore
            for _ in range(self.__max_reads_together):
                self.__semaphore.release()
            raise
        # release the lock
        self.__edit_lock.release()
        # release all the semaphore
        for _ in range(self.__max_reads_together):
            self.__semaphore.release()
        return val

    def get(self, key: Hashable) -> Any | None:
        """ get a value, if it doesn't exist, return None."""
        self.__semaphore.acquire()
        result = self.__database.get(key)
        self.__semaphore.release()
        return result

    def __contains__(self, key: Hashable) -> bool:
        self.__semaphore.acquire()
        result = key in self.__database
        self.__semaphore.release()
        return result


# because each process has its own memory, this file will be imported
# by x processes, so the file name of the __database can't be the same
# for all the processes, or they will interfere with each other in the
# asserts because every action affects the file of the __database and there
# are x number of processes that will import this file simultaneously
file_name = f"####test####{os.getpid()}"
__ = FileDatabase(file_name)
try:
    _ = SyncDatabase(__, True)
    _["hello"] = 5  # check set_value & write & read
    assert _["hello"] == 5  # check get_value & read
    assert _.pop("hello") == 5  # check pop_value & write & read
    _["hi"] = 6
    _["bye"] = 5
    assert _["hi"] == 6 and _["bye"] == 5
    del _
    # check final result
    with open(file_name, "rb") as test_file:
        _ = pickle.load(test_file)
    assert _ == {"hi": 6, "bye": 5}
    del _, __
except BaseException as exception:
    raise exception
finally:
    os.remove(file_name)
    del file_name
