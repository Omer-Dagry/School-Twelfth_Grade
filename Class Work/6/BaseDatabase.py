import multiprocessing
import time
from typing import *


# edit_and_read_lock._semlock._get_value()  # 1 not acquired, 0 acquired
# semaphore.get_value()  # number of left places
class BaseDatabase:
    def __init__(self, max_reads_together: int = 10):
        self.dic = {}
        self.max_reads_together = max_reads_together
        self.edit_and_read_lock = multiprocessing.Semaphore(1)
        self.semaphore = multiprocessing.Semaphore(self.max_reads_together)

    def set_value(self, key: Hashable, val: Any) -> bool:
        try:
            # pickup edit and read lock
            self.edit_and_read_lock.acquire()
            # wait until every one who was already reading is done
            while self.semaphore.get_value() != self.max_reads_together:
                time.sleep(0.1)  # prevent high cpu usage
            # here there is no one reading and or writing, so we can set key: val
            self.dic[key] = val
            return True
        except Exception:
            return False

    def get_value(self, key: Hashable) -> Any:
        # wait until no one is editing the dictionary
        while self.edit_and_read_lock.get_value() != 1:
            time.sleep(0.1)  # prevent high cpu usage
        self.semaphore.acquire()
        if key in self.dic.keys():
            val = self.dic[key]
        else:
            val = None
        self.semaphore.release()
        return val

    def delete_value(self, key: Hashable) -> Any:
        # remove key from dic or turn the value of key to None?
        pass
