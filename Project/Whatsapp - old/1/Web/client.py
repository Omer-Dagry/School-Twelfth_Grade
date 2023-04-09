import eel
import sys
import gevent


def close_callback(*args):
    print("hi")
    sys.exit()


def main():
    eel.init("webroot")
    eel.start("index.html")


if __name__ == '__main__':
    main()
