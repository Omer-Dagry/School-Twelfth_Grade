import time

from protocol_socket import EncryptedProtocolSocket


def main():
    for _ in range(2):
        s = EncryptedProtocolSocket()
        s.connect(("127.0.0.1", 8820))
        s.send_message("haahahhaha".encode())
        time.sleep(0.05)
        s.close()


if __name__ == '__main__':
    main()
