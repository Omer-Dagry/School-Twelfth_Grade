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
open_chat_files_lock = threading.Lock()
open_chat_files: list[str] = []
chat_folder: str = ""


@eel.expose
def get_username():
    return "omerdagry@gmail.com"


@eel.expose
def get_chat_msgs(chat_id: str):
    global chat_folder
    # latest_file = f"{email}\\{chat_id}\\data\\chat"
    # latest_file = latest_file + max(os.listdir(latest_file))
    # with open(latest_file, "rb") as f:
    #     data = json.dumps(pickle.loads(f.read()))
    # open_chat_files_lock.acquire()
    # open_chat_files = [latest_file]
    # chat_folder = os.path.dirname(latest_file)
    # open_chat_files_lock.release()
    with open("check", "rb") as f:
        data = json.dumps(pickle.loads(f.read()))
    return data


@eel.expose
def get_all_chat_ids():
    # chat_ids = os.listdir(email)
    # #       [chat_id, [chat_name, last_message, time, chat_type (group or the email of the user the chat is with)]
    chat_id_last_msg_and_time: dict[str, list[str, str, str, str]] = {}
    # for chat_id in chat_ids:
    #     with open(f"{email}\\{chat_id}\\name", "rb") as f:
    #         chat_name = pickle.loads(f.read())
    #     chat_type = "group" if len(chat_id) == 1 else "1 on 1"
    #     chat_name = chat_name[0] if len(chat_id) == 1 else chat_name[0] if chat_name[0] != email else chat_name[1]
    #     latest_chat_msgs_file_name = max(os.listdir(f"{email}\\{chat_id}\\data\\chat"))
    #     with open(latest_chat_msgs_file_name, "rb") as f:
    #         last_chat_msgs = pickle.loads(f.read())
    #     last_msg = last_chat_msgs[max(last_chat_msgs.keys())]
    #     msg = last_msg[1]
    #     msg_time = last_msg[-1].strftime("%m/%d/%Y %H:%M")
    #     chat_id_last_msg_and_time[chat_id] = [chat_name, msg, msg_time, chat_type]
    return json.dumps({"5467": ["Omer Dagry", "hi", "04/13/2023 8:34", "group"]})


@eel.expose
def get_more_msgs():
    # open_chat_files_lock.acquire()
    # if chat_folder + "\\0" not in open_chat_files:
    #     with open(chat_folder + f"\\{int(min(open_chat_files)) - 1}") as f:
    #         data = json.dumps(pickle.loads(f.read()))
    # else:
    #     data = json.dumps({})
    # open_chat_files_lock.release()
    # return data
    return json.dumps(
        {1: ["omerdagry@gmail.com", "1", "msg", [], False, [], datetime.datetime.now().strftime("%m/%d/%Y")],
         2: ["omerdagry@gmail.com", "2", "msg", [], False, [], datetime.datetime.now().strftime("%m/%d/%Y")],
         3: ["dor", "3", "msg", [], False, [], datetime.datetime.now().strftime("%m/%d/%Y")]})


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


def main():
    eel.init("webroot")
    # TODO: uncomment the following lines
    # t = threading.Thread(target=update)
    # t.start()
    eel.start("index.html")

    # # ---------------------------------------------------------------
    # d = {}
    # for i in range(4, 804):
    #     from_ = "omerdagry@gmail.com" if i % 2 == 0 else random.choice(["dor", "yuval", "ofri", "yoav", "liav"])
    #     d[i] = [from_, str(i), "msg", [], False, [], datetime.datetime.now().strftime("%m/%d/%Y")]
    # with open("check", "wb") as f:
    #     f.write(pickle.dumps(d))


if __name__ == '__main__':
    main()
