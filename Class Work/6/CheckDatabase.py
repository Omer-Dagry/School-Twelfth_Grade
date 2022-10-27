import time
import datetime
import multiprocessing

from SynchronizedDatabase import SynchronizedDatabase


class CheckDatabase:
    def __init__(self):
        self.database = None

    def create_database(self, mode: int, range_end: int,
                        number_of_processes: int = multiprocessing.cpu_count(),
                        number_of_threads: int = multiprocessing.cpu_count(),
                        max_reads_together: int = 10):
        synchronized_database = SynchronizedDatabase(mode=mode,
                                                     number_of_processes=number_of_processes,
                                                     number_of_threads=number_of_threads,
                                                     max_reads_together=max_reads_together)
        synchronized_database.create_workers(range_end)
        synchronized_database.start_work()
        while synchronized_database.still_working():
            time.sleep(2)
        self.database = synchronized_database.get_database()

    def _check(self, mode: int, range_end: int,
               number_of_processes: int = multiprocessing.cpu_count(),
               number_of_threads: int = 20,
               max_reads_together: int = 10):
        result = True
        self.create_database(mode, range_end,
                             number_of_processes=number_of_processes,
                             number_of_threads=number_of_threads,
                             max_reads_together=max_reads_together)
        name = "Thread" if mode == 0 else "Process"
        range_ = range(1, number_of_threads) if mode == 0 else range(1, number_of_processes)
        all_keys = [f"{name}-{i}" for i in range_]
        range_ = range(range_end // 2, range_end) if mode == 0 else range(range_end // 2, range_end)
        for name in all_keys:
            for i in range_:
                try:
                    if self.database[f"{name} {i}"] != i:
                        print(f"Error, '{f'{name} {i}'}' != {i}")
                        result = False
                except KeyError:
                    print(f"Error, missing the key '{f'{name} {i}'}'")
                    result = False
        return result

    def check_multiprocessing_and_threading(self):
        # check threading
        start = datetime.datetime.now()
        print("Starting Check For Threading")
        result = self._check(0, 30)
        print("-" * 64)
        if not result:
            print(" " * 28 + "FAILED")
        else:
            print(" " * 28 + "PASSED\n")
        print(f"Time Passed: {datetime.datetime.now() - start}")
        # check multiprocessing
        start = datetime.datetime.now()
        print("Starting Check For Multiprocessing")
        result = self._check(1, 300)
        print("-" * 64)
        if not result:
            print(" " * 28 + "FAILED")
        else:
            print(" " * 28 + "PASSED\n")
        print(f"Time Passed: {datetime.datetime.now() - start}")


def main():
    database_checker = CheckDatabase()
    database_checker.check_multiprocessing_and_threading()


if __name__ == '__main__':
    main()
