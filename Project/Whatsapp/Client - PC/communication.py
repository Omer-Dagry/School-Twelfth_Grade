import os
import pickle
import shutil

from tkinter import *
from threading import Thread
from tkinter import messagebox
from photo_tools import check_size
from tkinter.filedialog import askopenfilename
from protocol_socket import EncryptedProtocolSocket


# Globals
REMOVE = "remove"
SYNC_MODES = ["new", "all"]


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
                 f"{username}{str(len(email)).ljust(15)}{email}{password}".encode()
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
        communication = Communication(email, password, server_ip_port)
        ok, sock, username = communication.login(verbose, sock)
        if not ok:
            return False, None
    return True, sock


class Communication:
    def __init__(self, email: str, password: str, server_ip_port: tuple[str, int]) -> None:
        """
        :param email: the username
        :param password: the md5 hash of the real password
        :param server_ip_port: a tuple of the server IP and port
        """
        self.__email = email
        self.__password = password
        self.__server_ip_port = server_ip_port

    def login(self, verbose: bool = True, sock: EncryptedProtocolSocket | None = None) \
            -> tuple[bool, None | EncryptedProtocolSocket, str]:
        """
        :param verbose: if true signup will print info, if false it won't print info
        :param sock: an existing socket to use
        :return: status, sock, reason for status
        """
        # login (length 30)     len email (length 10)   email    password (fixed length - md5 hash length)
        login_msg = f"{'login'.ljust(30)}{str(len(self.__email)).ljust(15)}{self.__email}{self.__password}".encode()
        if sock is None:
            sock = EncryptedProtocolSocket()
            sock.connect(self.__server_ip_port)
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

    def sync(self, sock: EncryptedProtocolSocket, mode: str = "new") \
            -> tuple[bool, list[str | os.PathLike], list[str | os.PathLike]]:
        """  sync once

        :param sock: the socket to the server
        :param mode: 'new' or 'all'
        :return: True if new data received else False, list of the modified/new files, list of deleted files/folders
        """
        if mode not in SYNC_MODES:
            raise ValueError(f"param 'mode' should be either 'new' or 'all', got '{mode}'")
        sock.send_message(f"sync {mode}".ljust(30).encode())
        response = sock.receive_message()
        #                         cmd                  {}             str       bytes
        # response -> f"{'sync new/all'.ljust(30)}{empty-dict/dict[file_name, file_data]}"
        if response[:30] != f"sync {mode}".ljust(30).encode():
            return False, [], []
        try:
            files_dict = pickle.loads(response[30:])
        except EOFError:
            files_dict = {}
        if files_dict:
            deleted_files_path: list[str | os.PathLike] = []
            modified_files_path: list[str | os.PathLike] = []
            for file_path, file_data in files_dict.items():
                file_path = f"{self.__email}\\{file_path}"
                # if it's a not remove message
                # a remove message will be after a request of a client
                # to delete message for everyone, if the message is a file
                # in order to delete the file on the clients side
                if file_data != REMOVE:
                    modified_files_path.append(file_path)
                    with open(file_path, "wb") as f:
                        f.write(file_data)
                elif os.path.isfile(file_path):  # a file was deleted in a chat
                    deleted_files_path.append(file_path)
                    os.remove(file_path)
                elif os.path.isdir(file_path):  # the user was removed from the chat
                    deleted_files_path.append(file_path)
                    shutil.rmtree(file_path)
            return True, modified_files_path, deleted_files_path
        else:
            return False, [], []

    def upload_file(self, chat_id: str | int, filename: str = "", root: Tk = None, delete_file: bool = False) -> None:
        upload_thread = Thread(target=self.upload_file_, args=(str(chat_id), filename, delete_file,), daemon=True)
        upload_thread.start()
        if root is not None:
            root.destroy()

    def upload_file_(self, chat_id: str, filename: str = "", delete_file: bool = False) -> None:
        # if filename == "":
        #     filename = askopenfilename()
        # ok, sock, _ = self.login(verbose=False)
        # if not ok:
        #     raise ValueError("email or password incorrect, could not login to upload file")
        # TODO: upload file
        # if delete_file:
        #     os.remove(filename)
        # TODO: finish
        raise NotImplementedError

    @staticmethod
    def send_message(chat_id: str | int, msg: str, sock: EncryptedProtocolSocket) -> bool:
        chat_id = str(chat_id)
        request = f"{'msg'.ljust(30)}{str(len(chat_id)).ljust(15)}{chat_id}{msg}".encode()
        if not sock.send_message(request):
            messagebox.showerror("Send Message Error", f"Could not send the message, lost connection to server.")
            return False
        status_msg = sock.receive_message().decode()
        if status_msg != f"{'msg'.ljust(30)}{'ok'.ljust(6)}":
            messagebox.showerror("Send Message Error", f"Could not send the message, server error.")
            return False
        return True

    def new_chat(self, other_email: str, sock: EncryptedProtocolSocket) -> None:
        # TODO: finish
        raise NotImplementedError

    def make_call(self, chat_id: str) -> None:
        # go to 'users' file of this chat and make call to users
        # OR
        # change the way a call works and call the chat_id and the server
        # will handle who to call
        # TODO: finish
        raise NotImplementedError

    def upload_profile_picture(self, path_to_picture: os.PathLike | str = None) -> None:
        if path_to_picture is None:  # ask for file
            file_types = [("PNG", "*.png"), ("JPG", "*.jpg"), ("JPEG", "*.jpeg")]
            path_to_picture = askopenfilename(filetypes=file_types)
        if not check_size(path_to_picture):  # check image size
            messagebox.showerror("Profile Picture", "Image size is invalid,\nmust be at least 64x64.")
            return
        # TODO: finish
        raise NotImplementedError

    def delete_message_for_me(self, chat_id: str, message_index: int, root: Tk | Toplevel):
        # close the MessageOptions window
        root.destroy()
        pass
        # TODO: finish
        raise NotImplementedError

    def delete_message_for_everyone(self, chat_id: str, message_index: int, root: Tk | Toplevel):
        # close the MessageOptions window
        root.destroy()
        pass
        # TODO: finish
        raise NotImplementedError
