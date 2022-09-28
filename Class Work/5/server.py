import itertools
import socket
import threading


ABC = "abcdefghigklmnopqrstuvwxyz"
NUMBERS = "1234567890"
SIGNS = "!?:|\\/.,<>;'@#$%^&*(){}[]~`" + '"'


def main():
    for option in itertools.product(ABC + NUMBERS, repeat=10):
        pass


if __name__ == '__main__':
    main()
