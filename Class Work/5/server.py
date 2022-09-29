import datetime
import itertools
import socket
import threading


MD5_HASH = "EC9C0F7EDCC18A98B1F31853B1813301".lower()
NUMBERS = "0123456789"


def main():
    start = datetime.datetime.now()
    print(start)
    for option in itertools.product(NUMBERS, repeat=10):
        pass
    print(datetime.datetime.now() - start)


if __name__ == '__main__':
    main()
