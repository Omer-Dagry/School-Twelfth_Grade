"""
###############################################
Author: Omer Dagry
Mail: omerdagry@gmail.com
Date: 06/01/2023 (dd/mm/yyyy)
###############################################
"""
import os
import ssl
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
# Others
CHAT_ID_CHARS = [letter for letter in string.ascii_uppercase + string.ascii_lowercase + string.digits]
random.shuffle(CHAT_ID_CHARS)
SERVER_EMAIL = "project.twelfth.grade@gmail.com"
SERVER_EMAIL_APP_PASSWORD = "hbqbubnlppqxmupy"
SERVER_DATA = "Data\\Server_Data\\"
USERS_DATA = "Data\\Users_Data\\"
IP = "0.0.0.0"
PORT = 8820
SERVER_IP_PORT = (IP, PORT)

# Globals
# File DBs
# email_password_file_database -> {email: password, another email: password, ...}
email_password_file_database = FileDatabase(f"{SERVER_DATA}email_password", ignore_existing=True)
# email_user_file_database -> {email: username, another email: another username, ...}
email_user_file_database = FileDatabase(f"{SERVER_DATA}email_username", ignore_existing=True)
# chat_id_users_database -> {chat_id: [email, another_email], another_chat_id: [email, another_email], ...}
chat_id_users_file_database = FileDatabase(f"{SERVER_DATA}chat_id_users", ignore_existing=True)
# user_online_status_database -> {email: ["Online", None], email: ["Offline" / last_seen - datetime.datetime], ...}
user_online_status_file_database = FileDatabase(f"{SERVER_DATA}user_online_status", ignore_existing=True)
# Sync DBs
email_password_database = SyncDatabase(email_password_file_database, False, max_reads_together=1000)
email_user_database = SyncDatabase(email_user_file_database, False, max_reads_together=1000)
chat_id_users_database = SyncDatabase(chat_id_users_file_database, False, max_reads_together=1000)
user_online_status_database = SyncDatabase(user_online_status_file_database, False, max_reads_together=1000)
# Others
clients_sockets = []
printing_lock = threading.Lock()

# Create All Needed Directories
os.makedirs(f"{SERVER_DATA}", exist_ok=True)
os.makedirs(f"{USERS_DATA}", exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)


def start_server() -> EncryptedProtocolSocket:
    server_socket = EncryptedProtocolSocket(cert_file=os.path.abspath("private_key_and_crt\\certificate.crt"),
                                            key_file=os.path.abspath("private_key_and_crt\\privateKey.key"),
                                            server_side=True)
    try:
        server_socket.bind(SERVER_IP_PORT)
        printing_lock.acquire()
        print("Server Is Up!!")
        logging.info("Server Is Up!!")
        printing_lock.release()
        server_socket.listen()
    except OSError:
        logging.debug(f"The Port {PORT} Is Taken.")
        print(f"The Port {PORT} Is Taken.")
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
    clients_sockets.append(client_socket)
    logging.info("[Server]: New Connection From: '%s:%s'" % (client_addr[0], client_addr[1]))
    printing_lock.acquire()
    print("[Server]: New Connection From: '%s:%s'" % (client_addr[0], client_addr[1]))
    printing_lock.release()
    return client_socket, client_socket.getpeername()


def write_to_file(file_path: str, mode: str, data: bytes | str) -> None:
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
    if user_email not in email_password_database:
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
    if user_email not in email_password_database:
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


def add_new_data_to(emails: list[str] | str, new_data_paths: list[str] | str) -> None:
    """
    :param emails: the emails of the users to add the new data to there new_data file
    :param new_data_paths: the paths to the new files / updated files
    """
    if isinstance(emails, str):
        emails: list[str] = [emails]
    if isinstance(new_data_paths, str):
        new_data_paths: list[str] = [new_data_paths]
    for email in set(emails):
        if email not in email_password_database:
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
    if email not in email_password_database:
        return []
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
    if email not in email_password_database:
        return []
    with open(f"{USERS_DATA}{email}\\one_on_one_chats", "r") as f:
        data = f.read()
    if data == "":
        return []
    return data.split("\n")[:-1]


def known_to_each_other(emails: list[str]) -> None:
    """ mark emails as known to each other

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
        if email not in email_user_database:
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
    if from_user not in email_user_database or add_user not in email_user_database or \
            not is_user_in_chat(from_user, group_id):
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


def remove_user_from_group(from_user: str, remove_user: str, group_id: str) -> bool:
    if from_user not in email_user_database or remove_user not in email_user_database or \
            not is_user_in_chat(from_user, group_id):
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
    except Exception as e:
        logging.debug(f"exception: {traceback.format_exception(e)} (user: '{from_user}', func: 'send_msg')")
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
    except Exception as e:
        logging.debug(f"exception: {traceback.format_exception(e)} (user: '{from_user}', func: 'send_file')")
        return False


def delete_msg_for_me(from_user: str, chat_id: str, index_of_msg: int) -> bool:
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
    except Exception as e:
        logging.debug(f"exception: {traceback.format_exception(e)} (user: '{from_user}', func: 'delete_msg_for_me')")
        return False
    finally:
        if lock:
            unblock(f"{USERS_DATA}{chat_id}\\data\\not free")


def delete_msg_for_everyone(from_user: str, chat_id: str, index_of_msg: int) -> bool:
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
    except Exception as e:
        logging.debug(f"exception: {traceback.format_exception(e)} "
                      f"(user: '{from_user}', func: 'delete_msg_for_everyone')")
        return False
    finally:
        if lock:
            unblock(f"{USERS_DATA}{chat_id}\\data\\not free")


def send_mail(to: str, subject: str, body: str, html: str = "") -> None:
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
    if email in email_user_database:
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
    # if username doesn't exist
    if email not in email_user_database and len(username) <= 40:
        # add username and password to the email_password_database & email_user_database
        email_password_database[email] = hashlib.md5(password.encode()).hexdigest().lower()
        email_user_database[email] = username
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
    if email not in email_password_database:
        return False, ""
    username = email_user_database[email]
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
    email_password_database[email] = password
    logging.info(f"reset password attempt successful - email: '{email}', username: '{username}'.")
    return True, "Password changed successfully."


def login(email: str, password: str) -> bool:
    """
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
    return True


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
    :param status: 'ok' or 'not ok'
    :param reason: the reason
    """
    return f"{mode.ljust(30)}{status.lower().ljust(6)}{reason}".encode()


def request_response(cmd: str, status: str, reason: str) -> bytes:
    """
    :param cmd: the requested command
    :param status: 'ok' or 'not ok'
    :param reason: the reason
    """
    return f"{cmd.ljust(30)}{status.lower().ljust(6)}{reason}".encode()


def handle_client(client_socket: EncryptedProtocolSocket, client_ip_port: tuple[str, str]) -> None:
    logged_in = False
    signed_up = False
    stop = False
    email = None
    username = None
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
                password = msg[40 + len_email:]
                if not login(email, password):
                    client_socket.send_message(
                        login_or_signup_response("login", "not ok", "email or password is incorrect.")
                    )
                    stop = True
                    break
                logged_in = True
                username = email_user_database[email]
                client_socket.send_message(login_or_signup_response("login", "ok", username))
                del msg, cmd, len_email, password
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
            threading.current_thread().name = f"{email} (client)"  # set thread name
            client_socket.settimeout(None)
            if email not in email_user_database:
                logging.debug(f"[Server]: The email '{email}' doesn't exists in the database.")
                raise ValueError(f"[Server]: The email '{email}' doesn't exists in the database.")
            username = email_user_database[email]
            password = email_password_database[email]
            printing_lock.acquire()
            print(f"[Server]: '%s:%s' logged in as '{email}-{username}'." % client_ip_port)
            logging.info(f"[Server]: '%s:%s' logged in as '{email}-{username}'." % client_ip_port)
            printing_lock.release()
            #
            # handle client's requests until client disconnects
            while True:
                request: bytes
                request = client_socket.receive_message()
                if request == b"":
                    break
                cmd = request[:30].decode().strip()
                request = request if cmd == "file" else request.decode()  # decode the request only if it's not a file
                # TODO call the right func to handle the client's request
                response = None
                if cmd == "sync new":
                    request: str
                    # sync(username)
                    # also remember user_online_status_database (last seen and online)
                    pass
                elif cmd == "sync all":
                    request: str
                    # sync(username, sync_all=True)
                    # also remember user_online_status_database (last seen and online)
                    pass
                elif cmd == "msg":
                    request: str
                    len_chat_id = int(request[30:45].strip())  # currently 20
                    chat_id = request[45:len_chat_id + 45]
                    msg = request[len_chat_id + 45:]
                    ok = send_msg(username, chat_id, msg)
                    #
                    response = request_response(cmd, "ok" if ok else "not ok", "")
                elif cmd == "delete for everyone":
                    request: str
                    pass
                elif cmd == "file":
                    request: bytes
                    pass
                elif cmd == "delete for me":
                    request: str
                    pass
                elif cmd == "add user":
                    request: str
                    pass
                elif cmd == "remove user":
                    request: str
                    pass
                elif cmd == "new chat":
                    request: str
                    pass
                elif cmd == "new group":
                    request: str
                    pass
                elif cmd == "login":
                    request: str
                    pass
                elif cmd == "signup":
                    request: str
                    pass
                else:
                    print(f"[Server]: '%s:%s' Logged In As '{email}-{username}' - "
                          f"sent unknown cmd {cmd}" % client_ip_port)
                    logging.warning(f"[Server]: '%s:%s' Logged In As '{email}-{username}' - "
                                    f"sent unknown cmd {cmd}" % client_ip_port)
                    continue
                # send response
                if response is not None:
                    client_socket.send_message(response)
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
        client_socket.close()
        printing_lock.acquire()
        print(f"[Server]: Client '%s:%s' disconnected." % client_ip_port)
        logging.info(f"[Server]: Client '%s:%s' disconnected." % client_ip_port)
        printing_lock.release()
        if email in email_user_database:
            if user_online_status_database[email][1] == 1:
                #                                                     last seen
                user_online_status_database[email] = ["Offline", datetime.datetime.now()]
            else:
                user_online_status_database[email][1] -= 1  # reduce online count by 1 (each connection is 1)


def main():
    # logging configuration
    logging.basicConfig(format=LOG_FORMAT, filename=LOG_FILE, level=LOG_LEVEL)
    #
    server_socket = start_server()
    clients_threads: list[threading.Thread] = []
    clients_threads_socket: dict[threading.Thread, EncryptedProtocolSocket] = {}
    while True:
        time.sleep(0.5)
        client_socket, client_ip_port = accept_client(server_socket)
        if client_socket is not None:
            client_socket: EncryptedProtocolSocket
            client_ip_port: tuple[str, int]
            client_thread = threading.Thread(target=handle_client,
                                             args=(client_socket, client_ip_port),
                                             daemon=True, name="%s:%s" % client_ip_port)
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
