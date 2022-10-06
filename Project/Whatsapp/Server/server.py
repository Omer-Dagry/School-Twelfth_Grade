"""
###############################################
Author: Omer Dagry
Mail: omerdagry@gmail.com
Date: 05/10/2022 (dd/mm/yyyy)
###############################################
username & password can't end with space
each client gets a thread that handles him
###############################################
protocol:
login:
encrypt with password
len_msg.rjust(120, " ") + "login".rjust(32, " ") + username.rjust(32, " ") +
len_of_encrypted_password.rjust(32, " ") + aes_encryption(password.rjust(32, " ")
-----------------------------------------------
signup:
encrypt with hash(username + a constant string)
len_msg.rjust(120, " ") + "signup".rjust(32, " ") + username.rjust(32, " ") +
len_of_encrypted_password.rjust(32, " ") + aes_encryption(password.rjust(32, " ")
-----------------------------------------------
the rest:
msg_types: msg, image, delete for me, delete for everyone, in chat
encrypt with the password of the user
len_encrypted_data.rjust(120, " ") + aes_encryption(msg_type.rjust(32, " ") + send_to.rjust(32, " ") +
                                                    str(len(msg)).rjust(100, " ") + msg)
###############################################
"""
import base64
import hashlib
import socket
import threading

from Crypto import Random
from Crypto.Cipher import AES
from typing import *


# Constants
IP = "127.0.0.1"
PORT = 8820

# Globals
clients_sockets = []
lock = threading.Lock()


class AESCipher:
    def __init__(self, key):
        self.bs = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw: str, file_data: bytes = None) -> bytes:
        raw = self.to_ascii_values(raw)
        if file_data is None:
            raw = self.pad(raw.encode())
        else:
            file_data = b"file:" + file_data
            raw = self.pad(raw.encode() + file_data)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc: bytes) -> tuple[str, Union[bytes, None]]:
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self.to_ascii_chars(self.unpad(cipher.decrypt(enc[AES.block_size:])))

    def pad(self, s: Union[str, bytes]) -> Union[str, bytes]:
        if s is str:
            return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)
        else:
            return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs).encode()

    @staticmethod
    def unpad(s: Union[str, bytes]) -> Union[str, bytes]:
        return s[:-ord(s[len(s)-1:])]

    @staticmethod
    def to_ascii_values(data: str) -> str:
        data_ascii = [str(ord(char)) for char in data]
        return ",".join(data_ascii)

    @staticmethod
    def to_ascii_chars(data_ascii: bytes) -> tuple[str, Union[bytes, None]]:
        if b"file:" in data_ascii:
            file_data = b"file:".join(data_ascii.split(b"file:")[1:])  # get file data
            list_data_ascii = data_ascii.split(b"file:")[0].decode().split(",")  # get msg metadata
            return "".join([chr(int(char)) for char in list_data_ascii if char != ""]), file_data[5:]
        else:
            list_data_ascii = data_ascii.decode().split(",")
            return "".join([chr(int(char)) for char in list_data_ascii if char != ""]), None


def start_server() -> socket.socket:
    server_socket = socket.socket()
    server_socket.bind((IP, PORT))
    print("Server Is Up!!")
    server_socket.listen()
    return server_socket


def send_all(sock: socket.socket, msg: bytes) -> bool:
    try:
        sent_amount = 0
        while sent_amount != len(msg):
            sent_amount += sock.send(msg[sent_amount:])
        return True
    except (ConnectionError, socket.error):
        return False


def receive_all(sock: socket.socket, data_len: int) -> bytes:
    try:
        data = b""
        while len(data) != data_len:
            res = sock.recv(data_len - len(data))
            if res == b"":
                raise ConnectionError
            data += res
        return data
    except (ConnectionError, socket.error):
        return b""


def receive_a_msg(sock: socket.socket) -> bytes:
    len_of_msg = receive_all(sock, 120).decode()
    while len_of_msg.startswith(" "):
        len_of_msg = len_of_msg[1:]
    return receive_all(sock, int(len_of_msg))


def send_msg(from_user: str, to_user: str, msg: str) -> bool:
    pass


def send_file(from_user: str, to_user: str, file_data: bytes) -> bool:
    pass


def login(username: str, password: str) -> bool:
    pass


def signup(username: str, password: str) -> bool:
    pass


def handle_client(client_socket: socket.socket, client_ip_port: tuple[str, str]):
    pass


def accept_client(server_socket: socket.socket) -> Union[tuple[socket.socket, tuple[str, str]], tuple[None, None]]:
    global clients_sockets
    server_socket.settimeout(2)
    try:
        client_socket, client_addr = server_socket.accept()
    except (socket.error, ConnectionRefusedError):
        return None, None
    lock.acquire()
    print("New Connection From: '%s:%s'" % (client_addr[0], client_addr[1]))
    clients_sockets.append(client_socket)
    lock.release()
    return client_socket, client_socket.getpeername()


def main():
    server_socket = start_server()
    clients_threads: list[threading.Thread] = []
    clients_threads_socket: dict[threading.Thread, socket.socket] = {}
    while True:
        client_socket, client_ip_port = accept_client(server_socket)
        if client_socket is not None:
            client_thread = threading.Thread(target=handle_client,
                                             args=(client_socket, client_ip_port),
                                             daemon=True)
            client_thread.start()
            clients_threads.append(client_thread)
            clients_threads_socket[client_thread] = client_socket
        for client_thread in clients_threads:
            if not client_thread.is_alive():
                clients_threads.remove(client_thread)
                try:
                    client_socket = clients_threads_socket[client_thread]
                    client_socket.close()
                except socket.error:
                    pass
                clients_threads_socket.pop(client_thread)


if __name__ == '__main__':
    main()
