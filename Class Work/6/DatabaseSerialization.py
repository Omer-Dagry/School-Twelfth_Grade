import multiprocessing
import threading

from BaseDatabase import BaseDatabase
from typing import *


class DatabaseSerialization(BaseDatabase):
    def __init__(self,
                 mode: int = 1,
                 number_of_processes: int = multiprocessing.cpu_count(),
                 number_of_threads: int = 20,
                 max_reads_together: int = 10):
        if mode not in [0, 1]:
            raise ValueError("the arg 'mode' can be 0 or 1, 0 for threads, 1 for processes.")
        super().__init__(max_reads_together=max_reads_together)
        self.number_of_processes = number_of_processes
        self.number_of_threads = number_of_threads
        pool: list[Union[multiprocessing.Process, threading.Thread]] = []
        if mode == 0:
            for i in range(self.number_of_threads):
                thread = threading.Thread(target=,
                                          args=(,),
                                          daemon=True)
                pool.append(thread)
        else:
            for i in range(self.number_of_processes):
                process = multiprocessing.Process(target=,
                                                  args=(,),
                                                  daemon=True)
                pool.append(process)


# import pickle
#
#
# with open('var.txt', 'wb') as f:
#     var = {1: 'a', 2: 'b'}
#     pickle.dump(var, f)
