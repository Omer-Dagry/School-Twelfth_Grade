import datetime
import hashlib
import itertools
import multiprocessing
import time

ABC = "abcdefghigklmnopqrstuvwxyz"
NUMBERS = "1234567890"
SIGNS = "!?:|\\/.,<>;'@#$%^&*(){}[]~`" + '"'
# 3735928559


def check(asdfasdf):
    pass


def hello(repeat):
    md5_hash = "EC9C0F7EDCC18A98B1F31853B1813301".lower()
    message = ""
    print(datetime.datetime.now())
    for option in itertools.product(NUMBERS, repeat=repeat):
        if hashlib.md5("".join(option).encode('utf-8')).hexdigest() == md5_hash:
            message = "".join(option)
            break
    print(datetime.datetime.now())
    print(message)


def main():
    for i in range(6):
        p = multiprocessing.Process(target=hello, args=(i + 9,), daemon=True)
        p.start()
    while multiprocessing.active_children():
        pass


if __name__ == '__main__':
    main()