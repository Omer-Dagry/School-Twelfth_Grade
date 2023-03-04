"""
###############################################
Author: Omer Dagry
Mail: omerdagry@gmail.com
Date: 06/01/2023 (dd/mm/yyyy)
###############################################
"""
import hashlib
import os
import ssl
import time
import socket
import pickle
import random
import shutil
import string
import logging
import smtplib
import datetime
import threading

from email.mime.text import MIMEText
from SyncDB import SyncDatabase, FileDatabase
from email.mime.multipart import MIMEMultipart
from protocol_socket import EncryptedProtocolSocket


# Constants
# logging
LOG_DIR = 'log'
LOG_LEVEL = logging.DEBUG
LOG_FILE = LOG_DIR + "/ChatEase-Server.log"
LOG_FORMAT = "%(levelname)s | %(asctime)s | %(processName)s | %(message)s"
#
CHAT_ID_CHARS = [letter for letter in string.ascii_uppercase + string.ascii_lowercase + string.digits]
random.shuffle(CHAT_ID_CHARS)
SERVER_EMAIL = "project.twelfth.grade@gmail.com"
SERVER_EMAIL_APP_PASSWORD = "hbqbubnlppqxmupy"
USERS_DATA = "Data\\Users_Data\\"
SERVER_DATA = "Data\\Server_Data\\"
IP = "127.0.0.1"
PORT = 8820

# Globals
printing_lock = threading.Lock()
clients_sockets = []
online_users = []

# Databases
# user_password_database -> {"email - username": password, "another email - another username": password, ...}
user_password_file_database = FileDatabase(f"{SERVER_DATA}user_password", ignore_existing=True)
# chat_id_users_database -> {chat_id: [email, another_email], another_chat_id: [email, another_email], ...}
chat_id_users_file_database = FileDatabase(f"{SERVER_DATA}chat_id_users", ignore_existing=True)
# user_online_status_database -> {email: ["Online", None], email: ["Offline" / last_seen - datetime.datetime]}
user_online_status_file_database = FileDatabase(f"{SERVER_DATA}user_online_status", ignore_existing=True)
#
user_password_database = SyncDatabase(user_password_file_database, False, max_reads_together=100)
chat_id_users_database = SyncDatabase(chat_id_users_file_database, False, max_reads_together=100)
user_online_status_database = SyncDatabase(user_online_status_file_database, False, max_reads_together=1000)

# Create All Needed Directories
os.makedirs(f"{SERVER_DATA}", exist_ok=True)
os.makedirs(f"{USERS_DATA}", exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


def start_server() -> EncryptedProtocolSocket:
    server_socket = EncryptedProtocolSocket()
    try:
        server_socket.bind((IP, PORT))
        printing_lock.acquire()
        print("Server Is Up!!")
        logging.info("Server Is Up!!")
        printing_lock.release()
        server_socket.listen()
    except OSError:
        print(f"The Port {PORT} Is Taken.")
        logging.debug(f"The Port {PORT} Is Taken.")
        exit()
    return server_socket


def accept_client(server_socket: EncryptedProtocolSocket) \
        -> tuple[EncryptedProtocolSocket, tuple[str, int]] | tuple[None, None]:
    global clients_sockets
    server_socket.settimeout(2)
    try:
        client_socket, client_addr = server_socket.accept()
    except (socket.error, ConnectionError):
        return None, None
    printing_lock.acquire()
    print("[Server]: New Connection From: '%s:%s'" % (client_addr[0], client_addr[1]))
    logging.info("[Server]: New Connection From: '%s:%s'" % (client_addr[0], client_addr[1]))
    clients_sockets.append(client_socket)
    printing_lock.release()
    return client_socket, client_socket.getpeername()


def write_to_file(file_path: str, mode: str, data: bytes | str):
    """
    :param file_path: the path to the file
    :param mode: the mode to open the file in
    :param data: the data to write
    """
    with open(file_path, mode) as f:
        f.write(data)


def read_from_file(file_path: str, mode: str) -> str | bytes:
    """
    :param file_path: the path to the file
    :param mode: the mode to open the file in
    """
    with open(file_path, mode) as f:
        data: str | bytes = f.read()
    return data


def block(path: str) -> bool:
    """ :return: True to signal the "lock" is acquired """
    """
        create a folder "folder_name" to block 
        another thread from touching a specific resource file of the user
        because we are reading the file and then writing back
        and if someone does it the same time with us something will
        be lost, so blocking like this allows to block only for 
        this specific user, which is what we need
    """
    while True:
        try:
            os.makedirs(path, exist_ok=False)
            break
        except OSError:
            time.sleep(0.0005)
    return True


def unblock(path: str) -> bool:
    """ :return: True to signal the "lock" isn't acquired """
    if not os.path.isdir(path):
        raise ValueError(f"The 'lock' is already unlocked. (path - '{path}')")
    shutil.rmtree(path)
    return False


def add_chat_id_to_user_chats(user_email: str, chat_id: str) -> bool:
    exists, username = get_username(user_email)
    if not exists:
        return False
    os.makedirs(f"{USERS_DATA}{user_email}\\", exist_ok=True)
    if not os.path.isfile(f"{USERS_DATA}{user_email}\\chats"):
        write_to_file(f"{USERS_DATA}{user_email}\\chats", "wb", b"")
    try:
        chats_list: set = pickle.loads(read_from_file(f"{USERS_DATA}{user_email}\\chats", "rb"))
    except EOFError:
        chats_list = set()
    chats_list.add(chat_id)
    write_to_file(f"{USERS_DATA}{user_email}\\chats", "wb", pickle.dumps(chats_list))
    return True


def remove_chat_id_from_user_chats(user_email: str, chat_id: str) -> bool:
    exists, username = get_username(user_email)
    if not exists:
        return False
    os.makedirs(f"{USERS_DATA}{user_email}\\", exist_ok=True)
    if not os.path.isfile(f"{USERS_DATA}{user_email}\\chats"):
        write_to_file(f"{USERS_DATA}{user_email}\\chats", "wb", b"")
    try:
        chats_list: set = pickle.loads(read_from_file(f"{USERS_DATA}{user_email}\\chats", "rb"))
    except EOFError:
        chats_list = set()
    if chat_id in chats_list:
        chats_list.remove(chat_id)
    write_to_file(f"{USERS_DATA}{user_email}\\chats", "wb", pickle.dumps(chats_list))
    return True


def is_user_in_chat(user_email: str, chat_id: str) -> bool:
    """
    :param user_email: the email of the user to check if he is in the chat
    :param chat_id: the id of the chat that will be checked
    :return: True if the user is in the chat else False
    """
    exists, username = get_username(user_email)
    if not exists:
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


def add_new_data_to(emails: list[str] | str, new_data_paths: list[str] | str):
    """
    :param emails: the emails of the users to add the new data to there new_data file
    :param new_data_paths: the paths to the new files / updated files
    """
    if isinstance(emails, str):
        emails: list[str] = [emails]
    if isinstance(new_data_paths, str):
        new_data_paths: list[str] = [new_data_paths]
    for email in set(emails):
        exists, username = get_username(email)
        if not exists:
            continue
        block(f"{USERS_DATA}{email}\\new data not free")
        try:
            os.makedirs(f"{USERS_DATA}{email}\\", exist_ok=True)
            if not os.path.isfile(f"{USERS_DATA}{email}\\new_data"):
                write_to_file(f"{USERS_DATA}{email}\\new_data", "wb", b"")
            try:
                new_data_list = pickle.loads(read_from_file(f"{USERS_DATA}{email}\\new_data", "rb"))
            except EOFError:
                new_data_list = []
            new_data_list.extend(new_data_paths)
            write_to_file(f"{USERS_DATA}{email}\\new_data", "wb", pickle.dumps(new_data_list))
        finally:
            unblock(f"{USERS_DATA}{email}\\new data not free")


def get_new_data_of(email: str) -> list[str]:
    exists, username = get_username(email)
    if not exists:
        pass
    block(f"{USERS_DATA}{email}\\new data not free")
    try:
        os.makedirs(f"{USERS_DATA}{email}\\", exist_ok=True)
        if not os.path.isfile(f"{USERS_DATA}{email}\\new_data"):
            write_to_file(f"{USERS_DATA}{email}\\new_data", "wb", b"")
        try:
            new_data_list = pickle.loads(read_from_file(f"{USERS_DATA}{email}\\new_data", "rb"))
        except EOFError:
            new_data_list = []
        # new data collected, now is []
        write_to_file(f"{USERS_DATA}{email}\\new_data", "wb", b"")
        return new_data_list
    finally:
        unblock(f"{USERS_DATA}{email}\\new data not free")


def get_one_on_one_chats_list_of(email: str) -> list[str]:
    exists, username = get_username(email)
    if not exists:
        pass
    with open(f"{USERS_DATA}{email}\\one_on_one_chats", "r") as f:
        data = f.read()
    if data == "":
        return []
    return data.split("\n")[:-1]


def known_to_each_other(emails: list[str]):
    """
    :param emails: the emails of the users that are known to each other
    """
    for email in emails:
        block(f"{USERS_DATA}{email}\\known_users_block")
        try:
            try:
                known_to_user: set = pickle.loads(read_from_file(f"{USERS_DATA}{email}\\known_users", "rb"))
            except EOFError:
                known_to_user = set()
            for email_2 in emails:
                if email == email_2:
                    continue
                known_to_user.add(email_2)
            write_to_file(f"{USERS_DATA}{email}\\known_users", "wb", pickle.dumps(known_to_user))
        finally:
            unblock(f"{USERS_DATA}{email}\\known_users_block")


def create_new_chat(user_created: str, with_user: str) -> tuple[bool, str]:
    """
    :param user_created: the email of the user that created the chat
    :param with_user: the email of the user that the chat is created with
    :return: (True, chat_id) if the chat was created else (False, "")
    """
    # check that the 2 users exist
    exists, user_created_username = get_username(user_created)
    exists2, with_user_username = get_username(with_user)
    if not exists:
        return False, ""
    if not exists2:
        return False, "User Doesn't Exist."
    user_created_one_on_one_chats = get_one_on_one_chats_list_of(user_created)
    if with_user in user_created_one_on_one_chats:
        return False, "Chat Already Exists."
    chat_id = "".join(random.choices(CHAT_ID_CHARS, k=20))
    while not chat_id_users_database.safe_set(chat_id, [user_created, with_user]):
        chat_id = "".join(random.choices(CHAT_ID_CHARS, k=20))
    try:
        os.makedirs(f"{USERS_DATA}{chat_id}\\data\\chat", exist_ok=False)
        os.makedirs(f"{USERS_DATA}{chat_id}\\data\\files", exist_ok=True)
    # if OSError is raised, that means that there is already a chat with this chat id
    # and there shouldn't be according to the chat_id_users_database
    except OSError:
        return False, ""
    # chat metadata
    write_to_file(f"{USERS_DATA}{chat_id}\\name", "w",
                  f"{user_created} - {with_user_username}\n{with_user} - {user_created_username}")
    write_to_file(f"{USERS_DATA}{chat_id}\\type", "w", "chat")
    write_to_file(f"{USERS_DATA}{chat_id}\\users", "w", f"{user_created}\n{with_user}")
    # add chat id to each user chats
    add_chat_id_to_user_chats(user_created, chat_id)
    add_chat_id_to_user_chats(with_user, chat_id)
    # add with_user to user_created one_on_one_chats file
    write_to_file(f"{USERS_DATA}{user_created}\\one_on_one_chats", "a", f"{with_user}\n")
    # add user_created to with_user one_on_one_chats file
    write_to_file(f"{USERS_DATA}{with_user}\\one_on_one_chats", "a", f"{user_created}\n")
    #
    known_to_each_other([with_user, user_created])
    return True, chat_id


def create_new_group(user_created: str, users: list[str], group_name: str) -> tuple[bool, str]:
    users.append(user_created)
    #
    for email in set(users):
        exists, username = get_username(email)
        if not exists:
            return False, ""
    chat_id = "".join(random.choices(CHAT_ID_CHARS, k=20))
    while not chat_id_users_database.safe_set(chat_id, users):
        chat_id = "".join(random.choices(CHAT_ID_CHARS, k=20))
    try:
        os.makedirs(f"{USERS_DATA}{chat_id}\\data\\chat", exist_ok=False)
        os.makedirs(f"{USERS_DATA}{chat_id}\\data\\files", exist_ok=True)
    # if OSError is raised, that means that there is already a chat with this chat id
    # and there shouldn't be according to the chat_id_users_database
    except OSError:
        return False, ""
    # chat metadata
    write_to_file(f"{USERS_DATA}{chat_id}\\name", "w", group_name)
    write_to_file(f"{USERS_DATA}{chat_id}\\type", "w", "group")
    write_to_file(f"{USERS_DATA}{chat_id}\\users", "w", "\n".join(set(users)))
    for email in users:
        add_chat_id_to_user_chats(email, chat_id)
    known_to_each_other(users)
    return True, chat_id


def add_user_to_group(from_user: str, add_user: str, group_id: str) -> bool:
    exists, username = get_username(add_user)
    exists2, username2 = get_username(from_user)
    if not exists or not exists2 or not is_user_in_chat(from_user, group_id):
        return False
    # update database
    chat_id_users_database.add(group_id, [add_user])
    # update file of users
    block(f"{USERS_DATA}{group_id}\\users_block")
    write_to_file(f"{USERS_DATA}{group_id}\\users", "a", f"\n{add_user}")
    unblock(f"{USERS_DATA}{group_id}\\users_block")
    #
    add_chat_id_to_user_chats(add_user, group_id)
    add_new_data_to(from_user, f"all of: {group_id}")
    return True


def remove_user_from_group(from_user: str, remove_user: str, group_id: str):
    exists, username = get_username(remove_user)
    exists2, username2 = get_username(from_user)
    if not exists or not exists2 or not is_user_in_chat(from_user, group_id) or \
            not is_user_in_chat(remove_user, group_id):
        return False
    # update database
    chat_id_users_database.remove(group_id, remove_user)
    # update file of users
    block(f"{USERS_DATA}{group_id}\\users_block")
    users = read_from_file(f"{USERS_DATA}{group_id}\\users", "r").split("\n")
    if remove_user in users:
        users.remove(remove_user)
    users = "\n".join(users)
    write_to_file(f"{USERS_DATA}{group_id}\\users", "w", users)
    unblock(f"{USERS_DATA}{group_id}\\users_block")
    #
    remove_chat_id_from_user_chats(remove_user, group_id)
    add_new_data_to(from_user, f"all of: {group_id}")
    send_msg(from_user, group_id, f"{from_user} removed {remove_user}", remove_msg=True)
    return True


def send_msg(from_user: str, chat_id: str, msg: str, file_msg: bool = False, remove_msg: bool = False) -> bool:
    """
    :param from_user: the email of the user that sent the msg
    :param chat_id: the id of the chat that the msg is being sent to
    :param msg: the msg
    :param file_msg: if a file was sent to a chat the send_file
                     function will call this function with file_msg=True
                     and the msg will be the file location
    :param remove_msg: a message that will say 'x removed y' and will be displayed different
    """
    # 3 types: regular msg / file msg (if it's a file) / remove msg (if someone removed someone)
    msg_type = "msg" if not file_msg and not remove_msg else "file" if file_msg else "remove" if remove_msg else None
    if msg_type is None:
        return False
    lock = block(f"{USERS_DATA}{chat_id}\\data\\not free")
    try:
        users_in_chat = chat_id_users_database.get(chat_id)
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
            data = {(latest + 1) * 800: [from_user, msg, msg_type, [], False, [], datetime.datetime.now()]}
            write_to_file(f"{USERS_DATA}{chat_id}\\data\\chat\\{latest + 1}", "wb", pickle.dumps(data))
        else:
            #        index:              [from_user, msg, msg_type, deleted_for, delete_for_all, seen by, time]
            data[max(data.keys()) + 1] = [from_user, msg, msg_type, [], False, [], datetime.datetime.now()]
            write_to_file(f"{USERS_DATA}{chat_id}\\data\\chat\\{latest}", "wb", pickle.dumps(data))
        # when finished remove the folder
        lock = unblock(f"{USERS_DATA}{chat_id}\\data\\not free")
        # add the new file / updated file to the new data of all the users in the chat
        latest = latest + 1 if len(data) >= 800 or first_chat else latest
        add_new_data_to(users_in_chat, f"{USERS_DATA}{chat_id}\\data\\chat\\{latest}")
        return True
    except Exception:
        return False
    finally:
        if lock:
            unblock(f"{USERS_DATA}{chat_id}\\data\\not free")


def send_file(from_user: str, chat_id: str, file_data: bytes, file_name: str) -> bool:
    """
    :param from_user: the email of the user that sent the file
    :param chat_id: the id of the chat that the file is being sent to
    :param file_data: the data of the file
    :param file_name: the name of the file
    """
    try:
        users_in_chat = chat_id_users_database.get(chat_id)
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
        if send_msg(from_user, chat_id, new_file_name, file_msg=True):
            add_new_data_to(users_in_chat, location + new_file_name)
            return True
        else:
            os.remove(location + new_file_name)
            return False
    except Exception:
        return False


def delete_msg_for_me(from_user: str, chat_id: str, index_of_msg: int):
    users_in_chat = chat_id_users_database.get(chat_id)
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
    except Exception:
        return False
    finally:
        if lock:
            unblock(f"{USERS_DATA}{chat_id}\\data\\not free")


def delete_msg_for_everyone(from_user: str, chat_id: str, index_of_msg: int):
    users_in_chat = chat_id_users_database.get(chat_id)
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
        else:
            unblock(f"{USERS_DATA}{chat_id}\\data\\not free")
            return False
        unblock(f"{USERS_DATA}{chat_id}\\data\\not free")
        add_new_data_to(from_user, f"{USERS_DATA}{chat_id}\\data\\chat\\{file_number}")
        return True
    except Exception:
        return False
    finally:
        if lock:
            unblock(f"{USERS_DATA}{chat_id}\\data\\not free")


def send_mail(to: str, subject: str, body: str, html: str = ""):
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


def signup(username: str, email: str, password: str, client_sock: EncryptedProtocolSocket) -> tuple[bool, str]:
    """
    :param username: the username
    :param email: the email of the user
    :param password: the md5 hash of the password
    :param client_sock: the socket of the client
    """
    # check that the email isn't registered
    exists, _ = get_username(email)
    if exists:
        return False, ""
    # create confirmation code
    confirmation_code = random.choices(range(0, 10), k=6)
    confirmation_code = "".join(map(str, confirmation_code))
    # send confirmation code to the email
    send_mail(email, "Confirmation Code",
              f"Your code is: {confirmation_code}",
              f"<div style='color: rgb(18, 151, 228); font-size: xx-large;'>Your code is: {confirmation_code}</div>")
    printing_lock.acquire()
    print(f"A mail was sent to '{email}' with the confirmation code '{confirmation_code}'")
    printing_lock.release()
    # send client a msg that says that we are waiting for a confirmation code
    client_sock.send_message(f"{'confirmation_code'.ljust(30)}".encode())
    # receive the response from the client and set a timeout of 5 minutes
    msg = client_sock.receive_message(timeout=60*5)
    # if response timed out
    if msg == b"":
        return False, "Request timeout."
    msg = msg.decode()
    # check the response
    if msg[:30].strip() != "confirmation_code" or msg[30:] != confirmation_code:
        logging.info(f"signup attempt (for '{email}') failed - "
                     f"got wrong confirmation code from user trying to signup as '{username}'")
        return False, "Confirmation code is incorrect."
    # user_password_database -> {"email - username": password, "another email - another username": password, ...}
    email_user = user_password_database.keys()
    # if username doesn't exist
    if f"{email} - {username}" not in email_user and len(username) <= 40:
        # add username and password to the user_password_database
        user_password_database[f"{email} - {username}"] = hashlib.md5(password.encode()).hexdigest().lower()
        logging.info(f"signup attempt successful - email: '{email}', username: '{username}'")
        # create user directory and files
        os.makedirs(f"{USERS_DATA}{email}", exist_ok=True)
        write_to_file(f"{USERS_DATA}{email}\\chats", "wb", b"")
        write_to_file(f"{USERS_DATA}{email}\\new_data", "wb", b"")
        write_to_file(f"{USERS_DATA}{email}\\known_users", "wb", b"")
        write_to_file(f"{USERS_DATA}{email}\\one_on_one_chats", "wb", b"")
        return True, "Signed up successfully."
    return False, "Email already registered."


def reset_password(email: str, client_sock: EncryptedProtocolSocket) -> tuple[bool, str]:
    """
    :param email: the email of the user that wants to reset their password
    :param client_sock: the socket of the client
    """
    # check that the email is registered
    exists, username = get_username(email)
    if not exists:
        return False, ""
    # create confirmation code
    confirmation_code = random.choices(range(0, 10), k=6)
    confirmation_code = "".join(map(str, confirmation_code))
    # send confirmation code to the email
    send_mail(email, "Confirmation Code",
              f"Your code is: {confirmation_code}",
              f"<div style='color: rgb(18, 151, 228); font-size: xx-large;'>Your code is: {confirmation_code}</div>")
    printing_lock.acquire()
    print(f"A mail was sent to '{email}' with the confirmation code '{confirmation_code}'")
    printing_lock.release()
    # send client a msg that says that we are waiting for a confirmation code
    client_sock.send_message(f"{'confirmation_code'.ljust(30)}".encode())
    # receive the response from the client and set a timeout of 5 minutes
    msg = client_sock.receive_message(timeout=60 * 5)
    # if response timed out
    if msg == b"":
        return False, "Request timeout."
    msg = msg.decode()
    # check the response
    if msg[:30].strip() != "confirmation_code" or msg[30:] != confirmation_code:
        logging.info(f"reset password attempt (for '{email}') failed - got wrong confirmation code from user")
        return False, "Confirmation code is incorrect."
    # send client a msg that says that we are waiting for a new password
    client_sock.send_message(f"{'new_password'.ljust(30)}".encode())
    # receive the response from the client and set a timeout of 5 minutes
    msg = client_sock.receive_message(timeout=60 * 5)
    # if response timed out
    if msg == b"":
        return False, "Request timeout."
    msg = msg.decode()
    # validate the response
    if msg[:30].strip() != "new_password":
        return False, ""
    # extract password
    password = msg[30:]
    # set new password
    user_password_database[f"{email} - {username}"] = password
    logging.info(f"reset password attempt successful - email: '{email}', username: '{username}'.")
    return True, "Password changed successfully."


def get_user_password(email: str) -> tuple[bool, str]:
    users_email = [" - ".join(user_email.split(" - ")[:-1]) for user_email in user_password_database.keys()]
    if email in users_email:
        return True, user_password_database[f"{email} - {get_username(email)[1]}"]
    return False, ""


def get_username(email: str) -> tuple[bool, str]:
    # user_password_database -> {"email - username": password, "another email - another username": password, ...}
    # email_user -> {email: username, another_email: another_username, ...}
    email_user: dict[str: str] = {
        e: u for e, u in map(
            lambda x: [" - ".join(x.split(" - ")[:-1]), x.split(" - ")[-1]], user_password_database.keys()
        )
    }
    if email in email_user:
        return True, email_user[email]
    return False, ""


def login(email: str, password: str) -> bool:
    """
    :param email: the email of the user
    :param password: the md5 hash of the password
    """
    user_exists, user_password_hash = get_user_password(email)
    if not user_exists or user_password_hash != hashlib.md5(password.encode()).hexdigest().lower():
        return False
    user_online_status_database[email] = ["Online", None]
    return True


def sync(email: str, sync_all: bool = False) -> bool:
    block(f"{USERS_DATA}{email}\\sync")
    new_data = get_new_data_of(email)
    if sync_all:
        pass
    # TODO finish this func
    # make a dictionary -> {file_path: file_data}
    # pickle the dictionary & send to client
    with open(f"{USERS_DATA}{email}\\new_data.txt", "w") as f:
        f.write("")
    unblock(f"{USERS_DATA}{email}\\sync")


def call_user(from_email: str, to_email: str):
    """
        !!! open a thread to call this func !!!

        check if to_email is connected
        if he is, send a msg that says that from_email
        is calling him, if to_email answers the call
        send from_email a msg that says that from_email answered
        the call, and from_email will start a server sock at
        port number x, and then this server will send to_email
        the ip and port of from_email server sock and the call will start
    """
    pass


def call_group(from_email: str, to_emails: list[str]):
    """
        !!! open a thread to call this func !!!

        check if at least one of to_emails is connected
        if someone is, send a msg that says that from_email
        is calling them, if someone answers the call
        send from_email a msg that says that someone answered
        the call, and from_email will start a server sock at
        port number x, and then this server will send the ones that
        answered the call the ip and port of from_email server
        sock and the call will start
    """
    pass


def login_or_signup_response(mode: str, status: str, reason: str) -> bytes:
    """
    :param mode: login or signup
    :param status: ok or not ok
    :param reason: the reason
    """
    return f"{mode.ljust(30)}{status.ljust(6)}{reason}".encode()


def handle_client(client_socket: EncryptedProtocolSocket, client_ip_port: tuple[str, str]):
    global online_users
    logged_in = False
    signed_up = False
    stop = False
    email = ""
    try:
        # let client login / signup and login
        while not logged_in:
            # receive 1 msg
            client_socket.settimeout(5)
            try:
                msg = client_socket.receive_message()
            except socket.timeout:
                client_socket.send_message(login_or_signup_response("login", "not ok", "Request Timed Out."))
                break
            client_socket.settimeout(None)
            msg = msg.decode()
            cmd = msg[:30].strip()
            # check if the msg is signup msg or login, else throw the msg
            # because the client hasn't logged in yet
            # if client sent login request
            if cmd == "login":
                len_email = int(msg[30:40].strip())
                email = msg[40:40 + len_email]
                user_exists, password = get_user_password(email)
                if not user_exists:
                    client_socket.send_message(
                        login_or_signup_response("login", "not ok", "email or password is incorrect.")
                    )
                    stop = True
                    break
                if msg[40 + len_email:] != password:
                    client_socket.send_message(
                        login_or_signup_response("login", "not ok", "email or password is incorrect.")
                    )
                    stop = True
                    break
                logged_in = True
                user_exists, username = get_username(email)
                client_socket.send_message(login_or_signup_response("login", "ok", username))
                del msg, cmd, len_email, user_exists, password
            elif cmd == "signup" and not signed_up:
                len_username = int(msg[:2].strip())
                username = msg[2:2 + len_username]
                len_email = int(msg[2 + len_username:12 + len_username].strip())
                email = msg[12 + len_username:12 + len_username + len_email]
                password = msg[12 + len_username + len_email:]
                ok, reason = signup(username, email, password, client_socket)
                if not ok:
                    client_socket.send_message(login_or_signup_response("signup", "not ok", reason))
                    stop = True
                    break
                client_socket.send_message(login_or_signup_response("signup", "ok", ""))
                signed_up = True
                del msg, len_username, len_email, password, reason, ok
            elif cmd == "signup" and signed_up:
                stop = True
                break
            else:
                stop = True
                break
        if not stop and logged_in:
            client_socket.settimeout(None)
            user_exists, username = get_username(email)
            user_exists2, password = get_user_password(email)
            if not user_exists & user_exists2:
                raise Exception(f"[Server]: The email '{email}' doesn't exists in the database.")
            del user_exists, user_exists2
            printing_lock.acquire()
            print(f"[Server]: '%s:%s' logged in as '{email}-{username}'." % client_ip_port)
            logging.info(f"[Server]: '%s:%s' logged in as '{email}-{username}'." % client_ip_port)
            printing_lock.release()
            #
            # handle client's requests until client disconnects
            request = client_socket.receive_message()
            request = request.decode()
            while request != "":
                request = client_socket.receive_message()
                request = request.decode()
                # TODO call the right func to handle the client's request
                cmd = request[:30].strip()
                if cmd == "sync new":
                    sync(username)
                elif cmd == "sync all":
                    sync(username, sync_all=True)
                elif cmd == "msg":
                    pass
                elif cmd == "delete for everyone":
                    pass
                elif cmd == "file":
                    pass
                elif cmd == "delete for me":
                    pass
                elif cmd == "add user":
                    pass
                elif cmd == "remove user":
                    pass
                elif cmd == "new chat":
                    pass
                elif cmd == "new group":
                    pass
                elif cmd == "login":
                    pass
                elif cmd == "signup":
                    pass
                else:
                    print(f"[Server]: '%s:%s' Logged In As '{email}-{username}' - "
                          f"sent unknown cmd {cmd}" % client_ip_port)
                    logging.warning(f"[Server]: '%s:%s' Logged In As '{email}-{username}' - "
                                    f"sent unknown cmd {cmd}" % client_ip_port)
            del request
    except (socket.error, TypeError, OSError, ConnectionError, Exception) as err:
        printing_lock.acquire()
        if "username" in locals():
            print(f"[Server]: error while handling '%s:%s' ('{username}'): {str(err)}" % client_ip_port)
            logging.warning(f"[Server]: error while handling '%s:%s' ('{username}'): {str(err)}" % client_ip_port)
        else:
            print(f"[Server]: error while handling '%s:%s': {str(err)}" % client_ip_port)
            logging.warning(f"[Server]: error while handling '%s:%s': {str(err)}" % client_ip_port)
        printing_lock.release()
    finally:
        try:
            client_socket.close()
        except Exception:
            pass
        printing_lock.acquire()
        if "username" in locals():
            print(f"[Server]: Client '%s:%s' ('{username}') disconnected." % client_ip_port)
            logging.info(f"[Server]: Client '%s:%s' ('{username}') disconnected." % client_ip_port)
        else:
            print(f"[Server]: Client '%s:%s' disconnected." % client_ip_port)
            logging.info(f"[Server]: Client '%s:%s' disconnected." % client_ip_port)
        printing_lock.release()
        if get_username(email)[0]:  # if 'email' is registered as a user
            #                                                     last seen
            user_online_status_database[email] = ["Offline", datetime.datetime.now()]


def main():
    # logging configuration
    logging.basicConfig(format=LOG_FORMAT, filename=LOG_FILE, level=LOG_LEVEL)
    #
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
