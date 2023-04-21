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


def showerror(title: str | None, message: str | None, **options) -> None:
    Thread(target=messagebox.showerror, args=(title, message,), kwargs=options).start()


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
    if not sock.send_message(signup_msg):
        showerror("Signup Error", "Could not send signup request, lost connection to server.")
        sock.close()
        return False, None
    confirmation_code_msg = sock.receive_message().decode()
    if confirmation_code_msg.strip() == "confirmation_code":
        if not sock.send_message(
                f"{'confirmation_code'.ljust(30)}"
                f"{input('Please enter your confirmation code (sent to your email): ')}".encode()):
            showerror("Signup Error", "Could not send signup confirmation code, lost connection to server.")
            sock.close()
            return False, None
    else:
        return False, None
    # signup (length 30)   status (length 6)   reason
    response = sock.receive_message().decode()
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


def reset_password(username: str, email: str, server_ip_port: tuple[str, int]
                   ) -> tuple[bool, EncryptedProtocolSocket | None]:
    """
    :return: the returned socket isn't connected !!
    """
    sock = EncryptedProtocolSocket()
    sock.connect(server_ip_port)
    if not sock.send_message(f"{'reset password'.ljust(30)}{str(len(email)).ljust(15)}{email}{username}".encode()):
        showerror(
            "Reset Password Error", "Could not send reset password request, lost connection to server.")
        sock.close()
        return False, None
    confirmation_code_msg = sock.receive_message()
    if confirmation_code_msg[:30].strip() == "confirmation_code":
        sock.send_message(
            f"{'confirmation_code'.ljust(30)}"
            f"{input('Please enter your confirmation code (sent to your email): ')}".encode()
        )
    else:
        sock.close()
        return False, None
    new_password_msg = sock.receive_message()
    if new_password_msg != f"{'new_password'.ljust(30)}".encode():
        sock.close()
        return False, None
    sock.send_message(f"{'new_password'.ljust(30)}{input('Please enter your new password: ')}".encode())
    reset_password_status = sock.receive_message()
    if "not ok" in reset_password_status.decode():
        sock.close()
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
        if not sock.send_message(login_msg):
            showerror("Login Error", "Could not send login request, lost connection to server.")
            sock.close()
            return False, None, ""
        # login (length 30)   status (length 6)   reason
        response = sock.receive_message().decode()
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
        if not sock.send_message(f"sync {mode}".ljust(30).encode()):
            showerror("Sync Error", "Could not send sync request, lost connection to server.")
            sock.close()
            return False, [], []
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
                if file_path.startswith(self.__email):
                    file_path = f"webroot\\{file_path}"
                else:
                    file_path = f"webroot\\{self.__email}\\{file_path}"
                # if it's a not remove message
                # a remove message will be after a request of a client
                # to delete message for everyone, if the message is a file
                # in order to delete the file on the clients side
                if file_data != REMOVE:
                    modified_files_path.append(file_path)
                    for _ in range(2):
                        try:
                            with open(file_path, "wb") as f:
                                f.write(file_data)
                            break
                        except FileNotFoundError:
                            os.makedirs("\\".join(file_path.split("\\")[:-1]))
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

    def upload_file_(self, chat_id: str, filepath: str = "", delete_file: bool = False) -> None:
        if filepath == "":
            filepath = askopenfilename()
            if filepath == "" or not os.path.isfile(filepath):
                return
        ok, sock, _ = self.login(verbose=False)
        if not ok:
            raise ValueError("email or password incorrect, could not login to upload file")
        with open(filepath, "rb") as f:
            file_data = f.read()
        file_name = filepath.split("\\")[-1]
        request = f"{'file'.ljust(30)}{str(len(chat_id)).ljust(15)}{chat_id}" \
                  f"{str(len(file_name)).ljust(15)}{file_name}".encode() + file_data
        if not sock.send_message(request):
            showerror("Failed to upload file", "Could not upload the file, lost connection to server.")
            return
        if delete_file:
            os.remove(filepath)
        sock.close()

    @staticmethod
    def send_message(chat_id: str | int, msg: str, sock: EncryptedProtocolSocket) -> bool:
        chat_id = str(chat_id)
        request = f"{'msg'.ljust(30)}{str(len(chat_id)).ljust(15)}{chat_id}{msg}".encode()
        if not sock.send_message(request):
            showerror("Failed to send message", f"Could not send the message, lost connection to server.")
            return False
        status_msg = sock.receive_message().decode()
        if "not ok" in status_msg:
            showerror("Failed to send message", f"Could not send the message, server error.")
            return False
        return True

    @staticmethod
    def familiarize_user_with(other_email: str, sock: EncryptedProtocolSocket) -> bool:
        request = f"{'familiarize user with'.ljust(30)}{other_email}".encode()
        if not sock.send_message(request):
            showerror(f"Failed to familiarize user", "lost connection to server.")
            return False
        response = sock.receive_message()
        if "not ok" in response.decode():
            # showerror(f"Failed to familiarize user", response.split(b"not ok")[1].decode())
            return False
        return True

    @staticmethod
    def new_chat(other_email: str, sock: EncryptedProtocolSocket) -> bool:
        request = f"{'new chat'.ljust(30)}{other_email}".encode()
        if not sock.send_message(request):
            showerror(f"Failed to create new chat with '{other_email}'", "lost connection to server.")
            return False
        response = sock.receive_message()
        if "not ok" in response.decode():
            showerror(f"Failed to create new chat with '{other_email}'", "server error.")
            return False
        return True

    @staticmethod
    def new_group(other_emails: list[str], group_name: str, sock: EncryptedProtocolSocket) -> tuple[bool, str]:
        request = f"{'new chat'.ljust(30)}{group_name}".encode() + pickle.dumps(other_emails)
        if not sock.send_message(request):
            showerror(f"Failed to create new group", "lost connection to server.")
            return False, ""
        response = sock.receive_message().decode()
        if "not ok" in response:
            showerror(f"Failed to create new group", "server error.")
            return False, ""
        chat_id = response.split("ok")[-1].strip()
        return True, chat_id

    @staticmethod
    def add_user_to_group(other_email: str, chat_id: str, sock: EncryptedProtocolSocket) -> bool:
        request = f"{'add user'.ljust(30)}{str(len(chat_id)).ljust(15)}{chat_id}{other_email}".encode()
        if not sock.send_message(request):
            showerror(f"Failed to add '{other_email}' to group", "lost connection to server.")
            return False
        status_msg = sock.receive_message()
        if "not ok" in status_msg.decode():
            showerror(f"Failed to add '{other_email}' to group", "server error.")
            return False
        return True

    @staticmethod
    def remove_user_from_group(other_email: str, chat_id: str, sock: EncryptedProtocolSocket) -> bool:
        request = f"{'remove user'.ljust(30)}{str(len(chat_id)).ljust(15)}{chat_id}{other_email}".encode()
        if not sock.send_message(request):
            showerror(f"Failed to remove '{other_email}' from group", "lost connection to server.")
            return False
        status_msg = sock.receive_message()
        if "not ok" in status_msg.decode():
            showerror(f"Failed to remove '{other_email}' from group", "server error.")
            return False
        return True

    def make_call(self, chat_id: str) -> bool:
        # go to 'users' file of this chat and make call to users
        # OR
        # change the way a call works and call the chat_id and the server
        # will handle who to call
        # TODO: finish
        raise NotImplementedError

    def upload_profile_picture(self, path_to_picture: os.PathLike | str = None) -> bool:
        if path_to_picture is None:  # ask for file
            file_types = [("PNG", "*.png"), ("JPG", "*.jpg"), ("JPEG", "*.jpeg")]
            path_to_picture = askopenfilename(filetypes=file_types)
            if path_to_picture == "" or not os.path.isfile(path_to_picture):
                return False
        if not check_size(path_to_picture):  # check image size
            showerror("Profile Picture", "Image size is invalid,\nmust be at least 64x64.")
            return False
        ok, sock, _ = self.login(verbose=False)
        if not ok:
            raise ValueError("email or password incorrect, could not login to upload file")
        with open(path_to_picture, "rb") as f:
            file_data = f.read()
        request = f"{'upload profile picture'.ljust(30)}".encode() + file_data
        if not sock.send_message(request):
            showerror(
                "Upload Profile Picture Error", "Could not upload the file, lost connection to server.")
            return False
        sock.close()
        return True

    def upload_group_picture(self, chat_id: str, path_to_picture: os.PathLike | str = None) -> bool:
        if path_to_picture is None:  # ask for file
            file_types = [("PNG", "*.png"), ("JPG", "*.jpg"), ("JPEG", "*.jpeg")]
            path_to_picture = askopenfilename(filetypes=file_types)
            if path_to_picture == "" or not os.path.isfile(path_to_picture):
                return False
        if not check_size(path_to_picture):  # check image size
            showerror("Group Picture", "Image size is invalid,\nmust be at least 64x64.")
            return False
        ok, sock, _ = self.login(verbose=False)
        if not ok:
            raise ValueError("email or password incorrect, could not login to upload file")
        with open(path_to_picture, "rb") as f:
            file_data = f.read()
        request = f"{'upload group picture'.ljust(30)}{str(len(chat_id)).ljust(15)}{chat_id}".encode() + file_data
        if not sock.send_message(request):
            showerror(
                "Upload Group Picture Error", "Could not upload the file, lost connection to server.")
            return False
        sock.close()
        return True

    @staticmethod
    def delete_message_for_me(chat_id: str, message_index: int, root: Tk | Toplevel,
                              sock: EncryptedProtocolSocket) -> bool:
        # close the MessageOptions window
        root.destroy()
        request = f"{'delete message for me'.ljust(30)}{str(len(chat_id)).ljust(15)}{chat_id}{message_index}"
        if not sock.send_message(request.encode()):
            showerror("Delete Message For Me Error", "Could not delete the message.")
            return False
        return True

    @staticmethod
    def delete_message_for_everyone(chat_id: str, message_index: int, root: Tk | Toplevel,
                                    sock: EncryptedProtocolSocket) -> bool:
        # close the MessageOptions window
        root.destroy()
        request = f"{'delete message for everyone'.ljust(30)}{str(len(chat_id)).ljust(15)}{chat_id}{message_index}"
        if not sock.send_message(request.encode()):
            showerror("Delete Message For Me Error", "Could not delete the message.")
            return False
        return True
