import eel
import gevent


def main():
    eel.init("webroot")
    eel.main()
    eel.start("index.html")


if __name__ == '__main__':
    main()
