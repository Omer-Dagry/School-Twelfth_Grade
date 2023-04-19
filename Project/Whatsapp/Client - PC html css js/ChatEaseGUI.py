import os
import shutil

import eel
import wave
import time
import json
import pickle
import pyaudio
import tkinter
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
message_options_root: tkinter.Tk | None = None
stop_rec: bool = True


"""                                                 Chat                                                             """


@eel.expose
def get_all_chat_ids() -> str:
    chat_ids = [chat_id for chat_id in os.listdir(f"webroot\\{email}") if os.path.isdir(f"webroot\\{email}\\{chat_id}")]
    chat_ids.remove("profile_pictures")
    if "recordings" in chat_ids:
        chat_ids.remove("recordings")
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
def get_user_last_seen(user_email: str) -> str:
    with open(f"webroot\\{email}\\users_status", "rb") as f:
        users_status: dict = pickle.loads(f.read())
    return users_status.get(user_email, "")


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
def get_more_msgs() -> str:
    open_chat_files_lock.acquire()
    if chat_folder + "\\0" not in open_chat_files:
        with open(chat_folder + f"\\{int(min(open_chat_files)) - 1}") as f:
            data = json.dumps(pickle.loads(f.read()))
    else:
        data = json.dumps({})
    open_chat_files_lock.release()
    return data


@eel.expose
def get_known_to_user() -> str:
    with open(f"webroot\\{email}\\known_users", "rb") as f:
        known_users: set[str] = pickle.loads(f.read())
    return json.dumps(dict(((i, user_email) for i, user_email in enumerate(list(known_users)))))


"""                                              Get User Info                                                       """


@eel.expose
def get_email() -> str:
    return email


@eel.expose
def get_username() -> str:
    return username


"""                             Sync With Server & Update Open Chats In GUI                                          """


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


"""                                   Communication Wrapper Functions                                                """


@eel.expose
def send_file(chat_id: str, file_path: str) -> None:
    file_path = f"webroot\\{file_path}"
    if file_path == "webroot\\" or os.path.isfile(file_path):
        communication.upload_file(chat_id, filename=file_path)


@eel.expose
def send_message(message: str, chat_id: str) -> bool:
    return communication.send_message(chat_id, message, sock) if chat_id != "" else False


@eel.expose
def new_chat(other_email: str) -> bool:
    return communication.new_chat(other_email, sock)


@eel.expose
def new_group(other_emails: list[str], group_name: str) -> bool:
    return communication.new_group(other_emails, group_name, sock)[0]


@eel.expose
def add_user_to_group(other_email: str, chat_id: str) -> bool:
    return communication.add_user_to_group(other_email, chat_id, sock)


@eel.expose
def remove_user_from_group(other_email: str, chat_id: str) -> bool:
    return communication.remove_user_from_group(other_email, chat_id, sock)


@eel.expose
def make_call(chat_id: str) -> bool:
    return communication.make_call(chat_id) if chat_id != "" else False


@eel.expose
def upload_profile_picture() -> bool:
    return communication.upload_profile_picture()


@eel.expose
def delete_message_for_me(chat_id: str, message_index: int):
    return communication.delete_message_for_me(chat_id, message_index, message_options_root, sock)


@eel.expose
def delete_message_for_everyone(chat_id: str, message_index: int):
    return communication.delete_message_for_everyone(chat_id, message_index, message_options_root, sock)


"""                                           Recording                                                              """


@eel.expose
def start_recording(chat_id: str) -> bool:
    global stop_rec
    if stop_rec:
        stop_rec = False
        recording_thread = threading.Thread(target=record_audio, args=(chat_id,), daemon=True)
        recording_thread.start()
        return True
    return False


def record_audio(chat_id: str) -> None:
    global stop_rec
    skip = False
    os.makedirs("webroot\\omerdagry@gmail.com\\recordings", exist_ok=True)  # TODO: change to {email}
    # TODO: change to {email}
    num = max([int(num.split(".")[0]) for num in os.listdir("webroot\\omerdagry@gmail.com\\recordings")] + [0])
    recording_file_path = f"webroot\\omerdagry@gmail.com\\recordings\\{num + 1}.wav"
    try:
        audio = pyaudio.PyAudio()
        stream = audio.open(format=pyaudio.paInt16, channels=1, rate=44100, input=True, frames_per_buffer=1024)
        frames = []
        while not stop_rec:
            data = stream.read(1024)
            frames.append(data)
        stream.stop_stream()
        stream.close()
        audio.terminate()
        with open(recording_file_path, "wb") as f:
            sound_file = wave.open(f, "wb")
            sound_file.setnchannels(1)
            sound_file.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
            sound_file.setframerate(44100)
            sound_file.writeframes(b''.join(frames))
            sound_file.close()
    except Exception as e:  # in case there is no microphone
        # TODO: display error message
        skip = True
    finally:
        # TODO: disable recording button until RecordingOptions is closed
        stop_rec = True
    if not skip:
        time.sleep(1)
        eel.display_recording_options(recording_file_path[8:], chat_id)
        print("done")


@eel.expose
def stop_recording() -> bool:
    global stop_rec
    if not stop_rec:
        stop_rec = True
        time.sleep(2)
        return True
    return False


@eel.expose
def delete_recording(recording_file_path: str):
    if os.path.isfile(f"webroot\\{recording_file_path}"):
        os.remove(f"webroot\\{recording_file_path}")


"""                                 Connect To Server & Start GUI & Sync                                             """


def start(user_email: str, user_username: str, user_password: str,
          server_ip_port_: tuple[str, int], first_time_sync_all: bool,
          regular_sock: EncryptedProtocolSocket, sync_sock: EncryptedProtocolSocket) -> None:
    global email, username, password, communication, server_ip_port, sock
    # Set Globals
    email = user_email
    sock = regular_sock
    username = user_username
    password = user_password
    server_ip_port = server_ip_port_
    communication = Com(email, password, server_ip_port)
    # Start sync thread
    t = threading.Thread(target=update, args=(communication, sync_sock, first_time_sync_all,), daemon=True)
    t.start()
    # Wait for first sync (so we will have all the data) and then launch the GUI
    while not first_sync_done:
        time.sleep(0.1)
    # Launch GUI
    try:
        eel.init("webroot")
        eel.start("index.html", port=8080)
    finally:
        shutil.rmtree(f"webroot\\{email}\\recordings")


if __name__ == '__main__':
    # start("omerdagry@gmail.com", "Omer Dagry", "", ("127.0.0.1", 8820), True)

    # --------------------------------------

    email = "omerdagry@gmail.com"
    username = "Omer Dagry"
    try:
        eel.init("webroot")
        eel.start("index.html", port=8080)
    finally:
        if os.path.isdir("webroot\\omerdagry@gmail.com\\recordings"):
            shutil.rmtree("webroot\\omerdagry@gmail.com\\recordings")


# TODO: add a communication options to upload a group picture
