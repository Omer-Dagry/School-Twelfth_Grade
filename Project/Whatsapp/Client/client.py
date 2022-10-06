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
KEY = "w h a t s a p p"
SERVER_PORT = 8820
SERVER_IP = "127.0.0.1"

# Globals
username: Union[str, None] = None
password: Union[str, None] = None


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


def send_all(sock: socket.socket, msg: bytes):
    try:
        sent_amount = 0
        while sent_amount != len(msg):
            sent_amount += sock.send(msg[sent_amount:])
    except (ConnectionError, socket.error):
        print("Lost Connection To Server.")
        exit()


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
        print("Lost Connection To Server.")
        exit()


def receive_a_msg(sock: socket.socket) -> bytes:
    len_of_msg = receive_all(sock, 120).decode()
    while len_of_msg.startswith(" "):
        len_of_msg = len_of_msg[1:]
    return receive_all(sock, int(len_of_msg))


def send_message(msg: str, send_to: str, sock: socket.socket) -> bool:
    global password
    aes_cipher = AESCipher(password)
    """
    encrypt with the password of the user
    len_encrypted_data.rjust(120, " ") + aes_encryption(msg_type.rjust(32, " ") + send_to.rjust(32, " ") +
                                                        str(len(msg)).rjust(100, " ") + msg)
    """
    enc_msg = aes_cipher.encrypt("msg".rjust(32, " ") + send_to.rjust(32, " ") +
                                 str(len(msg)).rjust(100, " ") + msg)
    send_all(sock, str(len(enc_msg)).rjust(120, " ").encode() + enc_msg)
    return True


def send_file(path_to_image: str, send_to: str, sock: socket.socket) -> bool:
    global password
    try:
        with open(path_to_image, "rb") as file:
            file_data = file.read()
    except FileNotFoundError:
        return False
    aes_cipher = AESCipher(password)
    """
    encrypt with the password of the user
    len_encrypted_data.rjust(120, " ") + aes_encryption(msg_type.rjust(32, " ") + send_to.rjust(32, " ") +
                                                        str(len(msg)).rjust(100, " ") + msg)
    """
    enc_msg = aes_cipher.encrypt("file".rjust(32, " ") + send_to.rjust(32, " ") +
                                 str(len(file_data)).rjust(100, " "), file_data=file_data)
    # return enc_msg
    send_all(sock, str(len(enc_msg)).rjust(120, " ").encode() + enc_msg)
    return True


def login(sock: socket.socket) -> bool:
    global username, password
    aes_cipher = AESCipher(password)
    enc_msg = aes_cipher.encrypt(password.rjust(32, " "))
    metadata = ("login".rjust(32, " ") + username.rjust(32, " ") + str(len(enc_msg)).rjust(32, " ")).encode()
    """
    encrypt with password
    len_msg.rjust(120, " ") + "login".rjust(32, " ") + username.rjust(32, " ") + 
    len_of_encrypted_password.rjust(32, " ") + aes_encryption(password.rjust(32, " ")
    """
    send_all(sock, str(len(metadata + enc_msg)).rjust(120, " ").encode() + metadata + enc_msg)
    enc_msg = receive_a_msg(sock)
    msg, file = aes_cipher.decrypt(enc_msg)
    if msg == "login".rjust(32, " ") + "confirmed".rjust(32, " "):
        return True
    return False


def signup(sock: socket.socket):
    global username, password
    # now_allowed_in_pass = ["012", "123", "234", "345", "456", "567", "678", "789",
    #                        "210", "321", "432", "543", "654", "765", "876", "987",
    #                        "password"]
    # TODO get username and password
    # TODO check username and password are ok
    username = "Omer Dagry"
    password = "omda12"
    """
    encrypt with hash(username + a constant string)
    len_msg.rjust(120, " ") + "signup".rjust(32, " ") + username.rjust(32, " ") + 
    len_of_encrypted_password.rjust(32, " ") + aes_encryption(password.rjust(32, " ")
    """
    key = hashlib.sha256((username + KEY).encode()).hexdigest()
    aes_cipher = AESCipher(key)
    enc_msg = aes_cipher.encrypt(password.rjust(32, " "))
    metadata = ("signup".rjust(32, " ") + username.rjust(32, " ") + str(len(enc_msg)).rjust(32, " ")).encode()
    send_all(sock, str(len(metadata + enc_msg)).rjust(120, " ").encode() + metadata + enc_msg)
    enc_msg = receive_a_msg(sock)
    msg, file = aes_cipher.decrypt(enc_msg)
    if msg == "signup".rjust(32, " ") + "signed up".rjust(32, " "):
        return login(sock)
    elif msg == "signup".rjust(32, " ") + "username taken".rjust(32, " "):
        print("This User Name Is Taken Please Chose Another One.")
        return signup(sock)
    else:
        return False


def main():
    global username, password
    # enc_msg = send_file(r"D:\Projects\Work-Silicom\Palma\log\Palma 5.xlsx", "omer")
    # aes = AESCipher("hello")
    # print(aes.decrypt(enc_msg))
    # print(aes.decrypt(aes.encrypt("hi")))


if __name__ == '__main__':
    main()
