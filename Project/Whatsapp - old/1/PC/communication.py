import os
import socket
import time
import hashlib
import threading

from encryption import AESCipher


def sync_with_server(sync_sock: socket.socket, user_password: str, first_time_all: bool = False) -> bool:
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
    aes_cipher = AESCipher(user_password)
    # send sync request and receive the answer
    if first_time_all:
        sync_msg: bytes = aes_cipher.encrypt("sync all".rjust(32, " "))
        send_a_msg_by_the_protocol(sync_sock, sync_msg)
        enc_msg = receive_a_msg_by_the_protocol(sync_sock)
    else:
        sync_msg = aes_cipher.encrypt("sync new".rjust(32, " "))
        send_a_msg_by_the_protocol(sync_sock, sync_msg)
        enc_msg = receive_a_msg_by_the_protocol(sync_sock)
    response = aes_cipher.decrypt(enc_msg)
    # handle the answer
    if response == "no changes":
        return False
    while response != b"":
        # get len of file name
        len_file_name: int = int(strip_msg(response[:32].decode()))
        response = response[32:]
        # get file name
        file_name: str = response[:len_file_name].decode()
        response = response[len_file_name:]
        # get len of file data
        len_file_data: int = int(strip_msg(response[:32].decode()))
        response = response[32:]
        # get file data
        file_data: bytes = response[:len_file_data]
        response = response[len_file_data:]
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


def send_message(msg: str, send_to: str, sock: socket.socket, user_password: str) -> bool:
    aes_cipher = AESCipher(user_password)
    """
    encrypt with the password of the user
    len_encrypted_data.rjust(120, " ") + aes_encryption(msg_type.rjust(32, " ") + send_to.rjust(32, " ") + msg)
    """
    enc_msg = aes_cipher.encrypt("msg".rjust(32, " ") + send_to.rjust(32, " ") + msg)
    send_a_msg_by_the_protocol(sock, enc_msg)
    return True


def send_file(path_to_file: str, send_to: str, server_ip: str, server_port: str, user_password: str) -> bool:
    try:
        with open(path_to_file, "rb") as file:
            file_data = file.read()
    except FileNotFoundError:
        return False
    file_upload_sock = socket.socket()
    file_upload_sock.connect((server_ip, server_port))
    aes_cipher = AESCipher(user_password)
    file_name = path_to_file.split("\\")[-1]
    """
    encrypt with the password of the user
    len_encrypted_data.rjust(120, " ") + 
    aes_encryption("file.rjust(32, " ") + send_to.rjust(32, " ") + file_name, file_data=file_data)
    """
    enc_msg = aes_cipher.encrypt("file".rjust(32, " ") + send_to.rjust(32, " ") + file_name, file_data=file_data)
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


def login(sock: socket.socket, username: str, user_password: str, verbose: bool = False) -> bool:
    """ login using the global username and password """
    aes_cipher = AESCipher(username)
    enc_msg = aes_cipher.encrypt(user_password.rjust(32, " "))
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


def signup(sock: socket.socket, username: str, user_password: str,
           allowed_chars_in_username: str, default_encryption_key: str, verbose: bool = False) -> bool:
    """ Signup using global username and password and then call the login function"""
    """
    encrypt with hash(username + a constant string)
    len_msg.rjust(120, " ") + "signup".rjust(32, " ") + username.rjust(32, " ") + 
    len_of_encrypted_password.rjust(32, " ") + aes_encryption(password.rjust(32, " ")
    """
    # send signup request
    key = hashlib.sha256((username + default_encryption_key).encode()).hexdigest()
    aes_cipher = AESCipher(key)
    enc_msg = aes_cipher.encrypt(user_password.rjust(32, " "))
    metadata = ("signup".rjust(32, " ") + username.rjust(32, " ") + str(len(enc_msg)).rjust(32, " ")).encode()
    send_a_msg_by_the_protocol(sock, metadata + enc_msg)
    # receive signup response
    aes_cipher = AESCipher(user_password)
    enc_msg = receive_a_msg_by_the_protocol(sock)
    if enc_msg == b"":
        if verbose:
            print("Server Closed The Connection.")
    msg, _ = aes_cipher.decrypt(enc_msg)
    if msg == "signup".rjust(32, " ") + "signed up successfully".rjust(32, " "):
        if verbose:
            print("Signed Up.")
        return login(sock, username, user_password, verbose)
    elif msg == "signup".rjust(32, " ") + "username taken".rjust(32, " "):
        print("This User Name Is Taken Please Chose Another One.")
        ok = False
        while not ok:
            username = input("Please Enter Your Desired Username: ")
            ok = True
            for char in username:
                if char not in allowed_chars_in_username:
                    print("Username Can Only Contain The Following Chars: " + allowed_chars_in_username)
                    ok = False
                    break
        return signup(sock, username, user_password, allowed_chars_in_username, default_encryption_key, verbose)
    else:
        if verbose:
            print("Error Signing Up.")
        return False
