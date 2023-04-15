import os
import traceback

import eel
import time
import json
import random
import pickle
import datetime
import threading


from communication import Communication as Com
from protocol_socket import EncryptedProtocolSocket


# Constants

# Globals
first_sync_done: bool = False
email: None | str = None
username: None | str = None
password: None | str = None
server_ip_port: None | tuple[str, int] = None
communication: None | Com = None
sock: None | EncryptedProtocolSocket = None
open_chat_files_lock = threading.Lock()
open_chat_files: list[str] = []
chat_folder: str = ""


@eel.expose
def get_email() -> str:
    return email


@eel.expose
def get_username() -> str:
    return username


@eel.expose
def get_chat_msgs(chat_id: str) -> str:
    global chat_folder, open_chat_files
    latest_file = f"webroot\\{email}\\{chat_id}\\data\\chat\\"
    latest_file = latest_file + max(os.listdir(latest_file))
    with open(latest_file, "rb") as f:
        data = json.dumps(pickle.loads(f.read()))
    open_chat_files_lock.acquire()
    open_chat_files = [latest_file]
    chat_folder = os.path.dirname(latest_file)
    open_chat_files_lock.release()
    return data


@eel.expose
def get_all_chat_ids() -> str:
    chat_ids = [chat_id for chat_id in os.listdir(f"webroot\\{email}") if os.path.isdir(f"webroot\\{email}\\{chat_id}")]
    chat_ids.remove("profile_pictures")
    #       [chat_id, [chat_name, last_message, time, chat_type (group or the email of the user the chat is with)]
    chat_id_last_msg_and_time: dict[str, list[str, str, str, str]] = {}
    for chat_id in chat_ids:
        with open(f"webroot\\{email}\\{chat_id}\\name", "rb") as f:
            chat_name = pickle.loads(f.read())
        chat_type = "group" if len(chat_name) == 1 else "1 on 1"
        chat_name = chat_name[0] if len(chat_name) == 1 else chat_name[0] if chat_name[0] != username else chat_name[1]
        with open(f"webroot\\{email}\\{chat_id}\\users", "rb") as f:
            users = pickle.loads(f.read())
        latest_chat_msgs_file_name = max(os.listdir(f"webroot\\{email}\\{chat_id}\\data\\chat"))
        with open(f"webroot\\{email}\\{chat_id}\\data\\chat\\{latest_chat_msgs_file_name}", "rb") as f:
            last_chat_msgs = pickle.loads(f.read())
        last_msg = last_chat_msgs[max(last_chat_msgs.keys())]
        msg = f"{last_msg[0].split('@')[0]}: {last_msg[1]}"
        msg = msg if len(msg) <= 25 else msg[:25] + "..."
        msg_time = last_msg[-1] if isinstance(last_msg[-1], str) else last_msg[-1].strftime("%m/%d/%Y %H:%M")
        chat_id_last_msg_and_time[chat_id] = [chat_name, msg, msg_time, chat_type, users]
    return json.dumps(chat_id_last_msg_and_time)


@eel.expose
def get_more_msgs() -> str:
    open_chat_files_lock.acquire()
    if chat_folder + "\\0" not in open_chat_files:
        with open(chat_folder + f"\\{int(min(open_chat_files)) - 1}") as f:
            data = json.dumps(pickle.loads(f.read()))
    else:
        data = json.dumps({})
    open_chat_files_lock.release()
    return data


def update(com: Com, sync_sock: EncryptedProtocolSocket, first_time_sync_all: bool) -> None:
    global first_sync_done
    sync_new = "new"
    sync_all = "all"
    while True:
        new_data, modified_files, deleted_files = com.sync(sync_sock, sync_all if first_time_sync_all else sync_new)
        try:
            open_chat_id = eel.get_open_chat_id()
        except AttributeError:  # as e:  # Gui haven't loaded up yet
            # print(*traceback.format_exception(e), sep="")
            open_chat_id = None
        if new_data and any(open_chat_id == file_path.split("\\")[0] for file_path in modified_files + deleted_files):
            for file in modified_files:
                with open(file, "rb") as f:
                    data = json.dumps(pickle.loads(f.read()))
                eel.update(open_chat_id, data)
        time.sleep(0.5)
        if not first_sync_done:
            first_sync_done = True
            first_time_sync_all = False


@eel.expose
def get_user_last_seen(user_email: str) -> str:
    with open(f"webroot\\{email}\\users_status", "rb") as f:
        users_status: dict = pickle.loads(f.read())
    return users_status.get(user_email, "")


@eel.expose
def send_message(message) -> bool:
    return communication.send_message(eel.get_open_chat_id(), message, sock)


@eel.expose
def send_file() -> None:
    communication.upload_file_(eel.get_open_chat_id())


@eel.expose
def new_chat(other_email: str) -> bool:
    return communication.new_chat(other_email, sock)


@eel.expose
def new_group(other_emails: list[str], group_name: str) -> bool:
    return communication.new_group(other_emails, group_name, sock)[0]


@eel.expose
def add_user_to_group(other_email: str) -> bool:
    return communication.add_user_to_group(other_email, eel.get_open_chat_id(), sock)


@eel.expose
def remove_user_from_group(other_email: str) -> bool:
    return communication.remove_user_from_group(other_email, eel.get_open_chat_id(), sock)


@eel.expose
def make_call() -> bool:
    return communication.make_call(eel.get_open_chat_id())


@eel.expose
def upload_profile_picture():
    # TODO: askfile something
    # communication.upload_profile_picture()
    pass


# TODO: make a wrapper to all the rest of the function in Communication


def start(user_email: str, user_username: str, user_password: str,
          server_ip_port_: tuple[str, int], first_time_sync_all: bool) -> None:
    global email, username, password, communication, server_ip_port, sock
    email = user_email
    username = user_username
    password = user_password
    server_ip_port = server_ip_port_
    communication = Com(email, password, server_ip_port)
    status, sock, reason = communication.login()  # verbose=False)
    sync_sock = EncryptedProtocolSocket()
    status2, sync_sock, reason2 = communication.login(verbose=False, sock=sync_sock)
    if status and status2:
        t = threading.Thread(target=update, args=(communication, sync_sock, first_time_sync_all,), daemon=True)
        t.start()
        while not first_sync_done:
            time.sleep(0.1)
        eel.init("webroot")
        eel.start("index.html", port=8080)
    else:
        raise ConnectionError("Error Logging In.")

    # # ---------------------------------------------------------------
    # d = {}
    # for i in range(4, 804):
    #     from_ = "omerdagry@gmail.com" if i % 2 == 0 else random.choice(["dor", "yuval", "ofri", "yoav", "liav"])
    #     d[i] = [from_, str(i), "msg", [], False, [], datetime.datetime.now().strftime("%m/%d/%Y")]
    # with open("check", "wb") as f:
    #     f.write(pickle.dumps(d))


if __name__ == '__main__':
    # start("omerdagry@gmail.com", "Omer Dagry", "", ("127.0.0.1", 8820), True)
    eel.init("webroot")
    eel.start("index.html", port=8080)
