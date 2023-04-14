import os
import eel
import time
import json
import random
import pickle
import datetime
import threading


# Constants

# Globals
email: None | str = "omerdagry@gmail.com"
username: None | str = "Omer Dagry"
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
    # with open("check", "rb") as f:
    #     data = json.dumps(pickle.loads(f.read()))
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
    # return json.dumps({"5467": ["Omer Dagry", "hi", "04/13/2023 8:34", "group"]})


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
    # return json.dumps(
    #     {1: ["omerdagry@gmail.com", "1", "msg", [], False, [], datetime.datetime.now().strftime("%m/%d/%Y")],
    #      2: ["omerdagry@gmail.com", "2", "msg", [], False, [], datetime.datetime.now().strftime("%m/%d/%Y")],
    #      3: ["dor", "3", "msg", [], False, [], datetime.datetime.now().strftime("%m/%d/%Y")]})


def sync() -> tuple[list[str], list[str]]:
    return [], []


def update():
    time.sleep(5)  # wait for browser to start
    while True:
        modified_files, deleted_files = sync()
        open_chat_id = eel.get_open_chat_id()
        if any(open_chat_id == file_path.split("\\")[0] for file_path in modified_files + deleted_files) or True:
            for file in modified_files:
                with open(file, "rb") as f:
                    data = json.dumps(pickle.loads(f.read()))
                eel.update(open_chat_id, data)


@eel.expose
def get_user_last_seen(user_email: str):
    with open(f"webroot\\{email}\\users_status", "rb") as f:
        users_status: dict = pickle.loads(f.read())
    return users_status.get(user_email, "")


def main():
    eel.init("webroot")
    # TODO: uncomment the following lines
    # t = threading.Thread(target=update)
    # t.start()
    eel.start("index.html", port=8080)

    # # ---------------------------------------------------------------
    # d = {}
    # for i in range(4, 804):
    #     from_ = "omerdagry@gmail.com" if i % 2 == 0 else random.choice(["dor", "yuval", "ofri", "yoav", "liav"])
    #     d[i] = [from_, str(i), "msg", [], False, [], datetime.datetime.now().strftime("%m/%d/%Y")]
    # with open("check", "wb") as f:
    #     f.write(pickle.dumps(d))


if __name__ == '__main__':
    main()
