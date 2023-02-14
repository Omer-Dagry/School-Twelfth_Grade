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
len_encrypted_data.rjust(120, " ") + aes_encryption(msg_type.rjust(32, " ") + send_to.rjust(32, " ") + msg)
###############################################
"""
import socket
import threading

from typing import *
from communication import login, signup


# Constants
DEFAULT_ENCRYPTION_KEY = "31548#1#efghoi#0#&@!$!@##4$$$n829cl;'[[]sdfg.viu23caxwq52ndfko4-gg0lb"
SERVER_PORT = 8820
SERVER_IP = "127.0.0.1"
ALLOWED_CHARS_IN_USERNAME = "abcdefghijklmnopqrstuvwxyz" + "abcdefghijklmnopqrstuvwxyz".upper() + \
                      " " + "_-" + "0123456789"
NOW_ALLOWED_IN_PASSWORD = ["012", "123", "234", "345", "456", "567", "678", "789",
                           "210", "321", "432", "543", "654", "765", "876", "987",
                           "password"]

# Globals
username: Union[str, None] = None
password: Union[str, None] = None


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
                if char not in ALLOWED_CHARS_IN_USERNAME:
                    print("Username Can Only Contain The Following Chars: " + ALLOWED_CHARS_IN_USERNAME)
                    ok = False
                    break
        password = input("Enter Your Password: ")
        if not login(sock, username, password, verbose=True):
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
                if char not in ALLOWED_CHARS_IN_USERNAME:
                    print("Username Can Only Contain The Following Chars: " + ALLOWED_CHARS_IN_USERNAME)
                    ok = False
                    break  # break the for loop
            if len(username) > 25:
                print("Username Can't Be Longer Than 25 Chars")
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
        if not signup(sock, username, password, ALLOWED_CHARS_IN_USERNAME, DEFAULT_ENCRYPTION_KEY, verbose=True):
            username = None
            password = None
            return False
        else:
            return True


def main():
    global username, password
    sock = socket.socket()
    sync_sock = socket.socket()
    try:
        # connect the regular socket and the sync socket to the server
        sock.connect((SERVER_IP, SERVER_PORT))
        sync_sock.connect((SERVER_IP, SERVER_PORT))
        # signup and then login / login (asks for username and password and logs in the socket)
        ok = login_signup(sock)
        if ok:
            # got username and password, login the sync socket as well
            ok &= login(sync_sock, username, password)
            if username is not None and password is not None and ok:
                sync_thread = threading.Thread(target=)
    except (ConnectionError, socket.error):
        sock.close()
        sync_sock.close()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt as err:
        pass
