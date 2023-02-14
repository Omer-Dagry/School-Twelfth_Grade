import os
import tkinter

from threading import Thread
from protocol_socket import EncryptedProtocolSocket


def signup(username: str, email: str, password: str, server_ip_port: tuple[str, int], verbose: bool = True,
           sock: EncryptedProtocolSocket | None = None, login_after: bool = True) \
        -> tuple[bool, None | EncryptedProtocolSocket]:
    """
    :param username: the username
    :param email: the email of the user
    :param password: the md5 hash of the real password
    :param server_ip_port: a tuple of the server IP and port
    :param verbose: if true signup will print info, if false it won't print info
    :param sock: an existing socket to use
    :param login_after: whether to login after signing up or not
    """
    # signup (length 30)|len username (max 40)|username|len email (length 10)|
    # email|password (fixed length - md5 hash length)
    signup_msg = f"{'signup'.ljust(30)}{str(len(username)).ljust(2)}" \
                 f"{username}{str(len(email)).ljust(10)}{email}{password}".encode()
    if sock is None:
        sock = EncryptedProtocolSocket()
        sock.connect(server_ip_port)
    sock.send_message(signup_msg)
    confirmation_code_msg = sock.receive_message()
    if confirmation_code_msg[:30].strip() == "confirmation_code":
        sock.send_message(
            f"{'confirmation_code'.ljust(30)}"
            f"{input('Please enter your confirmation code (sent to your email): ')}".encode()
        )
    else:
        return False, None
    # signup (length 30)   status (length 6)   reason
    response = sock.receive_message()
    if response[:30].strip() not in ["login", "signup"]:
        return False, None
    response = response[30:]
    if response[:6].strip() != "ok":
        response = response[6:]
        if verbose:
            print(f"Signup Failed, Server Sent: {response}")
        return False, None
    if verbose:
        print("Signed up Successfully.")
    if login_after:
        ok, sock, username = login(email, password, server_ip_port, verbose, sock)
        if not ok:
            return False, None
    return True, sock


def login(email: str, password: str, server_ip_port: tuple[str, int], verbose: bool = True,
          sock: EncryptedProtocolSocket | None = None) \
        -> tuple[bool, None | EncryptedProtocolSocket, str]:
    """
    :param email: the username
    :param password: the md5 hash of the real password
    :param server_ip_port: a tuple of the server IP and port
    :param verbose: if true signup will print info, if false it won't print info
    :param sock: an existing socket to use
    """
    # login (length 30)     len email (length 10)   email    password (fixed length - md5 hash length)
    login_msg = f"{'login'.ljust(30)}{str(len(email)).ljust(10)}{email}{password}".encode()
    if sock is None:
        sock = EncryptedProtocolSocket()
        sock.connect(server_ip_port)
    sock.send_message(login_msg)
    # login (length 30)   status (length 6)   reason
    response = sock.receive_message()
    if response[:30].strip() not in ["login", "signup"]:
        return False, None, ""
    response = response[30:]
    if response[:6].strip() != "ok":
        response = response[6:]
        if verbose:
            print(f"Login Failed, Server Sent: {response}")
        sock.close()
        return False, None, ""
    if verbose:
        print("Logged in Successfully.")
    return True, sock, response[6:]


def sync(sock: EncryptedProtocolSocket, password: str, mode: str = "new") -> bool:
    """
    :param sock: the socket to the server
    :param password: the md5 hash of the real password
    :param mode: new or all
    :return: True if new data received else False
    """
    if mode not in ["new", "all"]:
        raise ValueError(f"param 'mode' should be either 'new' or 'all', got '{mode}'")
    sock.send_message(f"sync {mode}".ljust(30))
    response = sock.receive_message()
    # TODO: finish this function


def upload_file(current_chat_name: tkinter.Label, filename: str = "",
                root: tkinter.Tk = None, delete_file: bool = False):
    upload_thread = Thread(target=upload_file_, args=(current_chat_name.chat_id, filename, delete_file,), daemon=True)
    upload_thread.start()
    if root is not None:
        root.destroy()


def upload_file_(chat_id: str, filename: str = "", delete_file: bool = False):
    if filename == "":
        from tkinter import filedialog
        filename = filedialog.askopenfilename()
    # TODO: upload file
    if delete_file:
        os.remove(filename)


def send_message(current_chat_name: tkinter.Label, msg: str):
    chat_id = current_chat_name.chat_id
    # TODO: send the msg


def new_chat(other_email, email):
    pass
