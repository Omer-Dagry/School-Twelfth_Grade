import os
import rsa
import socket
import datetime

import cProfile
import pstats

from aes import AESCipher
from protocol_socket import EncryptedProtocolSocket


def recvall(buffsize: int, sock: socket.socket) -> bytes:
    data = b""
    while len(data) < buffsize:
        data += sock.recv(buffsize - len(data))
    return data


def recv_message(sock: socket.socket, aes: AESCipher) -> bytes:
    data_length = int(recvall(30, sock).decode().strip())
    return aes.decrypt(recvall(data_length, sock))


def recvall_no_encryption(buffsize: int, sock: socket.socket) -> bytes:
    data = b""
    while len(data) < buffsize:
        data += sock.recv(buffsize - len(data))
    return data


def send_message(data: bytes, sock: socket.socket, aes: AESCipher) -> None:
    data = aes.encrypt(data)
    sock.sendall(f"{len(data)}".ljust(30).encode())
    sock.sendall(data)


def exchange_aes_key(sock: socket.socket, aes_key: bytes) -> None:
    server_public_key_len = int(recvall_no_encryption(30, sock).decode().strip())
    server_public_key = rsa.PublicKey.load_pkcs1(recvall_no_encryption(server_public_key_len, sock), "PEM")
    #
    enc_key = rsa.encrypt(aes_key, server_public_key)
    sock.sendall(f"{len(enc_key)}".ljust(30).encode() + enc_key)


def main_regular():
    aes_key = os.urandom(16)
    aes_cipher = AESCipher(aes_key)
    s = socket.socket()
    s.connect(("127.0.0.1", 8820))
    print("connected")
    exchange_aes_key(s, aes_key)
    print("finished exchanging")
    with open("C:\\Users\\omerd\\Downloads\\Postman-win64-Setup.exe", "rb") as f:
        data = f.read()
    print(f"{len(data) = }")
    start_time = datetime.datetime.now()
    print(f"{start_time}")
    send_message(data, s, aes_cipher)
    msg = recv_message(s, aes_cipher)
    print(f"{len(msg) = }")
    print(f"{msg == data}")
    end_time = datetime.datetime.now()
    print(f"{end_time}\n{end_time - start_time}")
    s.close()


def main():
    s = EncryptedProtocolSocket()
    s.connect(("127.0.0.1", 8820))
    with open("C:\\Users\\omerd\\Downloads\\Postman-win64-Setup.exe", "rb") as f:
        data = f.read()
    print(f"{len(data) = }")
    start_time = datetime.datetime.now()
    print(f"{start_time}")
    print(s.send_message(data))
    msg = s.receive_message()
    end_time = datetime.datetime.now()
    print(f"{end_time}\n{end_time - start_time}")
    print(f"{len(msg) = }")
    s.close()


if __name__ == '__main__':
    with cProfile.Profile() as pr:
        main_regular()

    stats = pstats.Stats(pr)
    stats.sort_stats(pstats.SortKey.TIME)
    stats.dump_stats(filename="aes_stats.prof")
