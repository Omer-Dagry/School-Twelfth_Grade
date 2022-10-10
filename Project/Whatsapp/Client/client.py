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
import os
import socket
import sys
import threading
import time

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow
from Crypto import Random
from Crypto.Cipher import AES
from typing import *


# Constants
KEY = "31548#1#efghoi#0#&@!$!@##4$$$n829cl;'[[]sdfg.viu23caxwq52ndfko4-gg0lb"
SERVER_PORT = 8820
SERVER_IP = "127.0.0.1"
ALLOWED_IN_USERNAME = "abcdefghijklmnopqrstuvwxyz" + "abcdefghijklmnopqrstuvwxyz".upper() + \
                      " " + "_-" + "0123456789"
NOW_ALLOWED_IN_PASSWORD = ["012", "123", "234", "345", "456", "567", "678", "789",
                           "210", "321", "432", "543", "654", "765", "876", "987",
                           "password"]

# Globals
msg_row_height: int = 40
status_row_height: int = 30
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


class MainGUI:
    def __init__(self, sock: socket.socket):
        # socket to server, for regular communication
        self.sock = sock
        # constants
        self.bg_color: str = "white"
        self.bg_color_chats: str = "#e9ebf0"
        self.bg_color_buttons: str = "#e9ebf0"
        self.bg_color_input_boxes: str = "#d3d7de"
        # create app and window
        self.app = QApplication(sys.argv)
        self.win = QMainWindow()
        self.window_size: tuple[int, int] = (1000, 600)
        self.window_location: tuple[int, int] = (
            (self.app.screens()[0].size().width() // 2) - self.window_size[0] // 2,
            (self.app.screens()[0].size().height() // 2) - self.window_size[1] // 2
        )
        # create worker (sync thread)
        self.worker: Union[None, WorkerThread] = None
        # list of chat buttons
        self.chat_buttons: list[QtWidgets.QPushButton] = []
        # create grid
        self.widget = QtWidgets.QWidget(self.win)
        self.grid = QtWidgets.QGridLayout(self.widget)
        # basic buttons, chats list, chat, inputs
        self.search_user_button = QtWidgets.QPushButton("Search", self.widget)
        self.search_user_box = QtWidgets.QLineEdit("", self.widget)
        self.new_chat_button = QtWidgets.QPushButton("New", self.widget)
        self.current_chat_label = QtWidgets.QLabel("Home", self.widget)
        self.chats_list = QtWidgets.QListWidget(self.widget)
        self.chat = QtWidgets.QTextEdit(self.widget)
        self.voice_msg_button = QtWidgets.QPushButton("Voice Msg", self.widget)
        self.upload_file_button = QtWidgets.QPushButton("Upload File", self.widget)
        self.emoji_button = QtWidgets.QPushButton("emoji", self.widget)
        self.input_box = QtWidgets.QTextEdit("Type Something", self.widget)
        self.send_button = QtWidgets.QPushButton("Send", self.widget)
        # set GUI structure
        self.set_gui_structure()

    def set_gui_structure(self):
        # set some settings for the GUI window
        self.win.setWindowTitle("Whatsapp")
        self.win.setMinimumSize(300, 300)
        # set starting size and location
        self.win.setGeometry(self.window_location[0], self.window_location[1],
                             self.window_size[0], self.window_size[1])
        # --------------- grid layout settings ---------------
        self.widget.setStyleSheet("background-color:" + self.bg_color)
        self.win.setCentralWidget(self.widget)
        self.grid.setSpacing(0)
        self.grid.setContentsMargins(0, 0, 0, 0)
        # --------------- add widgets ---------------
        # search user button
        self.search_user_button.setStyleSheet("background-color:" + self.bg_color_buttons)
        self.search_user_button.setMaximumWidth(100)
        self.search_user_button.setFixedHeight(status_row_height)
        self.grid.addWidget(self.search_user_button, 0, 0)
        # search user box
        self.search_user_box.setStyleSheet("background-color:" + self.bg_color_input_boxes)
        self.search_user_box.setFixedSize(220, status_row_height)
        self.grid.addWidget(self.search_user_box, 0, 1)
        # new chat button
        self.new_chat_button.setStyleSheet("background-color:" + self.bg_color_buttons)
        self.new_chat_button.setMaximumWidth(100)
        self.new_chat_button.setFixedHeight(status_row_height)
        self.grid.addWidget(self.new_chat_button, 0, 2)
        # current chat title
        self.current_chat_label.setStyleSheet("background-color:" + self.bg_color_buttons)
        self.current_chat_label.setAlignment(QtCore.Qt.AlignCenter)
        self.current_chat_label.setFixedHeight(status_row_height)
        self.grid.addWidget(self.current_chat_label, 0, 3, 1, 5)
        # chats list
        self.chats_list.setStyleSheet("background-color:" + self.bg_color_chats)
        self.grid.addWidget(self.chats_list, 1, 0, 2, 3)
        # chat
        self.chat.setStyleSheet("background-color:" + self.bg_color_chats)
        self.grid.addWidget(self.chat, 1, 3, 1, 5)
        # record voice msg button
        self.voice_msg_button.setStyleSheet("background-color:" + self.bg_color_buttons)
        self.voice_msg_button.setFixedHeight(msg_row_height)
        self.grid.addWidget(self.voice_msg_button, 2, 3)
        # upload file button
        self.upload_file_button.setStyleSheet("background-color:" + self.bg_color_buttons)
        self.upload_file_button.setFixedHeight(msg_row_height)
        self.grid.addWidget(self.upload_file_button, 2, 4)
        # emoji button
        self.emoji_button.setStyleSheet("background-color:" + self.bg_color_buttons)
        self.emoji_button.setFixedHeight(msg_row_height)
        self.grid.addWidget(self.emoji_button, 2, 5)
        # input box
        self.input_box.setStyleSheet("background-color:" + self.bg_color_input_boxes)
        self.input_box.setFixedHeight(msg_row_height)
        self.grid.addWidget(self.input_box, 2, 6)
        # send button
        self.send_button.setStyleSheet("background-color:" + self.bg_color_buttons)
        self.send_button.setFixedHeight(msg_row_height)
        self.send_button.setMaximumWidth(100)
        self.grid.addWidget(self.send_button, 2, 7)

    def launch(self, sync_sock: socket.socket):
        # launch the app
        self.sync_(sync_sock)
        self.win.show()
        sys.exit(self.app.exec_())

    def sync_(self, sync_sock: socket.socket):
        """ connects the worker thread to the update_gui function """
        # sync socket, is a different socket from the regular socket,
        # it will be used **only** to sync
        self.worker = WorkerThread(sync_sock)
        self.worker.start()
        # self.worker.my_signal[()].connect(self.update)
        self.worker.my_signal.connect(self.update_gui)

    def update_gui(self, new_data: bool):
        """ updates the GUI if there is new data """
        # TODO finish the update GUI function
        if new_data:
            pass


class WorkerThread(QtCore.QThread):
    """ QThread class for syncing in the background """
    my_signal = pyqtSignal(bool)

    def __init__(self, sync_sock: socket.socket):
        super(WorkerThread, self).__init__()
        self.sync_sock = sync_sock

    def run(self):
        """ syncs with the server
        if new data received emits True
        else emits False
        """
        new_data = sync_with_server(self.sync_sock, first_time_all=True)
        self.my_signal.emit(new_data)
        while True:
            time.sleep(2)
            new_data = sync_with_server(self.sync_sock)
            self.my_signal.emit(new_data)


def sync_with_server(sync_sock: socket.socket, first_time_all: bool = False) -> bool:
    # """
    # Syncs With Server
    # :return: if received new data - True, else - False
    # """
    """
    send sync request (len_of_entire_msg (120 digits) + aes_cipher("sync new" (32 digits)))


    receive answer:
    the entire msg is encrypted by user password (aes_cipher = AESCipher(password), aes_cipher.encrypt(msg))
    len of entire msg (120 digits) +
    len of file name (32 digits) + file_name + len of file data (32 digits) + file_data + ...  + more files
    """
    global password
    aes_cipher = AESCipher(password)
    # send sync request and receive the answer
    if first_time_all:
        sync_msg: bytes = aes_cipher.encrypt("sync all".rjust(32, " "))
        send_a_msg_by_the_protocol(sync_sock, sync_msg)
        enc_msg = receive_a_msg_by_the_protocol(sync_sock)
    else:
        sync_msg = aes_cipher.encrypt("sync new".rjust(32, " "))
        send_a_msg_by_the_protocol(sync_sock, sync_msg)
        enc_msg = receive_a_msg_by_the_protocol(sync_sock)
    enc_msg = aes_cipher.decrypt(enc_msg)
    # handle the answer
    if enc_msg == "no changes":
        return False
    while enc_msg != b"":
        # get len of file name
        len_file_name: int = int(strip_msg(enc_msg[:32].decode()))
        enc_msg = enc_msg[32:]
        # get file name
        file_name: str = enc_msg[:len_file_name].decode()
        enc_msg = enc_msg[len_file_name:]
        # get len of file data
        len_file_data: int = int(strip_msg(enc_msg[:32].decode()))
        enc_msg = enc_msg[32:]
        # get file data
        file_data: bytes = enc_msg[:len_file_data]
        enc_msg = enc_msg[len_file_data:]
        # make sure that all the folders in the file path exist
        if file_name.startswith("\\"):
            file_path = os.path.dirname(__file__) + "\\".join(file_name.split("\\")[0:-1])
        else:
            file_path = os.path.dirname(__file__) + "\\" + "\\".join(file_name.split("\\")[0:-1])
        file_name = file_name.split("\\")[-1]
        # create the file
        with open(file_path + "\\" + file_name, "wb") as file:
            file.write(file_data)
    return True


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
        timeout = sock.timeout
        sock.settimeout(2.5)
        data = b""
        count = 0
        while len(data) != data_len and count < 10:
            try:
                res = sock.recv(data_len - len(data))
                if res == b"":
                    raise ConnectionError
                data += res
            except socket.error:
                time.sleep(1)
            count += 1
        sock.settimeout(timeout)
        if len(data) == data_len:
            return data
        else:
            raise ConnectionError
    except (ConnectionError, socket.error):
        return b""


def receive_a_msg_by_the_protocol(sock: socket.socket) -> bytes:
    len_of_msg = receive_all(sock, 120).decode()
    while len_of_msg.startswith(" "):
        len_of_msg = len_of_msg[1:]
    return receive_all(sock, int(len_of_msg))


def send_a_msg_by_the_protocol(sock: socket.socket, msg: bytes):
    send_all(sock, str(len(msg)).rjust(120, " ").encode() + msg)


def strip_msg(msg: str) -> str:
    while msg.startswith(" "):
        msg = msg[1:]
    return msg


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
    send_a_msg_by_the_protocol(sock, enc_msg)
    return True


def send_file(path_to_file: str, send_to: str) -> bool:
    global password
    try:
        with open(path_to_file, "rb") as file:
            file_data = file.read()
    except FileNotFoundError:
        return False
    file_upload_sock = socket.socket()
    file_upload_sock.connect((SERVER_IP, SERVER_PORT))
    aes_cipher = AESCipher(password)
    """
    encrypt with the password of the user
    len_encrypted_data.rjust(120, " ") + aes_encryption(msg_type.rjust(32, " ") + send_to.rjust(32, " ") +
                                                        str(len(msg)).rjust(100, " ") + msg)
    """
    enc_msg = aes_cipher.encrypt("file".rjust(32, " ") + send_to.rjust(32, " ") +
                                 str(len(file_data)).rjust(100, " "), file_data=file_data)
    # just for testing
    # return enc_msg
    #
    # send_a_msg_by_the_protocol(file_upload_sock, enc_msg)
    upload_file_thread = threading.Thread(target=send_a_msg_by_the_protocol,
                                          args=(
                                              file_upload_sock,
                                              enc_msg
                                          ),
                                          daemon=True)
    upload_file_thread.start()
    return True


def login(sock: socket.socket, verbose: bool = False) -> bool:
    """ login using the global username and password """
    global username, password
    aes_cipher = AESCipher(password)
    enc_msg = aes_cipher.encrypt(password.rjust(32, " "))
    metadata = ("login".rjust(32, " ") + username.rjust(32, " ") + str(len(enc_msg)).rjust(32, " ")).encode()
    """
    encrypt with password
    len_msg.rjust(120, " ") + "login".rjust(32, " ") + username.rjust(32, " ") + 
    len_of_encrypted_password.rjust(32, " ") + aes_encryption(password.rjust(32, " ")
    """
    send_a_msg_by_the_protocol(sock, metadata + enc_msg)
    enc_msg = receive_a_msg_by_the_protocol(sock)
    if enc_msg == b"":
        if verbose:
            print("Incorrect Username Or Password.")
        return False
    msg, file = aes_cipher.decrypt(enc_msg)
    if msg == "login".rjust(32, " ") + "confirmed".rjust(32, " "):
        if verbose:
            print("Logged In.")
        return True
    if verbose:
        print("Incorrect Username Or Password.")
    return False


def signup(sock: socket.socket, verbose: bool = False) -> bool:
    """ Signup using global username and password and then call the login function"""
    global username, password
    """
    encrypt with hash(username + a constant string)
    len_msg.rjust(120, " ") + "signup".rjust(32, " ") + username.rjust(32, " ") + 
    len_of_encrypted_password.rjust(32, " ") + aes_encryption(password.rjust(32, " ")
    """
    # send signup request
    key = hashlib.sha256((username + KEY).encode()).hexdigest()
    aes_cipher = AESCipher(key)
    enc_msg = aes_cipher.encrypt(password.rjust(32, " "))
    metadata = ("signup".rjust(32, " ") + username.rjust(32, " ") + str(len(enc_msg)).rjust(32, " ")).encode()
    send_a_msg_by_the_protocol(sock, metadata + enc_msg)
    # receive signup response
    aes_cipher = AESCipher(password)
    enc_msg = receive_a_msg_by_the_protocol(sock)
    if enc_msg == b"":
        if verbose:
            print("Server Closed The Connection.")
    msg, _ = aes_cipher.decrypt(enc_msg)
    if msg == "signup".rjust(32, " ") + "signed up successfully".rjust(32, " "):
        if verbose:
            print("Signed Up.")
        return login(sock, verbose)
    elif msg == "signup".rjust(32, " ") + "username taken".rjust(32, " "):
        print("This User Name Is Taken Please Chose Another One.")
        ok = False
        while not ok:
            username = input("Please Enter Your Desired Username: ")
            ok = True
            for char in username:
                if char not in ALLOWED_IN_USERNAME:
                    print("Username Can Only Contain The Following Chars: " + ALLOWED_IN_USERNAME)
                    ok = False
                    break
        return signup(sock, verbose)
    else:
        if verbose:
            print("Error Signing Up.")
        return False


def login_signup(sock: socket.socket) -> bool:
    """ ask the user what to do, login or signup, after signup logged in automatically """
    global username, password
    login_or_signup = input("Login Or Signup [L/S] ? ").lower()
    while login_or_signup not in ("l", "s"):
        login_or_signup = input("Login Or Signup [L/S] ? ").lower()
    if login_or_signup == 'l':
        ok = False
        while not ok:
            username = input("Please Enter Your Username: ")
            ok = True
            for char in username:
                if char not in ALLOWED_IN_USERNAME:
                    print("Username Can Only Contain The Following Chars: " + ALLOWED_IN_USERNAME)
                    ok = False
                    break
        password = input("Enter Your Password: ")
        if not login(sock, verbose=True):
            username = None
            password = None
            return False
        else:
            return True
    else:
        ok = False
        while not ok:
            username = input("Please Enter Your Desired Username: ")
            ok = True
            for char in username:
                if char not in ALLOWED_IN_USERNAME:
                    print("Username Can Only Contain The Following Chars: " + ALLOWED_IN_USERNAME)
                    ok = False
                    break
        ok = False
        while not ok:
            upper = False
            lower = False
            number = False
            password = input("Enter Your Desired Password: ")
            ok = True
            for not_allowed_sequence in NOW_ALLOWED_IN_PASSWORD:
                if not_allowed_sequence in password:
                    print("* Password Can Not Contain The Following Sequences: " +
                          ",".join(NOW_ALLOWED_IN_PASSWORD))
                    ok = False
                    break
            for char in password:
                if char.isupper():
                    upper = True
                if char.islower():
                    lower = True
                if char.isnumeric():
                    number = True
            if username in password or username.lower() in password.lower():
                print("* Password Can't Contain The Username.")
            if len(password) < 8:
                print("* Password Must Be 8 Chars Or Longer.")
            if not upper:
                print("* Password Must Contain 1 Or More UPPER Cased Letters.")
            if not lower:
                print("* Password Must Contain 1 Or More lower Cased Letters.")
            if not number:
                print("* Password Must Contain 1 Or More Numbers.")
            if not upper or not lower or not number or len(password) < 8 or \
                    username in password or username.lower() in password.lower():
                ok = False
        if not signup(sock, verbose=True):
            username = None
            password = None
            return False
        else:
            return True


def main():
    global username, password
    # enc_msg = send_file(r"D:\Projects\Work-Silicom\Palma\log\Palma 5.xlsx", "omer")
    # aes = AESCipher("hello")
    # print(aes.decrypt(enc_msg))
    # print(aes.decrypt(aes.encrypt("hi")))
    sock = socket.socket()
    sync_sock = socket.socket()
    try:
        sock.connect((SERVER_IP, SERVER_PORT))
        ok = login_signup(sock)
        if username is not None and password is not None and ok:
            gui = MainGUI(sock)
            sync_sock.connect((SERVER_IP, SERVER_PORT))
            ok = login(sync_sock)
            if ok:
                gui.launch(sync_sock)
    except (ConnectionError, socket.error):
        sock.close()
        sync_sock.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as err:
        pass
