"""
###############################################
Author: Omer Dagry
Mail: omerdagry@gmail.com
Final Date:  (dd/mm/yyyy) TODO: add date, and copy this to all files


TODO: add a file in each chat of a pickled dict -> {email: number_of_unread_msgs}
      each time a msg is sent increment number_of_unread_msgs for all the users
      each time a user enters the chat set his number_of_unread_msgs to 0
###############################################
"""
import os
import ssl
import sys
import rsa
import time
import socket
import pickle
import random
import shutil
import string
import logging
import hashlib
import smtplib
import datetime
import threading
import traceback

from typing import *
from email.mime.text import MIMEText
from SyncDB import SyncDatabase, FileDatabase
from email.mime.multipart import MIMEMultipart
from server_encrypted_protocol_socket import ServerEncryptedProtocolSocket


# Constants
# logging
LOG_DIR = 'log'
LOG_LEVEL = logging.DEBUG
LOG_FILE = LOG_DIR + "/ChatEase-Server.log"
LOG_FORMAT = "%(levelname)s | %(asctime)s | %(processName)s | %(message)s"
# Others
# Chat id's possible characters
CHAT_ID_CHARS = [letter for letter in string.ascii_uppercase + string.ascii_lowercase + string.digits]
random.shuffle(CHAT_ID_CHARS)
# Server email and special app password
SERVER_EMAIL = "project.twelfth.grade@gmail.com"
SERVER_EMAIL_APP_PASSWORD = "hbqbubnlppqxmupy"
# Paths
SERVER_DATA = "Data\\Server_Data\\"
USERS_DATA = "Data\\Users_Data\\"
# IP & Port
IP = "0.0.0.0"
PORT = 8820
SERVER_IP_PORT = (IP, PORT)
# Blocking Clients
BLOCK_TIME = 60 * 5
BLOCK_AFTER_X_EXCEPTIONS = 100
EXCEPTIONS_WINDOW_TIME = 60 * 5

# Globals
print_ = print
# File DBs
# email_password_file_database -> {email: password, another email: password, ...}
email_password_file_database = FileDatabase(f"{SERVER_DATA}email_password", ignore_existing=True)
# email_user_file_database -> {email: username, another email: another username, ...}
email_user_file_database = FileDatabase(f"{SERVER_DATA}email_username", ignore_existing=True)
# chat_id_users_database -> {chat_id: [email, another_email], another_chat_id: [email, another_email], ...}
chat_id_users_file_database = FileDatabase(f"{SERVER_DATA}chat_id_users", ignore_existing=True)
# user_online_status_database ->
# {email: ["Online", number_of_live_connection], email: ["Offline", last_seen - datetime.datetime], ...}
user_online_status_file_database = FileDatabase(f"{SERVER_DATA}user_online_status", ignore_existing=True)
# Sync DBs
# {email (str): password (str)}
email_password_database = SyncDatabase(email_password_file_database, False, max_reads_together=1000)
# {email (str), username (str)}
email_user_database = SyncDatabase(email_user_file_database, False, max_reads_together=1000)
# {chat_id (str): users (set[str])}
chat_id_users_database = SyncDatabase(chat_id_users_file_database, False, max_reads_together=1000)
# {email (str): status (list[str, int | datetime.datetime])}
user_online_status_database = SyncDatabase(user_online_status_file_database, False, max_reads_together=1000)
# Others
clients_sockets = []
printing_lock = threading.Lock()
received_exception_from: dict[str, set[datetime.datetime]] = {}  # {ip: {time of exception (for each exception)}}
blocked_ips: dict[str, datetime.datetime] = {}  # {ip: time of block}
add_exception_lock = threading.Lock()
blocked_client_lock = threading.Lock()

# Create All Needed Directories
os.makedirs(f"{SERVER_DATA}", exist_ok=True)
os.makedirs(f"{USERS_DATA}", exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


def print(*values: object, sep: str | None = " ", end: str | None = "\n"):
    printing_lock.acquire()
    print_(*values, sep=sep, end=end)
    printing_lock.release()


def start_server(my_public_key: rsa.PublicKey, my_private_key: rsa.PrivateKey) -> ServerEncryptedProtocolSocket:
    """ creates server socket binds it and returns it """
    server_socket = ServerEncryptedProtocolSocket(my_public_key, my_private_key)
    try:
        server_socket.bind(SERVER_IP_PORT)
        print(f"Server is up !! ({PORT = })")
        logging.info(f"Server is up !! ({PORT = })")
        server_socket.listen()
    except OSError:
        logging.debug(f"The Port {PORT} Is Taken.")
        print(f"The Port {PORT} Is Taken.")
        sys.exit(1)
    return server_socket


def accept_client(server_socket: ServerEncryptedProtocolSocket) \
        -> tuple[ServerEncryptedProtocolSocket | None, tuple[str, int] | None]:
    """ except client with a timeout of 2 seconds, if there is no connection in 2 seconds returns None"""
    global clients_sockets
    server_socket.settimeout(2)
    try:
        client_socket, client_addr = server_socket.accept()
    except (socket.error, ConnectionError):
        return None, None
    clients_sockets.append(client_socket)
    logging.info("[Server]: New Connection From: '%s:%s'" % (client_addr[0], client_addr[1]))
    print("[Server]: New Connection From: '%s:%s'" % (client_addr[0], client_addr[1]))
    return client_socket, client_socket.getpeername()


def write_to_file(file_path: str, mode: str, data: bytes | str) -> None:
    """ write to file """
    with open(file_path, mode) as f:
        f.write(data)


def read_from_file(file_path: str, mode: str) -> str | bytes:
    """ read a file """
    with open(file_path, mode) as f:
        data: str | bytes = f.read()
    return data


def add_exception_for_ip(ip: str) -> None:
    """ Add the ip to a list of exceptions """
    add_exception_lock.acquire()
    if ip in received_exception_from:
        received_exception_from[ip].add(datetime.datetime.now())
    else:
        received_exception_from[ip] = {datetime.datetime.now()}
    logging.debug(f"[Server]: added the exception that was received while handling '{ip}' to the list of exceptions")
    add_exception_lock.release()


def watch_exception_dict():
    """
    watch over the list of exceptions received from IPs, if an IP has more than BLOCK_AFTER_X_EXCEPTIONS
    exception in the last EXCEPTIONS_WINDOW_TIME minutes block that IP for BLOCK_TIME minutes

    open a thread for this function
    """
    while True:
        current_time = datetime.datetime.now()
        remove_ips = []
        for ip in received_exception_from:
            remove = []
            for ex_time in received_exception_from[ip]:
                if (current_time - ex_time).seconds > EXCEPTIONS_WINDOW_TIME:
                    remove.append(ex_time)
            for ex_time in remove:
                received_exception_from[ip].remove(ex_time)
            # if we received more than BLOCK_AFTER_X_EXCEPTIONS exception in the last EXCEPTIONS_WINDOW_TIME from
            # the same ip, block this ip for BLOCK_TIME
            if len(received_exception_from[ip]) >= BLOCK_AFTER_X_EXCEPTIONS:
                blocked_client_lock.acquire()
                blocked_ips[ip] = current_time
                blocked_client_lock.release()
                msg = f"[Server]: the IP '{ip}' received more than {BLOCK_AFTER_X_EXCEPTIONS} exception " \
                      f"in under than {EXCEPTIONS_WINDOW_TIME} seconds. this IP is blocked for {BLOCK_TIME}"
                print(msg)
                logging.warning(msg)
                remove_ips.append(ip)  # can't change during iteration
        for ip in remove_ips:
            received_exception_from.pop(ip)
        time.sleep(10)  # check every 10 seconds


def block(path: str) -> bool:
    """ :return: True to signal the "lock" is acquired """
    """
        create a folder "folder_name" to block another thread from touching a 
        specific resource file of the user/chat because we are reading the file 
        and then writing back and if someone does it at the same time with us 
        something will be lost, so blocking like this allows to block only for 
        this specific chat and not block all the clients threads, which is what we want
    """
    while True:
        try:
            os.makedirs(path, exist_ok=False)
            break
        except OSError:  # locked
            time.sleep(0.0005)
    return True


def unblock(path: str) -> bool:
    """ :return: True to signal the "lock" isn't acquired """
    if not os.path.isdir(path):
        logging.debug(f"The 'lock' is already unlocked. (path - '{path}')")
        raise ValueError(f"The 'lock' is already unlocked. (path - '{path}')")
    shutil.rmtree(path)
    return False


def add_chat_id_to_user_chats(user_email: str, chat_id: str) -> bool:
    """ add chat id to user chats file """
    if user_email not in email_password_database:
        return False
    block(f"{USERS_DATA}{user_email}\\chats block")
    if not os.path.isfile(f"{USERS_DATA}{user_email}\\chats"):
        write_to_file(f"{USERS_DATA}{user_email}\\chats", "wb", b"")
    try:
        chats_list: set = pickle.loads(read_from_file(f"{USERS_DATA}{user_email}\\chats", "rb"))
    except EOFError:
        chats_list = set()
    chats_list.add(chat_id)
    write_to_file(f"{USERS_DATA}{user_email}\\chats", "wb", pickle.dumps(chats_list))
    unblock(f"{USERS_DATA}{user_email}\\chats block")
    add_new_data_to(user_email, f"{USERS_DATA}{user_email}\\chats")
    return True


def remove_chat_id_from_user_chats(user_email: str, chat_id: str) -> bool:
    """ remove chat id from user chats file """
    if user_email not in email_password_database:
        return False
    block(f"{USERS_DATA}{user_email}\\chats block")
    if not os.path.isfile(f"{USERS_DATA}{user_email}\\chats"):
        write_to_file(f"{USERS_DATA}{user_email}\\chats", "wb", b"")
    try:
        chats_set: set = pickle.loads(read_from_file(f"{USERS_DATA}{user_email}\\chats", "rb"))
    except EOFError:
        chats_set = set()
    if chat_id in chats_set:
        chats_set.remove(chat_id)
    write_to_file(f"{USERS_DATA}{user_email}\\chats", "wb", pickle.dumps(chats_set))
    unblock(f"{USERS_DATA}{user_email}\\chats block")
    add_new_data_to(user_email, f"{USERS_DATA}{user_email}\\chats")
    return True


def get_user_chats_file(email: str) -> set[str]:
    """ returns all the chat ids of a user """
    block(f"{USERS_DATA}{email}\\chats block")
    if not os.path.isfile(f"{USERS_DATA}{email}\\chats"):
        write_to_file(f"{USERS_DATA}{email}\\chats", "wb", b"")
    try:
        chats_set: set = pickle.loads(read_from_file(f"{USERS_DATA}{email}\\chats", "rb"))
    except EOFError:
        chats_set = set()
    unblock(f"{USERS_DATA}{email}\\chats block")
    return chats_set


def add_user_to_group_users_file(email: str, chat_id: str) -> bool:
    """ add user to group users file, updates the new data """
    block(f"{USERS_DATA}{chat_id}\\users_block")
    if not os.path.isfile(f"{USERS_DATA}{chat_id}\\users"):
        write_to_file(f"{USERS_DATA}{chat_id}\\users", "wb", b"")
    try:
        users_set: set = pickle.loads(read_from_file(f"{USERS_DATA}{chat_id}\\users", "rb"))
    except EOFError:
        users_set = set()
    users_set.add(email)
    write_to_file(f"{USERS_DATA}{chat_id}\\users", "wb", pickle.dumps(users_set))
    unblock(f"{USERS_DATA}{chat_id}\\users_block")
    add_new_data_to(get_group_users(chat_id), f"{USERS_DATA}{chat_id}\\users")
    return True


def remove_user_from_group_users_file(email: str, chat_id: str) -> bool:
    """ remove user from group users file """
    block(f"{USERS_DATA}{chat_id}\\users_block")
    if not os.path.isfile(f"{USERS_DATA}{chat_id}\\users"):
        write_to_file(f"{USERS_DATA}{chat_id}\\users", "wb", b"")
    try:
        users_set: set = pickle.loads(read_from_file(f"{USERS_DATA}{chat_id}\\users", "rb"))
    except EOFError:
        users_set = set()
    if email not in users_set:
        return False
    users_set.remove(email)
    write_to_file(f"{USERS_DATA}{chat_id}\\users", "wb", pickle.dumps(users_set))
    unblock(f"{USERS_DATA}{chat_id}\\users_block")
    add_new_data_to(get_group_users(chat_id), f"{USERS_DATA}{chat_id}\\users")
    return True


def get_group_users(chat_id: str) -> set[str]:
    """ get group users file """
    block(f"{USERS_DATA}{chat_id}\\users_block")
    if not os.path.isfile(f"{USERS_DATA}{chat_id}\\users"):
        write_to_file(f"{USERS_DATA}{chat_id}\\users", "wb", b"")
    try:
        users_set: set = pickle.loads(read_from_file(f"{USERS_DATA}{chat_id}\\users", "rb"))
    except EOFError:
        users_set = set()
    unblock(f"{USERS_DATA}{chat_id}\\users_block")
    return users_set


def is_user_in_chat(user_email: str, chat_id: str) -> bool:
    """ check if a user is in a chat
    :param user_email: the email of the user to check if he is in the chat
    :param chat_id: the id of the chat that will be checked
    :return: True if the user is in the chat else False
    """
    if user_email not in email_password_database:
        return False
    if not os.path.isfile(f"{USERS_DATA}{user_email}\\chats"):
        return False
    try:
        chats_list: set = pickle.loads(read_from_file(f"{USERS_DATA}{user_email}\\chats", "rb"))
    except EOFError:
        chats_list = set()
    if chat_id not in chats_list:
        return False
    return True


def add_new_data_to(emails: str | Iterable[str], new_data_paths: str | Iterable[str]) -> None:
    """ add new file to user new_data file
    :param emails: the emails of the users to add the new data to there new_data file
    :param new_data_paths: the paths to the new files / updated files
    """
    if isinstance(emails, str):
        emails: set[str] = {emails}
    elif not isinstance(emails, set):  # some other type of iterable
        emails: set[str] = set(emails)
    if isinstance(new_data_paths, str):
        new_data_paths: list[str] = [new_data_paths]
    for email in emails:
        if email not in email_password_database:
            continue
        block(f"{USERS_DATA}{email}\\new data not free")
        try:
            os.makedirs(f"{USERS_DATA}{email}\\", exist_ok=True)
            if not os.path.isfile(f"{USERS_DATA}{email}\\new_data"):
                write_to_file(f"{USERS_DATA}{email}\\new_data", "wb", b"")
            try:
                new_data_list: set = pickle.loads(read_from_file(f"{USERS_DATA}{email}\\new_data", "rb"))
            except EOFError:
                new_data_list = set()
            new_data_list.update(new_data_paths)
            write_to_file(f"{USERS_DATA}{email}\\new_data", "wb", pickle.dumps(new_data_list))
        finally:
            unblock(f"{USERS_DATA}{email}\\new data not free")


def get_new_data_of(email: str) -> set[str]:
    """ get new_data of a user, AND CLEAR THE NEW DATA FILE ! """
    if email not in email_password_database:
        return set()
    block(f"{USERS_DATA}{email}\\new data not free")
    try:
        if not os.path.isfile(f"{USERS_DATA}{email}\\new_data"):
            write_to_file(f"{USERS_DATA}{email}\\new_data", "wb", b"")
        try:
            new_data_list: set = pickle.loads(read_from_file(f"{USERS_DATA}{email}\\new_data", "rb"))
        except EOFError:
            new_data_list = set()
        # clear new data
        write_to_file(f"{USERS_DATA}{email}\\new_data", "wb", b"")
        return new_data_list
    finally:
        unblock(f"{USERS_DATA}{email}\\new data not free")


def add_one_on_one_chat(email_1: str, email_2: str):
    """ adds a chat id (of type one on one) to users one_on_one_chats file """
    for email in [email_1, email_2]:
        block(f"{USERS_DATA}{email}\\one_on_one_chats_block")
        if not os.path.isfile(f"{USERS_DATA}{email}\\one_on_one_chats"):
            write_to_file(f"{USERS_DATA}{email}\\one_on_one_chats", "wb", b"")
        try:
            one_on_one_set: set = pickle.loads(read_from_file(f"{USERS_DATA}{email}\\one_on_one_chats", "rb"))
        except EOFError:
            one_on_one_set = set()
        one_on_one_set.add(email_2)
        write_to_file(f"{USERS_DATA}{email}\\one_on_one_chats", "wb", pickle.dumps(one_on_one_set))
        unblock(f"{USERS_DATA}{email}\\one_on_one_chats_block")
        add_new_data_to(email, f"{USERS_DATA}{email}\\one_on_one_chats")


def get_one_on_one_chats_list_of(email: str) -> set[str]:
    """ get all the chats (not groups) of a user """
    if email not in email_password_database:
        return set()
    block(f"{USERS_DATA}{email}\\one_on_one_chats_block")
    try:
        one_on_one_set: set = pickle.loads(read_from_file(f"{USERS_DATA}{email}\\one_on_one_chats", "rb"))
    except EOFError:
        one_on_one_set = set()
    unblock(f"{USERS_DATA}{email}\\one_on_one_chats_block")
    return one_on_one_set


def known_to_each_other(emails: list[str]) -> None:
    """ mark emails as known to each other
    :param emails: the emails of the users that are known to each other
    """
    for email in emails:
        if email not in email_user_database:
            continue
        block(f"{USERS_DATA}{email}\\known_users_block")
        try:
            if not os.path.isfile(f"{USERS_DATA}{email}\\known_users"):
                write_to_file(f"{USERS_DATA}{email}\\known_users", "wb", b"")
            try:
                known_to_user: set = pickle.loads(read_from_file(f"{USERS_DATA}{email}\\known_users", "rb"))
            except EOFError:
                known_to_user = set()
            for email_2 in emails:
                if email == email_2 or email_2 not in email_user_database:
                    continue
                known_to_user.add(email_2)
                add_new_data_to(
                    email, f"known user profile picture|{USERS_DATA}{email_2}\\{email_2}_profile_picture.png")
            write_to_file(f"{USERS_DATA}{email}\\known_users", "wb", pickle.dumps(known_to_user))
        finally:
            unblock(f"{USERS_DATA}{email}\\known_users_block")
            add_new_data_to(email, f"{USERS_DATA}{email}\\known_users")


def get_user_known_users(email: str) -> set[str]:
    """ get all the users known to a user """
    block(f"{USERS_DATA}{email}\\known_users_block")
    if not os.path.isfile(f"{USERS_DATA}{email}\\known_users"):
        write_to_file(f"{USERS_DATA}{email}\\known_users", "wb", b"")
    try:
        known_to_user: set = pickle.loads(read_from_file(f"{USERS_DATA}{email}\\known_users", "rb"))
    except EOFError:
        known_to_user = set()
    unblock(f"{USERS_DATA}{email}\\known_users_block")
    return known_to_user


# TODO: handle picture for 1 on 1 chats (in sync func, send the user all the profile pictures of his known users)
def create_new_chat(ip: str, user_created: str, with_user: str) -> tuple[bool, str]:
    """ create a new chat (one on one, not group)
    :param ip: the ip of the clients
    :param user_created: the email of the user that created the chat
    :param with_user: the email of the user that the chat is created with
    :return: (True, chat_id) if the chat was created else (False, "")
    """
    # check that the 2 users exist
    if user_created not in email_user_database:
        return False, ""
    if with_user not in email_user_database:
        return False, "User Doesn't Exist."
    user_created_username = email_user_database[user_created]
    with_user_username = email_user_database[with_user]
    user_created_one_on_one_chats = get_one_on_one_chats_list_of(user_created)
    if with_user in user_created_one_on_one_chats:
        return False, "Chat Already Exists."
    chat_id = "".join(random.choices(CHAT_ID_CHARS, k=20))
    while not chat_id_users_database.safe_set(chat_id, {user_created, with_user}):
        chat_id = "".join(random.choices(CHAT_ID_CHARS, k=20))
    try:
        os.makedirs(f"{USERS_DATA}{chat_id}\\data\\chat", exist_ok=False)
        os.makedirs(f"{USERS_DATA}{chat_id}\\data\\files", exist_ok=True)
    # if OSError is raised, that means that there is already a chat with this chat id
    # and there shouldn't be according to the chat_id_users_database
    except OSError:
        return False, ""
    # chat metadata
    write_to_file(f"{USERS_DATA}{chat_id}\\name", "wb", pickle.dumps([user_created_username, with_user_username]))
    write_to_file(f"{USERS_DATA}{chat_id}\\type", "w", "chat")
    write_to_file(f"{USERS_DATA}{chat_id}\\users", "wb", b"")
    add_user_to_group_users_file(user_created, chat_id)
    add_user_to_group_users_file(with_user, chat_id)
    # add chat id to each user chats
    add_chat_id_to_user_chats(user_created, chat_id)
    add_chat_id_to_user_chats(with_user, chat_id)
    # add with_user to user_created one_on_one_chats file
    # add user_created to with_user one_on_one_chats file
    add_one_on_one_chat(user_created, with_user)
    #
    known_to_each_other([with_user, user_created])
    add_new_data_to([user_created, with_user], f"{USERS_DATA}{chat_id}")
    send_msg(ip, user_created, chat_id, f"{user_created} added {with_user}.", add_message=True)
    return True, chat_id


def create_new_group(ip: str, user_created: str, users: list[str], group_name: str) -> tuple[bool, str]:
    """ create a new group """
    users.append(user_created)
    #
    for email in set(users):
        if email not in email_user_database:
            return False, ""
    chat_id = "".join(random.choices(CHAT_ID_CHARS, k=20))
    while not chat_id_users_database.safe_set(chat_id, set(users)):
        chat_id = "".join(random.choices(CHAT_ID_CHARS, k=20))
    try:
        os.makedirs(f"{USERS_DATA}{chat_id}\\data\\chat", exist_ok=False)
        os.makedirs(f"{USERS_DATA}{chat_id}\\data\\files", exist_ok=True)
    # if OSError is raised, that means that there is already a chat with this chat id
    # and there shouldn't be according to the chat_id_users_database
    except OSError:
        return False, ""
    # chat metadata
    write_to_file(f"{USERS_DATA}{chat_id}\\name", "wb", pickle.dumps([group_name]))
    write_to_file(f"{USERS_DATA}{chat_id}\\type", "w", "group")
    write_to_file(f"{USERS_DATA}{chat_id}\\users", "wb", b"")
    write_to_file(
        f"{USERS_DATA}{chat_id}\\group_picture.png", "wb",
        read_from_file(f"{SERVER_DATA}\\default_group_picture.png", "rb")
    )
    for email in users:
        add_chat_id_to_user_chats(email, chat_id)
        add_user_to_group_users_file(email, chat_id)
    known_to_each_other(users)
    add_new_data_to(users, f"{USERS_DATA}{chat_id}")
    for user in users:
        if user != user_created:
            send_msg(ip, user_created, chat_id, f"{user_created} added {user}.", add_message=True)
    return True, chat_id


def add_user_to_group(ip: str, from_user: str, add_user: str, group_id: str) -> bool:
    """ add a user to group (all the messages from before will be visible to him) """
    if from_user not in email_user_database or add_user not in email_user_database or \
            not is_user_in_chat(from_user, group_id):
        return False
    group_users = get_group_users(group_id)  # without the new user
    # update database
    chat_id_users_database.add(group_id, add_user)
    # update file of users
    add_user_to_group_users_file(add_user, group_id)
    #
    add_chat_id_to_user_chats(add_user, group_id)
    add_new_data_to(add_user, f"{USERS_DATA}{group_id}")  # make the entire chat as new data for the added user
    add_new_data_to(group_users, f"{USERS_DATA}{group_id}\\users")  # only update the users file for the others
    send_msg(ip, from_user, group_id, f"{from_user} added {add_user}.", add_message=True)
    return True


def remove_user_from_group(ip: str, from_user: str, remove_user: str, group_id: str) -> bool:
    """ remove a user from group (all the messages will be deleted for him) """
    if from_user not in email_user_database or remove_user not in email_user_database or \
            not is_user_in_chat(from_user, group_id):
        return False
    # update database
    chat_id_users_database.remove_set(group_id, remove_user)
    # update file of users
    remove_user_from_group_users_file(remove_user, group_id)
    #
    remove_chat_id_from_user_chats(remove_user, group_id)
    add_new_data_to(remove_user, f"{USERS_DATA}{remove_user}\\chats")
    add_new_data_to(get_group_users(group_id), f"{USERS_DATA}{group_id}\\users")
    add_new_data_to(remove_user, f"remove - {USERS_DATA}{group_id}")
    send_msg(ip, from_user, group_id, f"{from_user} removed {remove_user}.", remove_msg=True)
    return True


def send_msg(ip: str, from_user: str, chat_id: str, msg: str,
             file_msg: bool = False, remove_msg: bool = False, add_message: bool = False) -> bool:
    """ send message (to chat/group)
    :param ip: the ip of the client that sent the request
    :param from_user: the email of the user that sent the msg
    :param chat_id: the id of the chat that the msg is being sent to
    :param msg: the msg
    :param file_msg: if a file was sent to a chat the send_file
                     function will call this function with file_msg=True
                     and the msg will be the file location
    :param remove_msg: a message that will say 'x removed y' and will be displayed different
    :param add_message: a message that will say 'x added y' and will be displayed different
    """
    # 3 types: regular msg / file msg (if it's a file) / remove msg (if someone removed someone)
    msg_type = "msg" if not file_msg and not remove_msg and not remove_msg and not add_message else \
        "file" if file_msg else "remove" if remove_msg else "add" if add_message else None
    if msg_type is None:
        return False
    lock = block(f"{USERS_DATA}{chat_id}\\data\\not free")
    try:
        users_in_chat: set = chat_id_users_database.get(chat_id)
        if users_in_chat is None or not is_user_in_chat(from_user, chat_id):
            return False
        list_of_chat_files = os.listdir(f"{USERS_DATA}{chat_id}\\data\\chat\\")
        if list_of_chat_files:
            latest = int(max(list_of_chat_files))
            try:
                data: dict = pickle.loads(read_from_file(f"{USERS_DATA}{chat_id}\\data\\chat\\{latest}", "rb"))
            except EOFError:
                data = {}
            first_chat = False
        else:
            latest = -1
            data = {}
            first_chat = True
        if len(data) >= 800 or first_chat:
            #        index:             [from_user, msg, msg_type, deleted_for, delete_for_all, seen by, time]
            time_formatted = datetime.datetime.now().strftime("%m/%d/%Y %H:%M")
            data = {(latest + 1) * 800: [from_user, msg, msg_type, [], False, [], time_formatted]}
            write_to_file(f"{USERS_DATA}{chat_id}\\data\\chat\\{latest + 1}", "wb", pickle.dumps(data))
        else:
            #        index:              [from_user, msg, msg_type, deleted_for, delete_for_all, seen by, time]
            time_formatted = datetime.datetime.now().strftime("%m/%d/%Y %H:%M")
            data[max(data.keys()) + 1] = [from_user, msg, msg_type, [], False, [], time_formatted]
            write_to_file(f"{USERS_DATA}{chat_id}\\data\\chat\\{latest}", "wb", pickle.dumps(data))
        # when finished remove the folder
        lock = unblock(f"{USERS_DATA}{chat_id}\\data\\not free")
        # add the new file / updated file to the new data of all the users in the chat
        latest = latest + 1 if len(data) >= 800 or first_chat else latest
        add_new_data_to(users_in_chat, f"{USERS_DATA}{chat_id}\\data\\chat\\{latest}")
        return True
    except Exception as e:
        add_exception_for_ip(ip)
        logging.warning(f"received exception while handling '{ip}' exception: "
                        f"{''.join(traceback.format_exception(e))} (user: '{from_user}', func: 'send_msg')")
        return False
    finally:
        if lock:
            unblock(f"{USERS_DATA}{chat_id}\\data\\not free")


def send_file(ip: str, from_user: str, chat_id: str, file_data: bytes, file_name: str) -> bool:
    """ send file (to chat/group)
    :param ip: the ip of the client that sent the request
    :param from_user: the email of the user that sent the file
    :param chat_id: the id of the chat that the file is being sent to
    :param file_data: the data of the file
    :param file_name: the name of the file
    """
    try:
        users_in_chat: set = chat_id_users_database.get(chat_id)
        if users_in_chat is None or not is_user_in_chat(from_user, chat_id):
            return False
        location = f"{USERS_DATA}{chat_id}\\data\\files\\"
        # if there is already a file with this name, create new name
        if os.path.isfile(location + file_name):
            new_file_name = ".".join(file_name.split(".")[:-1]) + "_1" + file_name.split(".")[-1]
            i = 2
            while os.path.isfile(location + new_file_name):
                new_file_name = ".".join(file_name.split(".")[:-1]) + f"_{i}" + file_name.split(".")[-1]
                i += 1
        else:
            new_file_name = file_name
        # save the file
        with open(location + new_file_name, "wb") as file:
            file.write(file_data)
        #                                                       remove USERS_DATA
        if send_msg(ip, from_user, chat_id, "\\".join((location + new_file_name).split("\\")[2:]), file_msg=True):
            add_new_data_to(users_in_chat, location + new_file_name)
            return True
        else:
            os.remove(location + new_file_name)
            return False
    except Exception as e:
        add_exception_for_ip(ip)
        logging.warning(f"received while handling '{ip}' exception: "
                        f"{''.join(traceback.format_exception(e))} (user: '{from_user}', func: 'send_file')")
        return False


def delete_msg_for_me(ip: str, from_user: str, chat_id: str, index_of_msg: int) -> bool:
    """ delete massage only for yourself (in chat/group) """
    users_in_chat: set = chat_id_users_database.get(chat_id)
    if users_in_chat is None or not is_user_in_chat(from_user, chat_id):
        return False
    file_number = index_of_msg // 800  # there are 800 messages per file
    if not os.path.isfile(f"{USERS_DATA}{chat_id}\\data\\chat\\{file_number}"):
        return False  # index_of_msg is invalid
    lock = block(f"{USERS_DATA}{chat_id}\\data\\not free")
    try:
        try:
            data: dict = pickle.loads(read_from_file(f"{USERS_DATA}{chat_id}\\data\\chat\\{file_number}", "rb"))
        except EOFError:
            data = {}
        # msg -> [from_user, msg, msg_type, deleted_for, delete_for_all, seen by, time]
        msg = data.get(index_of_msg)
        if msg is not None:
            deleted_for = msg[3]
            if from_user not in deleted_for:
                deleted_for.append(from_user)
            msg[3] = deleted_for
            data[index_of_msg] = msg
            write_to_file(f"{USERS_DATA}{chat_id}\\data\\chat\\{file_number}", "wb", pickle.dumps(data))
        else:
            unblock(f"{USERS_DATA}{chat_id}\\data\\not free")
            return False
        unblock(f"{USERS_DATA}{chat_id}\\data\\not free")
        add_new_data_to(from_user, f"{USERS_DATA}{chat_id}\\data\\chat\\{file_number}")
        return True
    except Exception as e:
        add_exception_for_ip(ip)
        logging.debug(f"received while handling '{ip}' exception: "
                      f"{''.join(traceback.format_exception(e))} (user: '{from_user}', func: 'delete_msg_for_me')")
        return False
    finally:
        if lock:
            unblock(f"{USERS_DATA}{chat_id}\\data\\not free")


def delete_msg_for_everyone(ip: str, from_user: str, chat_id: str, index_of_msg: int) -> bool:
    """ delete massage for everyone (in chat/group) """
    users_in_chat: set = chat_id_users_database.get(chat_id)
    if users_in_chat is None or not is_user_in_chat(from_user, chat_id):
        return False
    file_number = index_of_msg // 800  # there are 800 messages per file
    if not os.path.isfile(f"{USERS_DATA}{chat_id}\\data\\chat\\{file_number}"):
        return False  # index_of_msg is invalid
    lock = block(f"{USERS_DATA}{chat_id}\\data\\not free")
    try:
        try:
            data: dict = pickle.loads(read_from_file(f"{USERS_DATA}{chat_id}\\data\\chat\\{file_number}", "rb"))
        except EOFError:
            data = {}
        # msg -> [from_user, msg, msg_type, deleted_for, delete_for_all, seen by, time]
        msg = data.get(index_of_msg)
        if msg is not None and msg[0] == from_user:
            msg[1] = "This Message Was Deleted."
            msg[4] = True
            data[index_of_msg] = msg
            write_to_file(f"{USERS_DATA}{chat_id}\\data\\chat\\{file_number}", "wb", pickle.dumps(data))
            if msg[2] == "file":  # file msg, remove the file as well
                #                                              file name
                os.remove(f"{USERS_DATA}{chat_id}\\data\\files\\{msg[1]}")
                # tell all the clients to remove this file on their side
                add_new_data_to(users_in_chat, f"remove - {USERS_DATA}{chat_id}\\data\\files\\{msg[1]}")
        else:
            unblock(f"{USERS_DATA}{chat_id}\\data\\not free")
            return False
        unblock(f"{USERS_DATA}{chat_id}\\data\\not free")
        add_new_data_to(users_in_chat, f"{USERS_DATA}{chat_id}\\data\\chat\\{file_number}")
        return True
    except Exception as e:
        add_exception_for_ip(ip)
        logging.debug(f"received while handling '{ip}' exception: {''.join(traceback.format_exception(e))} "
                      f"(user: '{from_user}', func: 'delete_msg_for_everyone')")
        return False
    finally:
        if lock:
            unblock(f"{USERS_DATA}{chat_id}\\data\\not free")


def upload_profile_picture(email: str, picture_file: bytes) -> bool:
    """ change your profile picture """
    write_to_file(f"{USERS_DATA}{email}\\{email}_profile_picture.png", "wb", picture_file)
    known_to_user = get_user_known_users(email)
    known_to_user.add(email)
    for user in known_to_user:
        add_new_data_to(user, f"known user profile picture|{USERS_DATA}{email}\\{email}_profile_picture.png")
    return True


def update_group_photo(from_user: str, chat_id: str, picture_file: bytes) -> bool:
    """ change group picture """
    users_in_chat: set = chat_id_users_database.get(chat_id)
    if users_in_chat is None or not is_user_in_chat(from_user, chat_id):
        return False
    write_to_file(f"{USERS_DATA}\\{chat_id}\\group_profile_picture.png", "wb", picture_file)
    group_users = get_group_users(chat_id)
    for user in group_users:
        add_new_data_to(user, f"{USERS_DATA}\\{chat_id}\\group_profile_picture.png")
    return True


def send_mail(to: str, subject: str, body: str, html: str = "") -> None:
    """ send an email (for signup and password reset) """
    em = MIMEMultipart('alternative')
    em["From"] = SERVER_EMAIL
    em["To"] = to
    em["Subject"] = subject
    em.attach(MIMEText(body, "plain"))
    if html != "":
        em.attach(MIMEText(html, "html"))
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=ssl.create_default_context()) as smtp:
        smtp.login(SERVER_EMAIL, SERVER_EMAIL_APP_PASSWORD)
        smtp.sendmail(SERVER_EMAIL, to, em.as_string())
    logging.info(f"sent email to {to}")


def signup(username: str, email: str, password: str, client_sock: ServerEncryptedProtocolSocket) -> tuple[bool, str]:
    """  signup
    :param username: the username
    :param email: the email of the user
    :param password: the md5 hash of the password
    :param client_sock: the socket of the client
    """
    # check that the email isn't registered
    if email in email_user_database:
        return False, "Error"
    client_sock.send_message("signup".ljust(30).encode())
    # create confirmation code
    confirmation_code = random.choices(range(0, 10), k=6)
    confirmation_code = "".join(map(str, confirmation_code))
    # send confirmation code to the email
    send_mail(email, "Confirmation Code",
              f"Your code is: {confirmation_code}",
              f"<div style='color: rgb(18, 151, 228); font-size: xx-large;'>Your code is: {confirmation_code}</div>")
    print(f"[Server]: A mail was sent to '{email}' with the confirmation code '{confirmation_code}'")
    # send client a msg that says that we are waiting for a confirmation code
    client_sock.send_message(f"{'confirmation_code'.ljust(30)}".encode())
    # receive the response from the client and set a timeout of 5 minutes
    msg = client_sock.recv_message(timeout=60*5)
    # if response timed out
    if msg == b"":
        return False, "Request timeout."
    msg = msg.decode()
    # check the response
    if msg[: 30].strip() != "confirmation_code" or msg[30:] != confirmation_code:
        logging.info(f"signup attempt (for '{email}') failed - "
                     f"got wrong confirmation code from user trying to signup as '{username}'")
        return False, "Confirmation code is incorrect."
    # if username doesn't exist
    if email not in email_user_database and len(username) <= 40:
        # add username and password to the email_password_database & email_user_database
        email_password_database[email] = hashlib.md5(password.encode()).hexdigest().lower()
        email_user_database[email] = username
        user_online_status_database[email] = ["Offline", datetime.datetime.now()]
        logging.info(f"signup attempt successful - email: '{email}', username: '{username}'")
        # create user directory and files
        os.makedirs(f"{USERS_DATA}{email}", exist_ok=True)
        write_to_file(f"{USERS_DATA}{email}\\chats", "wb", b"")
        write_to_file(f"{USERS_DATA}{email}\\known_users", "wb", b"")
        write_to_file(f"{USERS_DATA}{email}\\new_data", "wb", b"")
        write_to_file(f"{USERS_DATA}{email}\\one_on_one_chats", "wb", b"")
        write_to_file(
            f"{USERS_DATA}{email}\\{email}_profile_picture.png", "wb",
            read_from_file(f"{SERVER_DATA}\\default_group_picture.png", "rb")
        )
        print(f"Signed up successfully {email}-{username}")
        return True, "Signed up successfully."
    return False, "Email already registered."


def reset_password(email: str, username: str, client_sock: ServerEncryptedProtocolSocket) -> tuple[bool, str]:
    """ reset password
    :param email: the email of the user that wants to reset their password
    :param username: the username
    :param client_sock: the socket of the client
    """
    if email not in email_user_database:
        return False, ""
    if email_user_database[email] != username:
        return False, ""
    client_sock.send_message("reset password".ljust(30).encode())
    username = email_user_database[email]
    # create confirmation code
    confirmation_code = random.choices(range(0, 10), k=6)
    confirmation_code = "".join(map(str, confirmation_code))
    # send confirmation code to the email
    send_mail(email, "Confirmation Code",
              f"Your code is: {confirmation_code}",
              f"<div style='color: rgb(18, 151, 228); font-size: xx-large;'>Your code is: {confirmation_code}</div>")
    print(f"[Server]: A mail was sent to '{email}' with the confirmation code '{confirmation_code}'")
    # send client a msg that says that we are waiting for a confirmation code
    client_sock.send_message(f"{'confirmation_code'.ljust(30)}".encode())
    # receive the response from the client and set a timeout of 5 minutes
    msg = client_sock.recv_message(timeout=60 * 5)
    # if response timed out
    if msg == b"":
        return False, "Request timeout."
    msg = msg.decode()
    # check the response
    if msg[: 30].strip() != "confirmation_code" or msg[30:] != confirmation_code:
        logging.info(f"reset password attempt (for '{email}') failed - got wrong confirmation code from user")
        return False, "Confirmation code is incorrect."
    client_sock.send_message(f"{'reset password'.ljust(30)}{'ok'.ljust(6)}".encode())
    # send client a msg that says that we are waiting for a new password
    client_sock.send_message("new password".ljust(30).encode())
    # receive the response from the client and set a timeout of 5 minutes
    msg = client_sock.recv_message(timeout=60 * 5)
    # if response timed out
    if msg == b"":
        return False, "Request timeout."
    msg = msg.decode()
    # validate the response
    if msg[: 30].strip() != "new password":
        return False, ""
    # extract password
    password = msg[30:]
    # set new password
    email_password_database[email] = hashlib.md5(password.encode()).hexdigest().lower()
    print(f"reset password attempt successful - email: '{email}', username: '{username}'.")
    logging.info(f"reset password attempt successful - email: '{email}', username: '{username}'.")
    return True, "Password changed successfully."


def login(email: str, password: str) -> bool:
    """ login
    :param email: the email of the user
    :param password: the md5 hash of the password
    """
    time.sleep(random.random())  # prevent timing attack (sleep between 0 and 1 seconds)
    if email not in email_user_database:
        return False
    user_password_hashed_hash = email_password_database[email]
    if user_password_hashed_hash != hashlib.md5(password.encode()).hexdigest().lower():
        return False
    if user_online_status_database[email][0] == "Online":
        user_online_status_database[email][1] += 1
    else:
        user_online_status_database[email] = ["Online", 1]
    return True


def sync(email: str, sync_all: bool = False) -> bytes:
    """ send user all the requested files (those who are new or changed / all his files) """
    block(f"{USERS_DATA}{email}\\sync")
    new_data: list[str] = list(get_new_data_of(email))  # get new data and clear
    if not sync_all:
        add = []
        remove = []
        for i in range(len(new_data)):
            path = new_data[i]
            if os.path.isdir(path):
                # add all files in dir and sub-dirs
                for path2, _, files in os.walk(path):
                    add.extend(map(lambda p: os.path.join(path2, p), files))  # (can't change during iteration)
                remove.append(i)  # remove the folder itself from new_data list (can't change during iteration)
        for index in remove:
            # move the item we want to remove to the end of the list and then pop it,
            # better performance because if we remove an item that isn't the last all the items
            # after it need to move 1 index back, unless we remove the last item in the list
            new_data[-1], new_data[index] = new_data[index], new_data[-1]
            new_data.pop()
        new_data.extend(add)
        del add, remove
    else:
        # user metadata
        # new_data = [f"{USERS_DATA}{email}\\known_users", f"{USERS_DATA}{email}\\{email}_profile_picture.png"]
        new_data = [f"{USERS_DATA}{email}\\{file}" for file in os.listdir(f"{USERS_DATA}{email}\\")]
        # user chats and groups
        chat_ids_set = get_user_chats_file(email)
        for chat_id in chat_ids_set:
            for path2, _, files in os.walk(f"{USERS_DATA}{chat_id}"):
                new_data.extend(map(lambda p: os.path.join(path2, p), files))
        known_to_user = get_user_known_users(email)
        for other_email in known_to_user:
            new_data.append(f"known user profile picture|{USERS_DATA}{other_email}\\{other_email}_profile_picture.png")
    # make a dictionary -> {file_path: file_data}
    # also remember user_online_status_database (last seen and online)
    known_to_user = get_user_known_users(email)
    users_status: dict[str, int | datetime.datetime | str] = \
        dict(((user, user_online_status_database.get(user)[1]) for user in known_to_user))
    current_time = datetime.datetime.now()
    for user in users_status:
        if isinstance(users_status[user], datetime.datetime):
            strftime = "%H:%M %m/%d/%Y" if (current_time - users_status[user]).days >= 1 else "%H:%M"
            users_status[user] = f'Last Seen {users_status[user].strftime(strftime)}'
        else:
            users_status[user] = "Online"
    file_name_data: dict[str, str] = {"users_status": pickle.dumps(users_status)}
    for file in new_data:
        # if it's a chat file, we need to lock it
        if file.count("\\") == 4:
            try:
                chat_path = "\\".join(file.split("\\")[:-1])  # remove chat file, leave chat_id and data dir
                if os.path.isdir(chat_path) and chat_path.endswith("\\data"):
                    file_path_for_user = "\\".join(file.split("\\")[2:])
                    chat_id = file_path_for_user.split("\\")[0]
                    block(f"{USERS_DATA}{chat_id}\\data\\not free")
                    file_name_data[file_path_for_user] = read_from_file(file, "rb")
                    unblock(f"{USERS_DATA}{chat_id}\\data\\not free")
                    continue
            except Exception:
                pass
        if os.path.isfile(file):
            #                            remove Data\\Users_Data
            file_path_for_user = "\\".join(file.split("\\")[2:])
            file_name_data[file_path_for_user] = read_from_file(file, "rb")
        elif file.startswith("known user profile picture|"):
            real_file_path = "".join(file.split("known user profile picture|")[1:])
            file_path_for_user = "\\".join(real_file_path.split("\\")[3:])
            file_name_data[f"profile_pictures\\{file_path_for_user}"] = read_from_file(real_file_path, "rb")
        elif file.startswith("remove - "):
            file_name_data[" - ".join(file.split(" - ")[1:])] = "remove"
        elif file == f"{USERS_DATA}{email}\\sync":
            pass
        else:
            logging.debug(f"[Server]: error in 'sync' function, FileNotFound: '{file}'")
    # pickle the dictionary
    sync_res: bytes = pickle.dumps(file_name_data)
    #
    unblock(f"{USERS_DATA}{email}\\sync")
    return sync_res


def call_group(from_email: str, chat_id: str):
    """ make a call to all the users in the chat - chat_id """
    """
        !!! open a thread to call this func !!!

        1. check if at least two of the users in the chat are connected
        2. start a UDP server on port x and send the user that started the call the port,
           and for the other users send a "call message" with the port number
    """
    users_in_chat = get_group_users(chat_id)
    # TODO: finish this func


def login_or_signup_response(mode: str, status: str, reason: str) -> bytes:
    """ make a response for login/signup according to the protocol
    :param mode: login or signup
    :param status: 'ok' or 'not ok'
    :param reason: the reason
    """
    return f"{mode.ljust(30)}{status.lower().ljust(6)}{reason}".encode()


def request_response(cmd: str, status: str, reason: str) -> bytes:
    """ make a response according to the protocol
    :param cmd: the requested command
    :param status: 'ok' or 'not ok'
    :param reason: the reason
    """
    return f"{cmd.ljust(30)}{status.lower().ljust(6)}{reason}".encode()


def handle_client(client_socket: ServerEncryptedProtocolSocket, client_ip_port: tuple[str, int]) -> None:
    """ handle a client (each client gets a thread that runs this function) """
    logged_in, signed_up, stop, email, username = False, False, False, None, None
    try:
        # let client login / signup and login
        while not logged_in:
            client_socket.settimeout(5)  # add timeout of 5 seconds, if there is no request within this time, close con
            try:
                msg = client_socket.recv_message()
            except socket.timeout:
                add_exception_for_ip(client_ip_port[0])
                client_socket.send_message(login_or_signup_response("login", "not ok", "Request Timed Out."))
                stop = True
                break
            client_socket.settimeout(None)
            msg = msg.decode()
            cmd = msg[: 30].strip()
            # check if the msg is signup msg or login, else throw the msg
            # because the client hasn't logged in yet
            if cmd == "login":
                len_email = int(msg[30: 45].strip())
                email = msg[45: 45 + len_email].lower()
                password = msg[45 + len_email:]
                if not login(email, password):
                    client_socket.send_message(
                        login_or_signup_response("login", "not ok", "Incorrect email or password !")
                    )
                    stop = True
                    break
                logged_in = True
                username = email_user_database[email]
                client_socket.send_message(login_or_signup_response("login", "ok", username))
                del msg, cmd, len_email, password
            elif cmd == "signup" and not signed_up:
                len_username = int(msg[30: 32].strip())
                username = msg[32: 32 + len_username]
                len_email = int(msg[32 + len_username: 47 + len_username].strip())
                email = msg[47 + len_username: 47 + len_username + len_email].lower()
                password = msg[47 + len_username + len_email:]
                ok, reason = signup(username, email, password, client_socket)
                if not ok:
                    client_socket.send_message(login_or_signup_response("signup", "not ok", reason))
                    stop = True
                    break
                client_socket.send_message(login_or_signup_response("signup", "ok", ""))
                signed_up = True
                del msg, len_username, len_email, password, reason, ok
            elif cmd == "signup" and signed_up:  # don't allow 1 connection to signup multiple times
                stop = True
                break
            elif cmd == "reset password":
                email_len = int(msg[30: 45])
                tmp_email = msg[45: 45 + email_len].lower()
                tmp_username = msg[45 + email_len:]
                status, reason = reset_password(tmp_email, tmp_username, client_socket)
                client_socket.send_message(request_response(cmd, "ok" if status else "not ok", reason))
                if not status:
                    stop = True
                    break
            else:
                add_exception_for_ip(client_ip_port[0])
                stop = True
                break
        if not stop and logged_in:
            if email not in email_user_database:  # double check that this user exists
                logging.debug(f"[Server]: The email '{email}' doesn't exists in the database.")
                raise ValueError(f"[Server]: The email '{email}' doesn't exists in the database.")
            # set thread name                    email            number of connections (of this client)
            threading.current_thread().name = f"{email} (client - {user_online_status_database[email][1]})"
            client_socket.settimeout(None)
            username = email_user_database[email]
            password = None  # no need to save the password, set to None
            #
            print(f"[Server]: '%s:%s' logged in as '{email}-{username}'." % client_ip_port)
            logging.info(f"[Server]: '%s:%s' logged in as '{email} - {username}'." % client_ip_port)
            #
            # handle client's requests until client disconnects
            stay_encoded = {"file", "upload profile picture", "upload group picture", "new group"}
            while True:
                request: bytes
                request = client_socket.recv_message()
                if request == b"" or request == b"bye":
                    break
                cmd = request[: 30].decode().strip()
                # decode the request only if it's not a file
                request = request if cmd in stay_encoded else request.decode()
                # TODO: add user in chat X + add a function to modify seen by lists of messages (call it for these msgs)
                response = None
                if cmd == "sync new":
                    request: str
                    response = sync(email)
                    response = f"{'sync new'.ljust(30)}".encode() + response
                    sync_msg = True
                elif cmd == "sync all":
                    request: str
                    sync_msg = True
                    response = sync(email, sync_all=True)
                    response = cmd.ljust(30).encode() + response
                elif cmd == "msg":
                    request: str
                    len_chat_id = int(request[30: 45].strip())  # currently 20
                    chat_id = request[45: len_chat_id + 45]
                    msg = request[len_chat_id + 45:]
                    ok = send_msg(client_ip_port[0], email, chat_id, msg)
                    response = request_response(cmd, "ok" if ok else "not ok", "")
                elif cmd == "delete for everyone":
                    request: str
                    chat_id_len = int(request[30: 45].strip())
                    chat_id = request[45: 45 + chat_id_len]
                    message_index = int(request[45 + chat_id_len:].strip())
                    delete_msg_for_everyone(client_ip_port[0], email, chat_id, message_index)
                elif cmd == "file":
                    request: bytes
                    chat_id_len = int(request[30: 45].strip())
                    chat_id = request[45: 45 + chat_id_len].decode()
                    file_name_len = int(request[45 + chat_id_len: 60 + chat_id_len].strip())
                    file_name = request[60 + chat_id_len: 60 + chat_id_len + file_name_len].decode()
                    file_data = request[60 + chat_id_len + file_name_len:]
                    send_file(client_ip_port[0], email, chat_id, file_data, file_name)
                elif cmd == "delete for me":
                    request: str
                    chat_id_len = int(request[30: 45].strip())
                    chat_id = request[45: 45 + chat_id_len]
                    message_index = int(request[45 + chat_id_len:])
                    delete_msg_for_me(client_ip_port[0], email, chat_id, message_index)
                elif cmd == "call":
                    request: str
                    # TODO: finish
                    pass
                elif cmd == "add user":
                    request: str
                    chat_id_len = int(request[30: 45].strip())
                    chat_id = request[45: 45 + chat_id_len]
                    other_user = request[45 + chat_id_len:]
                    ok = add_user_to_group(client_ip_port[0], email, other_user, chat_id)
                    response = request_response(cmd, "ok" if ok else "not ok", "")
                elif cmd == "remove user":
                    request: str
                    chat_id_len = int(request[30: 45].strip())
                    chat_id = request[45: 45 + chat_id_len]
                    other_user = request[45 + chat_id_len:]
                    ok = remove_user_from_group(client_ip_port[0], email, other_user, chat_id)
                    response = request_response(cmd, "ok" if ok else "not ok", "")
                elif cmd == "upload profile picture":
                    request: bytes
                    status = upload_profile_picture(email, request[30:])
                    response = request_response(cmd, "ok" if status else "not ok", "")
                elif cmd == "upload group picture":
                    request: bytes
                    len_chat_id = int(request[30: 45].decode().strip())  # currently 20
                    chat_id = request[45: len_chat_id + 45].decode()
                    status = update_group_photo(email, chat_id, request[len_chat_id + 45:])
                    response = request_response(cmd, "ok" if status else "not ok", "")
                elif cmd == "familiarize user with":
                    request: str
                    other_email = request[30:]
                    if other_email in email_user_database:
                        known_to_each_other([email, other_email])
                        response = request_response(cmd, "ok", "")
                    else:
                        response = request_response(cmd, "not ok", "user doesn't exists")
                elif cmd == "new chat":
                    request: str
                    other_email = request[30:]
                    status, chat_id = create_new_chat(client_ip_port[0], email, other_email)
                    response = request_response(cmd, "ok" if status else "not ok", chat_id)
                elif cmd == "new group":
                    request: bytes
                    group_name_len = int(request[30: 45].decode().strip())
                    group_name = request[45: 45 + group_name_len].decode()
                    other_users_list: list[str] = pickle.loads(request[45: group_name_len:])
                    status, chat_id = create_new_group(client_ip_port[0], email, other_users_list, group_name)
                    response = request_response(cmd, "ok" if status else "not ok", chat_id)
                else:
                    msg = f"[Server]: '%s:%s' Logged In As '{email}-{username}' - sent unknown cmd {cmd}" % \
                          client_ip_port
                    print(msg)
                    logging.warning(msg)
                    continue
                # send the response
                if response is not None:
                    client_socket.send_message(response)
    except Exception as err:
        add_exception_for_ip(client_ip_port[0])
        if not isinstance(err, ConnectionError):
            username = "Unknown username" if "username" not in locals() else username
            logging.warning(f"[Server]: error while handling '%s:%s' "
                            f"('{username}'): {''.join(traceback.format_exception(err))}" % client_ip_port)
    finally:
        client_socket.close()
        print(f"[Server]: Client '%s:%s' disconnected." % client_ip_port)
        logging.info(f"[Server]: Client '%s:%s' disconnected." % client_ip_port)
        if email in email_user_database and user_online_status_database[email][0] == "Online":
            if user_online_status_database[email][1] == 1:
                user_online_status_database[email] = ["Offline", datetime.datetime.now()]  # last seen
            else:
                user_online_status_database[email][1] -= 1  # reduce online count by 1 (each connection is 1)


def main():
    # logging configuration
    logging.basicConfig(format=LOG_FORMAT, filename=LOG_FILE, level=LOG_LEVEL)
    # generate public & private rsa keys, and start the server
    print("generating private and public keys")
    my_public_key, my_private_key = rsa.newkeys(2048, poolsize=os.cpu_count())
    print("done generating")
    server_socket = start_server(my_public_key, my_private_key)
    # exception watch thread
    watch_exception_dict_thread = threading.Thread(target=watch_exception_dict, daemon=True)
    watch_exception_dict_thread.start()
    #
    clients_threads: list[threading.Thread] = []
    clients_threads_socket: dict[threading.Thread, ServerEncryptedProtocolSocket] = {}
    while True:
        client_socket, client_ip_port = accept_client(server_socket)  # try to accept client
        if client_socket is not None:  # if there was a client waiting to connect
            client_ip_port: tuple[str, int]
            # check if the client's IP is blocked
            blocked_client_lock.acquire()
            if client_ip_port[0] in blocked_ips:
                # blocked but BLOCK_TIME passed
                if (datetime.datetime.now() - blocked_ips[client_ip_port[0]]).seconds > BLOCK_TIME:
                    blocked_ips.pop(client_ip_port[0])
                else:  # blocked
                    msg = f"[Server]: the IP '{client_ip_port[0]}' is blocked and tried to " \
                          f"connect again. closing connection."
                    print(msg)
                    logging.warning(msg)
                    blocked_client_lock.release()
                    try:
                        client_socket.close()  # close connection with blocked client
                    except (socket.error, ConnectionError):
                        pass
                    continue  # skip blocked client
            blocked_client_lock.release()
            # pass the client to the 'handle client' function (with a thread)
            client_thread = threading.Thread(target=handle_client, args=(client_socket, client_ip_port),
                                             daemon=True, name="%s:%s" % client_ip_port)
            client_thread.start()
            clients_threads.append(client_thread)
            clients_threads_socket[client_thread] = client_socket
        # check if someone disconnected
        remove = []
        for client_thread in clients_threads:
            if not client_thread.is_alive():
                remove.append(client_thread)
                try:
                    client_socket = clients_threads_socket[client_thread]
                    client_socket.close()
                except (socket.error, ConnectionError):
                    pass
                clients_threads_socket.pop(client_thread)
        for client_thread in remove:
            clients_threads.remove(client_thread)
        time.sleep(0.05)  # prevent high cpu usage from the while loop


def unblock_all():
    chat_or_group_block_folders = ["users_block", "data\\not free"]
    user_block_folders = ["chats block", "sync", "new data not free", "one_on_one_chats_block", "known_users_block"]
    for folder in os.listdir(USERS_DATA):
        if os.path.isdir(f"{USERS_DATA}{folder}"):
            if os.path.isfile(f"{folder}\\users"):  # group/chat
                files_n_folders = set(os.listdir(f"{USERS_DATA}{folder}"))
                for folder_name in chat_or_group_block_folders:
                    if folder_name in files_n_folders:
                        shutil.rmtree(f"{USERS_DATA}{folder}\\{folder_name}")
            else:
                files_n_folders = set(os.listdir(f"{USERS_DATA}{folder}"))
                for folder_name in user_block_folders:
                    if folder_name in files_n_folders:
                        shutil.rmtree(f"{USERS_DATA}{folder}\\{folder_name}")


if __name__ == '__main__':
    try:
        unblock_all()
        main()
    except KeyboardInterrupt:  # exit nicely on KeyboardInterrupt
        pass
    finally:
        for email in user_online_status_database.keys():
            if user_online_status_database[email][1] == "Online":
                user_online_status_database[email] = ["Offline", datetime.datetime.now()]
