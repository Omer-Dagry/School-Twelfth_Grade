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
import os
import time
import socket
import hashlib
import threading

from typing import *
from encryption import AESCipher
from communication import receive_a_msg_by_the_protocol, send_a_msg_by_the_protocol


# Constants
IP = "127.0.0.1"
PORT = 8820

# Globals
clients_sockets = []
online_users = []
lock = threading.Lock()


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


def strip_msg(msg: str) -> str:
    while msg[0] == " ":
        msg = msg[1:]
    return msg


def send_msg(from_user: str, to_user: str, msg: str) -> bool:
    """
    encrypt with the md5 hash of the password of the user
    len_encrypted_data.rjust(120, " ") + aes_encryption(msg_type.rjust(32, " ") + send_to.rjust(32, " ") + msg)
    """
    try:
        # TODO: save the msg for from_user
        # TODO: save the msg for to_user
        return True
    except (Exception, OSError, FileNotFoundError):
        return False


def send_file(from_user: str, to_user: str, file_data: bytes, file_name: str) -> bool:
    """
    encrypt with the password of the user
    len_encrypted_data.rjust(120, " ") +
    aes_encryption("file.rjust(32, " ") + send_to.rjust(32, " ") + file_name, file_data=file_data)
    """
    try:
        # from_user chat files location
        user_1_location = "Users_Data\\" + from_user + "\\" + "Chats\\" + to_user + "Files\\"
        # check that user_1_location path exists
        if not os.path.isdir(user_1_location):
            os.makedirs(user_1_location, exist_ok=True)
        # if there is already a file with this name, create new name
        if os.path.isfile(user_1_location + file_name):
            new_file_name = ".".join(file_name.split(".")[:-1]) + "_1" + file_name.split(".")[-1]
            i = 2
            while os.path.isfile(user_1_location + new_file_name):
                new_file_name = ".".join(file_name.split(".")[:-1]) + f"_{i}" + file_name.split(".")[-1]
                i += 1
        else:
            new_file_name = file_name
        # save the file
        with open(user_1_location + new_file_name, "wb") as file:
            file.write(file_data)
        #
        # user 2 chats files location
        user_2_location = "Users_Data\\" + to_user + "\\" + "Chats\\" + from_user + "Files\\"
        if not os.path.isdir(user_2_location):
            os.makedirs(user_2_location, exist_ok=True)
        # if there is already a file with this name, create new name
        if os.path.isfile(user_2_location + file_name):
            new_file_name = ".".join(file_name.split(".")[:-1]) + "_1" + file_name.split(".")[-1]
            i = 2
            while os.path.isfile(user_2_location + new_file_name):
                new_file_name = ".".join(file_name.split(".")[:-1]) + f"_{i}" + file_name.split(".")[-1]
                i += 1
        else:
            new_file_name = file_name
        # save the file
        with open(user_2_location + new_file_name, "wb") as file:
            file.write(file_data)
        # TODO decide what are the separations characters
        if send_msg(from_user, to_user, FILE_SEPARATION + "File:" + new_file_name):
            return True
        else:
            return False
    except (Exception, OSError, BaseException, FileNotFoundError):
        return False


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
    if username not in users and len(username) <= 25:
        # add username and password to the user_password.txt
        with open("Data\\Server_Data\\user_password.txt", "a") as user_password_file:
            user_password_file.write(username + "\n" + password + "\n")
        return True
    return False


def sync(username: str, sync_all: bool = False) -> bool:
    """
    send sync request (len_of_entire_msg (120 digits) + aes_cipher("sync new" (32 digits)))


    receive answer:
    the entire msg is encrypted by user password (aes_cipher = AESCipher(password), aes_cipher.encrypt(msg))
    len of entire msg (120 digits) +
    len of file name (32 digits) + file_name + len of file data (32 digits) + file_data + ...  + more files
    """
    pass
    # TODO finish this func


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
            msg, file = aes_cipher.decrypt(enc_msg)
            # TODO call the right func to handle the client's request
            cmd = msg[:32]
            if cmd == "sync new".rjust(32, " "):
                sync(username)
            elif cmd == "sync all".rjust(32, " "):
                sync(username, sync_all=True)
            # TODO add new sync type to send to the client 30 days worth of chats data
            # the sync function by default will sync 30 days worth of chats data (not necessarily the lst 30 days)
            # each request to get older chats data will send another 30 days worth of chats data
            elif cmd == "msg".rjust(32, " "):
                #        from      to          msg
                send_msg(username, msg[32:64], msg[164:])
            elif cmd == "file".rjust(32, " "):
                #         from      to     file_data  file_name
                send_file(username, msg[32:64], file, msg[64:])
    except (socket.error, TypeError, OSError, ConnectionError, Exception) as err:
        if str(err) != "invalid literal for int() with base 10: ''":  # when client disconnects
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
