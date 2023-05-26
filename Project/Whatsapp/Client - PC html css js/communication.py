"""
###############################################
Author: Omer Dagry
Mail: omerdagry@gmail.com
Date: 30/05/2023 (dd/mm/yyyy)
###############################################
"""

import os
import pickle
import shutil
import socket

from tkinter import *
from typing import Literal
from threading import Thread
from tkinter import messagebox
from photo_tools import check_size
from tkinter.filedialog import askopenfilename
from ClientSecureSocket import ClientEncryptedProtocolSocket

# Constants
CALL = "call|"
REMOVE = "remove"
USER_STATUS = "update users_status"
SYNC_CODE = "sync".ljust(30).encode()


def showerror(title: str | None, message: str | None, **options) -> None:
    """ display a little error window """
    print(f"Show error: {title = }: {message = }")
    Thread(target=messagebox.showerror, args=(title, message,), kwargs=options).start()


def signup_request(username: str, email: str, password: str, server_ip_port: tuple[str, int],
                   sock: ClientEncryptedProtocolSocket | None = None, return_status: bool = False) \
        -> tuple[bool, None | ClientEncryptedProtocolSocket] | tuple[bool, None | ClientEncryptedProtocolSocket, str]:
    """ signup first step """
    # signup (length 30)|len username (max 40)|username|len email (length 10)|
    # email|password (fixed length - md5 hash length)
    signup_msg = f"{'signup'.ljust(30)}{str(len(username)).ljust(2)}" \
                 f"{username}{str(len(email)).ljust(15)}{email}{password}".encode()
    if sock is None:
        sock = ClientEncryptedProtocolSocket()
        sock.connect(server_ip_port)
    if not sock.send_message(signup_msg):
        sock.close()
        if not return_status:
            showerror("Signup Error", "Could not send signup request, lost connection to server.")
            return False, None
        return False, None, "Lost connection to server !"
    response = sock.recv_message().decode()
    if response != "signup".ljust(30):
        if not return_status:
            return False, None
        return False, None, response[36:]
    if not return_status:
        return True, sock
    return True, sock, ""


def send_confirmation_code(sock: ClientEncryptedProtocolSocket, confirmation_code: str,
                           verbose: bool, signup_or_reset: Literal["signup", "reset"]) -> bool:
    """ confirmation code (for signup and reset password) """
    confirmation_code_msg = sock.recv_message().decode()
    if confirmation_code_msg.strip() == "confirmation_code":
        if not sock.send_message(f"{'confirmation_code'.ljust(30)}{confirmation_code}".encode()):
            showerror(
                "Signup Error" if signup_or_reset == "signup" else "Reset Password Error",
                "Could not send confirmation code, lost connection to server."
            )
            sock.close()
            return False
    else:
        return False
    # signup (length 30)   status (length 6)   reason
    # reset password (length 30)   status (length 6)   reason
    response = sock.recv_message().decode()
    if (response[:30].strip() != "signup" and signup_or_reset == "signup") or \
            (response[:30].strip() != "reset password" and signup_or_reset == "reset"):
        return False
    response = response[30:]
    if response[:6].strip() != "ok":
        response = response[6:]
        if verbose:
            print("Signup" if signup_or_reset == "Reset Password" else f" Failed, Server Sent: {response}")
        return False
    return True


def signup(username: str, email: str, password: str, server_ip_port: tuple[str, int], verbose: bool = True,
           sock: ClientEncryptedProtocolSocket | None = None, login_after: bool = True) \
        -> tuple[bool, None | ClientEncryptedProtocolSocket]:
    """ signup full process """
    status, sock = signup_request(username, email, password, server_ip_port, sock)
    if not status:
        return False, None
    status = send_confirmation_code(sock, input("Please Enter The Confirmation Code: "), verbose, "signup")
    if not status:
        return False, None
    if verbose:
        print("Signed up Successfully.")
    if login_after:
        communication = Communication(email, password, server_ip_port)
        ok, sock, username = communication.login(verbose, sock)
        if not ok:
            return False, None
    return True, sock


def reset_password_request(username: str, email: str, server_ip_port: tuple[str, int]) \
        -> tuple[bool, ClientEncryptedProtocolSocket | None]:
    """ reset password first step """
    sock = ClientEncryptedProtocolSocket()
    sock.connect(server_ip_port)
    if not sock.send_message(f"{'reset password'.ljust(30)}{str(len(email)).ljust(15)}{email}{username}".encode()):
        showerror(
            "Reset Password Error", "Could not send reset password request, lost connection to server.")
        sock.close()
        return False, None
    response = sock.recv_message().decode()
    if response != "reset password".ljust(30):
        sock.close()
        return False, None
    return True, sock


def reset_password_choose_password(sock: ClientEncryptedProtocolSocket, password: str) -> bool:
    """ reset password last step """
    new_password_msg = sock.recv_message()
    if new_password_msg != f"{'new password'.ljust(30)}".encode():
        sock.close()
        return False
    sock.send_message(f"{'new password'.ljust(30)}{password}".encode())
    reset_password_status = sock.recv_message()
    if "not ok" in reset_password_status.decode() or reset_password_status == b"":
        sock.close()
        return False
    return True


def reset_password(username: str, email: str, server_ip_port: tuple[str, int], verbose: bool) \
        -> tuple[bool, ClientEncryptedProtocolSocket | None]:
    """ reset password full process, the returned socket isn't logged in !! """
    status, sock = reset_password_request(username, email, server_ip_port)
    if not status:
        return False, None
    status = send_confirmation_code(
        sock, input('Please enter your confirmation code (sent to your email): '), verbose, "reset"
    )
    if not status:
        return False, None
    status = reset_password_choose_password(sock, input('Please enter your new password: '))
    return status, sock if status else None


class Communication:
    """ a class that contains all the communications that require a username and password """
    def __init__(self, email: str, password: str, server_ip_port: tuple[str, int]) -> None:
        """
        :param email: the username
        :param password: the md5 hash of the real password
        :param server_ip_port: a tuple of the server IP and port
        """
        self.__email = email
        self.__password = password
        self.__server_ip_port = server_ip_port

    def login(self, verbose: bool = True, sock: ClientEncryptedProtocolSocket | None = None) \
            -> tuple[bool, None | ClientEncryptedProtocolSocket, str]:
        """ login """
        # login (length 30)     len email (length 10)   email    password (fixed length - md5 hash length)
        login_msg = f"{'login'.ljust(30)}{str(len(self.__email)).ljust(15)}{self.__email}{self.__password}".encode()
        if sock is None:
            sock = ClientEncryptedProtocolSocket()
            try:
                sock.connect(self.__server_ip_port)
            except (ConnectionError, socket.error):
                return False, None, "Can't reach the server."
        if not sock.send_message(login_msg):
            showerror("Login Error", "Could not send login request, lost connection to server.")
            sock.close()
            return False, None, "Lost connection to server."
        # login (length 30)   status (length 6)   reason
        response = sock.recv_message().decode()
        if response[:30].strip() != "login":
            return False, None, "Error"
        response = response[30:]
        if response[:6].strip() != "ok":
            response = response[6:]
            if verbose:
                print(f"Login Failed, Server Sent: {response}")
            sock.close()
            return False, None, response
        if verbose:
            print("Logged in Successfully.")
        return True, sock, response[6:]

    def login_sync(self, verbose: bool = True, sock: ClientEncryptedProtocolSocket | None = None,
                   sync_mode: str = "all") -> tuple[bool, None | ClientEncryptedProtocolSocket, str]:
        """ login & let the server know this connection is to sync data """
        status, sock, reason = self.login(verbose=verbose, sock=sock)
        if status:
            sync_sock_notify_msg = f"{f'this is a sync sock {sync_mode}'.ljust(30)}".encode()
            if not sock.send_message(sync_sock_notify_msg):
                sock.close()
                return False, None, "Error notifying the server about sync sock"
        return status, sock, reason

    def sync(self, sock: ClientEncryptedProtocolSocket) -> tuple[bool, list[str], list[str], dict[str, int]]:
        """ sync once
        :param sock: this sock must be logged in using login_sync
        :return: True if new data received else False, list of the modified/new files, list of deleted files/folders
        """
        response = sock.recv_message(timeout=1)
        #                         cmd                  {}             str     bytes | str
        # response -> f"{'sync new/all'.ljust(30)}{empty-dict/dict[file_name, file_data]}"
        if response[:30] != SYNC_CODE:
            return False, [], [], {}
        try:
            files_dict = pickle.loads(response[30:])
        except EOFError:
            files_dict = {}
        if files_dict:
            deleted_files_path: list[str | os.PathLike] = []
            modified_files_path: list[str | os.PathLike] = []
            ongoing_calls: dict[str, int] = {}
            for file_path, file_data in files_dict.items():
                file_data: bytes
                if file_path.startswith(self.__email):
                    file_path = f"webroot\\{file_path}"
                else:
                    file_path = f"webroot\\{self.__email}\\{file_path}"
                # if it's a not remove message
                # a remove message will be after a request of a client
                # to delete message for everyone, if the message is a file
                # in order to delete the file on the clients side
                if file_data != REMOVE and CALL not in file_path:
                    modified_files_path.append(file_path)
                    for _ in range(2):
                        try:
                            with open(file_path, "wb") as f:
                                f.write(file_data)
                            break
                        except FileNotFoundError:
                            os.makedirs("\\".join(file_path.split("\\")[:-1]))
                elif CALL in file_path:
                    file_data: str
                    ongoing_calls["|".join(file_data.split("|")[2:])] = int(file_data.split("|")[1])
                elif os.path.isfile(file_path):  # a file was deleted in a chat
                    deleted_files_path.append(file_path)
                    os.remove(file_path)
                elif os.path.isdir(file_path):  # the user was removed from the chat
                    deleted_files_path.append(file_path)
                    shutil.rmtree(file_path)
            return True, modified_files_path, deleted_files_path, ongoing_calls
        else:
            return False, [], [], {}

    def upload_file(self, chat_id: str | int, filename: str = "", root: Tk = None,
                    delete_file: bool = False, send_file_active: list[bool] = None) -> None:
        """ upload a file """
        upload_thread = Thread(
            target=self.upload_file_, args=(str(chat_id), filename, delete_file, send_file_active), daemon=True
        )
        upload_thread.start()
        if root is not None:
            root.destroy()

    def upload_file_(self, chat_id: str, filepath: str, delete_file: bool, send_file_active: list[bool]) -> None:
        """ upload a file (don't call this func, call upload_file_) """
        if filepath == "":
            root = Tk()
            root.attributes('-topmost', True)  # Display the dialog in the foreground.
            root.iconify()  # Hide the little window.
            filepath = askopenfilename(parent=root)
            root.destroy()
            if send_file_active:
                send_file_active[0] = False
            if filepath == "" or filepath is None or not os.path.isfile(filepath):
                return
        elif send_file_active:
            send_file_active[0] = False
        ok, sock, _ = self.login(verbose=False)
        if not ok:
            raise ValueError("email or password incorrect, could not login to upload file")
        with open(filepath, "rb") as f:
            file_data = f.read()
        file_name = filepath.split("/")[-1]
        file_name = file_name.split("\\")[-1]
        request = f"{'file'.ljust(30)}{str(len(chat_id)).ljust(15)}{chat_id}" \
                  f"{str(len(file_name)).ljust(15)}{file_name}".encode() + file_data
        if not sock.send_message(request):
            showerror("Failed to upload file", "Could not upload the file, lost connection to server.")
            return
        if delete_file:
            os.remove(filepath)
        sock.close()

    @staticmethod
    def send_message(chat_id: str | int, msg: str, sock: ClientEncryptedProtocolSocket) -> bool:
        """ send a message """
        if len(msg) > 5000:
            showerror("Message To Long", f"Message length is {len(msg)}, and the maximum is 4999")
            return False
        chat_id = str(chat_id)
        request = f"{'msg'.ljust(30)}{str(len(chat_id)).ljust(15)}{chat_id}{msg}".encode()
        if not sock.send_message(request):
            showerror("Failed to send message", f"Could not send the message, lost connection to server.")
            return False
        status_msg = sock.recv_message().decode()
        if "not ok" in status_msg or status_msg == "":
            showerror("Failed to send message", f"Could not send the message, server error.")
            return False
        return True

    @staticmethod
    def familiarize_user_with(other_email: str, sock: ClientEncryptedProtocolSocket) -> bool:
        """ search for a user that isn't "known" to me, and make him "known" to me """
        request = f"{'familiarize user with'.ljust(30)}{other_email}".encode()
        if not sock.send_message(request):
            showerror(f"Failed to familiarize user", "lost connection to server.")
            return False
        response = sock.recv_message()
        if "not ok" in response.decode() or response == b"":
            # showerror(f"Failed to familiarize user", response.split(b"not ok")[1].decode())
            return False
        return True

    @staticmethod
    def new_chat(other_email: str, sock: ClientEncryptedProtocolSocket) -> bool:
        """ create a new chat (1 on 1) """
        request = f"{'new chat'.ljust(30)}{other_email}".encode()
        if not sock.send_message(request):
            showerror(f"Failed to create new chat with '{other_email}'", "lost connection to server.")
            return False
        response = sock.recv_message()
        if "not ok" in response.decode() or response == b"":
            showerror(f"Failed to create new chat with '{other_email}'", "server error.")
            return False
        return True

    @staticmethod
    def new_group(other_emails: list[str], group_name: str, sock: ClientEncryptedProtocolSocket) -> tuple[bool, str]:
        """ create new group """
        request = f"{'new group'.ljust(30)}{str(len(group_name)).ljust(15)}{group_name}".encode() + \
                  pickle.dumps(other_emails)
        if not sock.send_message(request):
            showerror(f"Failed to create new group", "lost connection to server.")
            return False, ""
        response = sock.recv_message().decode()
        if "not ok" in response or response == "":
            showerror(f"Failed to create new group", "server error.")
            return False, ""
        chat_id = response.split("ok")[-1].strip()
        return True, chat_id

    @staticmethod
    def add_user_to_group(other_email: str, chat_id: str, sock: ClientEncryptedProtocolSocket) -> bool:
        """ add a user to group """
        request = f"{'add user'.ljust(30)}{str(len(chat_id)).ljust(15)}{chat_id}{other_email}".encode()
        if not sock.send_message(request):
            showerror(f"Failed to add '{other_email}' to group", "lost connection to server.")
            return False
        status_msg = sock.recv_message()
        if "not ok" in status_msg.decode() or status_msg == b"":
            showerror(f"Failed to add '{other_email}' to group", "server error.")
            return False
        return True

    @staticmethod
    def remove_user_from_group(other_email: str, chat_id: str, sock: ClientEncryptedProtocolSocket) -> bool:
        """ remove a user from the group """
        request = f"{'remove user'.ljust(30)}{str(len(chat_id)).ljust(15)}{chat_id}{other_email}".encode()
        if not sock.send_message(request):
            showerror(f"Failed to remove '{other_email}' from group", "lost connection to server.")
            return False
        status_msg = sock.recv_message()
        if "not ok" in status_msg.decode() or status_msg == b"":
            showerror(f"Failed to remove '{other_email}' from group", "server error.")
            return False
        return True

    def make_call(self, chat_id: str) -> int | None:
        """
        send a request to the server to start a server for this call and
        notify the other users in the chat, and return the port for this call
        """
        ok, sock, _ = self.login(verbose=False)
        if not ok:
            raise ValueError("email or password incorrect, could not login to upload file")
        if not sock.send_message(f"{'call'.ljust(30)}{chat_id}".encode()):
            showerror(f"Failed to make a call", "lost connection to server.")
            return None
        port_message = sock.recv_message().decode()
        if "not ok" in port_message or port_message == "":
            showerror(f"Failed to make a call", "server error.")
            return None
        return int(port_message.split("ok")[1].strip())

    def upload_profile_picture(self, path_to_picture: os.PathLike | str = None) -> bool:
        """ upload profile picture """
        if path_to_picture is None:  # ask for file
            file_types = [("PNG", "*.png"), ("JPG", "*.jpg"), ("JPEG", "*.jpeg")]
            root = Tk()
            root.attributes('-topmost', True)  # Display the dialog in the foreground.
            root.iconify()  # Hide the little window.
            path_to_picture = askopenfilename(filetypes=file_types)
            root.destroy()
            if path_to_picture == "" or path_to_picture is None or not os.path.isfile(path_to_picture):
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
        """ upload group picture """
        if path_to_picture is None:  # ask for file
            file_types = [("PNG", "*.png"), ("JPG", "*.jpg"), ("JPEG", "*.jpeg")]
            root = Tk()
            root.attributes('-topmost', True)  # Display the dialog in the foreground.
            root.iconify()  # Hide the little window.
            path_to_picture = askopenfilename(filetypes=file_types)
            root.destroy()
            if path_to_picture == "" or path_to_picture is None or not os.path.isfile(path_to_picture):
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
    def delete_message_for_me(chat_id: str, message_index: int, sock: ClientEncryptedProtocolSocket) -> bool:
        """ delete message for me """
        request = f"{'delete for me'.ljust(30)}{str(len(chat_id)).ljust(15)}{chat_id}{message_index}"
        if not sock.send_message(request.encode()):
            showerror("Delete Message For Me Error", "Could not delete the message.")
            return False
        return True

    @staticmethod
    def delete_message_for_everyone(chat_id: str, message_index: int, sock: ClientEncryptedProtocolSocket) -> bool:
        """ delete message for everyone """
        request = f"{'delete for everyone'.ljust(30)}{str(len(chat_id)).ljust(15)}{chat_id}{message_index}"
        if not sock.send_message(request.encode()):
            showerror("Delete Message For Me Error", "Could not delete the message.")
            return False
        return True

    @staticmethod
    def mark_as_seen(sock: ClientEncryptedProtocolSocket, chat_id: str) -> None:
        """ mark all the messages in the chat as seen """
        request = f"{'user in chat'.ljust(30)}{chat_id}"
        if not sock.send_message(request.encode()):
            showerror("User in chat Error", "Lost connection to server.")
