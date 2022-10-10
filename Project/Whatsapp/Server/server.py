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
import datetime
import hashlib
import os.path
import socket
import threading
import time

from Crypto import Random
from Crypto.Cipher import AES
from typing import *


# Constants
IP = "127.0.0.1"
PORT = 8820
KEY = "31548#1#efghoi#0#&@!$!@##4$$$n829cl;'[[]sdfg.viu23caxwq52ndfko4-gg0lb"

# Globals
clients_sockets = []
online_users = []
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
        if enc == b"":
            return "", None
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


def accept_client(server_socket: socket.socket) -> Union[tuple[socket.socket, tuple[str, str]], tuple[None, None]]:
    global clients_sockets
    server_socket.settimeout(2)
    try:
        client_socket, client_addr = server_socket.accept()
    except (socket.error, ConnectionRefusedError):
        return None, None
    lock.acquire()
    print("[Server]: New Connection From: '%s:%s'" % (client_addr[0], client_addr[1]))
    clients_sockets.append(client_socket)
    lock.release()
    return client_socket, client_socket.getpeername()


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
    except (ConnectionError, socket.error, ValueError):
        return b""


def receive_a_msg_by_the_protocol(sock: socket.socket) -> bytes:
    len_of_msg = receive_all(sock, 120).decode()
    while len_of_msg.startswith(" "):
        len_of_msg = len_of_msg[1:]
    return receive_all(sock, int(len_of_msg))


def send_a_msg_by_the_protocol(sock: socket.socket, msg: bytes) -> bool:
    return send_all(sock, str(len(msg)).rjust(120, " ").encode() + msg)


def strip_msg(msg: str) -> str:
    while msg.startswith(" "):
        msg = msg[1:]
    return msg


def send_msg(from_user: str, to_user: str, msg: str) -> bool:
    """
    encrypt with the password of the user
    len_encrypted_data.rjust(120, " ") + aes_encryption(msg_type.rjust(32, " ") + send_to.rjust(32, " ") +
                                                        str(len(msg)).rjust(100, " ") + msg)
    """
    today_date = datetime.datetime.now().strftime("%m/%d/%Y")


def send_file(from_user: str, to_user: str, file_data: bytes) -> bool:
    """
    encrypt with the password of the user
    len_encrypted_data.rjust(120, " ") + aes_encryption(msg_type.rjust(32, " ") + send_to.rjust(32, " ") +
                                                        str(len(msg)).rjust(100, " ") + msg)
    """
    today_date = datetime.datetime.now().strftime("%m/%d/%Y")


def get_user_password(user: str) -> tuple[bool, str]:
    # get all usernames and passwords
    if not os.path.isfile("Data\\Server_Data\\user_password.txt"):
        return False, ""
    with open("Data\\Server_Data\\user_password.txt", "r") as user_password_file:
        user_password_data = user_password_file.read().split("\n")
    users = [user_password_data[i] for i in range(0, len(user_password_data)) if i % 2 == 0]
    passwords = [user_password_data[i] for i in range(0, len(user_password_data)) if i % 2 == 1]
    if user in users:
        return True, passwords[users.index(user)]
    return False, ""


def login(username: str, password: str) -> bool:
    """
    encrypt with password
    len_msg.rjust(120, " ") + "login".rjust(32, " ") + username.rjust(32, " ") +
    len_of_encrypted_password.rjust(32, " ") + aes_encryption(password.rjust(32, " ")
    """
    if not os.path.isfile("Data\\Server_Data\\user_password.txt"):
        return False
    # get all usernames and passwords
    with open("Data\\Server_Data\\user_password.txt", "r") as user_password_file:
        user_password_data = user_password_file.read().split("\n")
    users = [user_password_data[i] for i in range(0, len(user_password_data)) if i % 2 == 0]
    passwords = [user_password_data[i] for i in range(0, len(user_password_data)) if i % 2 == 1]
    # check if username and password are a match
    if username in users and password in passwords and \
            users.index(username) == passwords.index(password):
        return True
    return False


def signup(username: str, password: str) -> bool:
    """
    encrypt with hash(username + a constant string)
    len_msg.rjust(120, " ") + "signup".rjust(32, " ") + username.rjust(32, " ") +
    len_of_encrypted_password.rjust(32, " ") + aes_encryption(password.rjust(32, " ")
    """
    # if file doesn't exist, create the folders and the file
    if not os.path.isfile("Data\\Server_Data\\user_password.txt"):
        os.makedirs("Data\\Server_Data", exist_ok=True)
        with open("Data\\Server_Data\\user_password.txt", "w") as file:
            file.write("")
    # get all usernames
    with open("Data\\Server_Data\\user_password.txt", "r") as user_password_file:
        user_password_data = user_password_file.read().split("\n")
    users = [user_password_data[i] for i in range(0, len(user_password_data)) if i % 2 == 0]
    # if username doesn't exist
    if username not in users:
        # add username and password to the user_password.txt
        with open("Data\\Server_Data\\user_password.txt", "a") as user_password_file:
            user_password_file.write(username + "\n" + password + "\n")
        return True
    return False


def sync(username: str, first_sync: bool = False) -> bool:
    pass


def handle_client(client_socket: socket.socket, client_ip_port: tuple[str, str]):
    global lock, online_users
    logged_in = False
    did_not_signup = True
    stop = False
    username = ""
    password = ""
    try:
        # let client login / signup and login
        while not logged_in:
            # receive 1 msg
            msg = receive_a_msg_by_the_protocol(client_socket)
            cmd = strip_msg(msg[:32].decode())
            # check if the msg is signup msg or login, else throw the msg
            # because the client hasn't logged in yet
            if cmd == "signup" or cmd == "login":
                # disassemble msg by the protocol
                username = strip_msg(msg[32:64].decode())
                len_encrypted_password = int(strip_msg(msg[64:96].decode()))
                encrypted_password = msg[96:]
                # if client sent login request
                if cmd == "login":
                    # decrypt password
                    user_exists, password = get_user_password(username)
                    aes_cipher = AESCipher(password)
                    if user_exists:
                        password, _ = aes_cipher.decrypt(encrypted_password)
                        password = strip_msg(password)
                        aes_cipher = AESCipher(password)
                        if login(username, password):
                            response = aes_cipher.encrypt("login".rjust(32, " ") + "confirmed".rjust(32, " "))
                            send_a_msg_by_the_protocol(client_socket, response)
                            logged_in = True
                    if not logged_in:
                        response = aes_cipher.encrypt("login".rjust(32, " ") + "not confirmed".rjust(32, " "))
                        send_a_msg_by_the_protocol(client_socket, response)
                        stop = True
                        break
                # if client sent signup request for the first time
                elif cmd == "signup" and did_not_signup:
                    # decrypt password
                    key = hashlib.sha256((username + KEY).encode()).hexdigest()
                    aes_cipher = AESCipher(key)
                    password, _ = aes_cipher.decrypt(encrypted_password)
                    password = strip_msg(password)
                    # check and send response
                    aes_cipher = AESCipher(password)
                    if signup(username, password):
                        response = aes_cipher.encrypt("signup".rjust(32, " ") + "signed up successfully".rjust(32, " "))
                        did_not_signup = False
                        print(f"[Server]: '%s:%s' Signed Up As '{username}'." % client_ip_port)
                    else:
                        response = aes_cipher.encrypt("signup".rjust(32, " ") + "username taken".rjust(32, " "))
                    send_a_msg_by_the_protocol(client_socket, response)
                # if client sent signup request for more than one time
                elif cmd == "signup" and not did_not_signup:
                    stop = True
                    break
            else:
                stop = True
                break
        if stop:
            raise ConnectionError
        print(f"[Server]: '%s:%s' Logged In As '{username}'." % client_ip_port)
        # handle client's requests until client disconnects
        aes_cipher = AESCipher(password)
        enc_msg = receive_a_msg_by_the_protocol(client_socket)
        while enc_msg != b"":
            enc_msg = receive_a_msg_by_the_protocol(client_socket)
            msg = aes_cipher.decrypt(enc_msg)
            # TODO call the right func to handle the client's request
    except (socket.error, TypeError, OSError, ConnectionError, Exception) as err:
        if str(err) != "invalid literal for int() with base 10: ''":
            lock.acquire()
            print(f"[Server]: Error While Handling '%s:%s' ('{username}'):" % client_ip_port, str(err))
            lock.release()
    finally:
        try:
            client_socket.close()
        except socket.error:
            pass
    lock.acquire()
    print(f"[Server]: '%s:%s' ('{username}') Disconnected." % client_ip_port)
    lock.release()


def main():
    server_socket = start_server()
    clients_threads: list[threading.Thread] = []
    clients_threads_socket: dict[threading.Thread, socket.socket] = {}
    while True:
        time.sleep(0.5)
        client_socket, client_ip_port = accept_client(server_socket)
        if client_socket is not None:
            client_thread = threading.Thread(target=handle_client,
                                             args=(client_socket, client_ip_port),
                                             daemon=True)
            client_thread.start()
            clients_threads.append(client_thread)
            clients_threads_socket[client_thread] = client_socket
        # check if someone disconnected
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
