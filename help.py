import datetime
import hashlib
import itertools
import multiprocessing
import time

ABC = "abcdefghigklmnopqrstuvwxyz"
NUMBERS = "1234567890"
SIGNS = "!?:|\\/.,<>;'@#$%^&*(){}[]~`" + '"'
# 3735928559


def hello(repeat):
    pass


def main():
    for i in range(6):
        p = multiprocessing.Process(target=hello, args=(i + 9,), daemon=True)
        p.start()
    while multiprocessing.active_children():
        pass


if __name__ == '__main__':
    main()