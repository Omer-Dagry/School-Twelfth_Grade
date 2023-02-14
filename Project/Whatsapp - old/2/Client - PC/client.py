"""
###############################################
Author: Omer Dagry
Mail: omerdagry@gmail.com
Date: 06/01/2023 (dd/mm/yyyy)
###############################################
"""
import time
import socket
import hashlib

from typing import *
from threading import Thread
from gui import mainloop, update
from protocol_socket import ProtocolSocket
from communication import login, signup, sync


# Constants
SERVER_PORT = 8820
SERVER_IP = "127.0.0.1"
ALLOWED_CHARS_IN_USERNAME = "abcdefghijklmnopqrstuvwxyz" + "abcdefghijklmnopqrstuvwxyz".upper() + \
                      " " + "_" + "0123456789"
NOW_ALLOWED_IN_PASSWORD = ["012", "123", "234", "345", "456", "567", "678", "789",
                           "210", "321", "432", "543", "654", "765", "876", "987",
                           "password"]

# Globals
email: Union[str, None] = None
username: Union[str, None] = None
password: Union[str, None] = None


def login_signup(server_ip_port: tuple[str, int]) -> tuple[bool, ProtocolSocket | None]:
    """ ask the user what to do, login or signup, after signup logged in automatically """
    global username, password, email
    login_or_signup = input("Login Or Signup [L/S] ? ").lower()
    while login_or_signup not in ("l", "s"):
        login_or_signup = input("Login Or Signup [L/S] ? ").lower()
    ok = False
    while not ok:
        email = input("Please Enter Your Email: ")
        ok = True
    if login_or_signup == 'l':
        password = input("Enter Your Password: ")
        password = hashlib.md5(password.encode()).hexdigest().lower()
        ok, sock, username = login(email, password, server_ip_port, verbose=True)
        if not ok:
            username = None
            password = None
            return False, None
        else:
            return True, sock
    else:
        ok = False
        while not ok:
            username = input("Please Enter Your Desired Username: ")
            ok = True
            for char in username:
                if char not in ALLOWED_CHARS_IN_USERNAME:
                    print("Username Can Only Contain The Following Chars: " + ALLOWED_CHARS_IN_USERNAME)
                    ok = False
                    break  # break the for loop
            if len(username) > 40:
                print("Username Can't Be Longer Than 40 Chars")
                ok = False
        ok = False
        while not ok:
            upper = False
            lower = False
            number = False
            password = input("Enter Your Desired Password: ")
            ok = True
            for not_allowed_sequence in NOW_ALLOWED_IN_PASSWORD:
                if not_allowed_sequence in password:
                    print(not_allowed_sequence)
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
        password = hashlib.md5(password.encode()).hexdigest().lower()
        ok, sock = signup(username, email, password, server_ip_port, verbose=True)
        if not ok:
            username = None
            password = None
            return False, None
        else:
            return True, sock


def sync_(sync_sock: ProtocolSocket, first_time_all: bool = False):
    global password
    if first_time_all:
        sync(sync_sock, password, "all")
    while True:
        new_data = sync(sync_sock, password)
        if new_data:
            update()
        time.sleep(0.5)


def main():
    global username, password
    try:
        # signup and then login / login (asks for username and password and logs in the socket)
        ok, sock = login_signup((SERVER_IP, SERVER_PORT))
        if ok:
            # got username and password, login the sync socket as well
            ok2, sync_sock, username = login(email, password, (SERVER_IP, SERVER_PORT), verbose=False)
            ok &= ok2
            del ok2
            if username is not None and password is not None and ok:
                sync_thread = Thread(target=sync_, args=(sync_sock, True))
                mainloop(email)
            print("\n\nApp Closed.")
    except (ConnectionError, socket.error):
        if "sock" in locals():
            sock.close()
        if "sync_sock" in locals():
            sync_sock.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as err:
        pass