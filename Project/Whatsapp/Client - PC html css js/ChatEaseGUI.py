import os
import sys

import eel
import wave
import time
import json
import socket
import shutil
import pickle
import pyaudio
import tkinter
import threading
import traceback

from communication import Communication as Com
from client_encrypted_protocol_socket import ClientEncryptedProtocolSocket


# Constants

# Globals
first_sync_done: bool = False
email: None | str = None
username: None | str = None
password: None | str = None
server_ip_port: None | tuple[str, int] = None
communication: None | Com = None
sock: None | ClientEncryptedProtocolSocket = None
open_chat_files_lock = threading.Lock()
open_chat_files: set[str] = set()
chat_folder: str = ""
message_options_root: tkinter.Tk | None = None
stop_rec: bool = True
stop: bool = False
sync_thread: threading.Thread | None = None
first_time_sync_all: bool = True
sync_sock: ClientEncryptedProtocolSocket | None = None


"""                                                 Chat                                                             """


@eel.expose
def get_all_chat_ids() -> str:
    chat_ids = [chat_id for chat_id in os.listdir(f"webroot\\{email}") if os.path.isdir(f"webroot\\{email}\\{chat_id}")]
    if "profile_pictures" in chat_ids:
        chat_ids.remove("profile_pictures")
    if "recordings" in chat_ids:
        chat_ids.remove("recordings")
    #       [chat_id, [chat_name, last_message, time, chat_type (group or the email of the user the chat is with)]
    chat_id_last_msg_and_time: dict[str, list[str, str, str, str]] = {}
    for chat_id in chat_ids:
        try:
            with open(f"webroot\\{email}\\{chat_id}\\name", "rb") as f:
                chat_name = pickle.loads(f.read())
            chat_type = "group" if len(chat_name) == 1 else "1 on 1"
            chat_name = chat_name[0] if len(chat_name) == 1 else chat_name[0] if chat_name[0] != username \
                else chat_name[1]
            with open(f"webroot\\{email}\\{chat_id}\\users", "rb") as f:
                users = list(pickle.loads(f.read()))
            latest_chat_msgs_file_name = max(os.listdir(f"webroot\\{email}\\{chat_id}\\data\\chat"))
            with open(f"webroot\\{email}\\{chat_id}\\data\\chat\\{latest_chat_msgs_file_name}", "rb") as f:
                last_chat_msgs = pickle.loads(f.read())
            last_msg = last_chat_msgs[max(last_chat_msgs.keys())]
            msg = f"{last_msg[0].split('@')[0]}: {last_msg[1]}"
            msg = msg if len(msg) <= 25 else msg[:25] + "..."
            msg_time = last_msg[-1]
            chat_id_last_msg_and_time[chat_id] = [chat_name, msg, msg_time, chat_type, users]
        except FileNotFoundError:
            pass
    return json.dumps(chat_id_last_msg_and_time)


@eel.expose
def get_user_last_seen(user_email: str) -> str:
    with open(f"webroot\\{email}\\users_status", "rb") as f:
        try:
            users_status: dict = pickle.loads(f.read())
        except EOFError:
            users_status = {}
    return users_status.get(user_email, "")


@eel.expose
def get_chat_msgs(chat_id: str) -> str:
    global chat_folder, open_chat_files
    latest_file = f"webroot\\{email}\\{chat_id}\\data\\chat\\"
    latest_file = latest_file + max(os.listdir(latest_file))
    with open(latest_file, "rb") as f:
        data = json.dumps(pickle.loads(f.read()))
    open_chat_files_lock.acquire()
    open_chat_files = {latest_file}
    chat_folder = os.path.dirname(latest_file)
    open_chat_files_lock.release()
    return data


@eel.expose
def get_more_msgs() -> str:
    open_chat_files_lock.acquire()
    if chat_folder + "\\0" not in open_chat_files:  # no more chat files to load
        with open(chat_folder + f"\\{int(min(list(open_chat_files))) - 1}") as f:
            data = json.dumps(pickle.loads(f.read()))
    else:
        data = json.dumps({})
    open_chat_files_lock.release()
    return data


@eel.expose
def get_known_to_user() -> str:
    with open(f"webroot\\{email}\\known_users", "rb") as f:
        try:
            known_users: list[str] = list(pickle.loads(f.read()))
        except EOFError:
            known_users = list()
    return json.dumps(dict(((i, user_email) for i, user_email in enumerate(list(known_users)))))


"""                                              Get User Info                                                       """


@eel.expose
def get_email() -> str:
    return email


@eel.expose
def get_username() -> str:
    return username


"""                             Sync With Server & Update Open Chats In GUI                                          """


def update(com: Com, sync_socket: ClientEncryptedProtocolSocket, first_time_sync_mode: bool) -> None:
    global first_sync_done, stop
    sync_new = "new"
    sync_all = "all"
    open_chat_id = ""
    while not stop:
        new_data, modified_files, deleted_files = com.sync(sync_socket, sync_all if first_time_sync_mode else sync_new)
        if not first_sync_done:
            first_sync_done = True
            first_time_sync_mode = False
        if new_data:
            try:
                open_chat_id = eel.get_open_chat_id()()
            except AttributeError:  # as e:  # GUI haven't loaded up yet
                # print(*traceback.format_exception(e), sep="")
                pass
            if open_chat_id != "":
                for file_path in modified_files:
                    if open_chat_id == file_path.split("\\")[2] and file_path in open_chat_files:
                        try:
                            with open(file_path, "rb") as f:
                                data = json.dumps(pickle.loads(f.read()))
                            eel.update(open_chat_id, data)()
                        except pickle.UnpicklingError:
                            print(file_path)
                            raise
                        # eel.update(open_chat_id, data)()
            # TODO: handle deleted_files
        if len(modified_files) == 1:  # if there is no new data (only users_status), sleep an extra .5 seconds
            time.sleep(0.5)
        time.sleep(0.5)


"""                                   Communication Wrapper Functions                                                """


@eel.expose
def send_file(chat_id: str, file_path: str) -> None:
    global communication
    print(chat_id, file_path)
    if chat_id == "" or chat_id is None:
        return None
    if os.path.isfile(file_path):
        print("1")
        communication.upload_file(chat_id, filename=file_path)
        return None
    file_path = f"webroot\\{file_path}"
    print(file_path)
    if os.path.isfile(file_path):
        print("2")
        communication.upload_file(chat_id, filename=file_path)
    elif file_path == "webroot\\":
        print("3", threading.current_thread().name)
        communication.upload_file(chat_id)
    print("4")
    return None


@eel.expose
def send_message(message: str, chat_id: str) -> bool:
    return communication.send_message(chat_id, message, sock) if chat_id != "" else False


@eel.expose
def familiarize_user_with(other_email: str) -> bool:
    return communication.familiarize_user_with(other_email, sock)


@eel.expose
def new_chat(other_email: str) -> bool:
    print(f"new chat {other_email}")
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
def upload_group_picture(chat_id: str) -> bool:
    return communication.upload_group_picture(chat_id)


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
    # os.makedirs("webroot\\omerdagry@gmail.com\\recordings", exist_ok=True)  # TODO: change to {email}
    os.makedirs(f"webroot\\{email}\\recordings", exist_ok=True)  # TODO: change to {email}
    # TODO: change to {email}
    # num = max([int(num.split(".")[0]) for num in os.listdir("webroot\\omerdagry@gmail.com\\recordings")] + [0])
    # recording_file_path = f"webroot\\omerdagry@gmail.com\\recordings\\{num + 1}.wav"
    num = max([int(num.split(".")[0]) for num in os.listdir(f"webroot\\{email}\\recordings")] + [0])
    recording_file_path = f"webroot\\{email}\\recordings\\{num + 1}.wav"
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
        eel.display_recording_options(recording_file_path[8:], chat_id)()
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


"""                                           Other Functions                                                        """


@eel.expose
def start_file(file_path: str) -> bool:
    file_path = file_path.replace("/", "\\")
    if os.path.isfile(file_path):
        os.startfile(file_path)
        return True
    elif os.path.isfile(f"webroot\\{file_path}"):
        os.startfile(f"webroot\\{file_path}")
        return True
    return False


@eel.expose
def close_program():
    global stop
    stop = True
    if sync_thread is not None:
        sync_thread.join(5)  # wait up to 5 seconds
    sys.exit(0)


"""                                 Connect To Server & Start GUI & Sync                                             """


def start(user_email: str, user_username: str, user_password: str,
          server_ip_port_: tuple[str, int], first_time_sync_mode: bool,
          regular_sock: ClientEncryptedProtocolSocket, sync_socket: ClientEncryptedProtocolSocket) -> None:
    global email, username, password, communication, server_ip_port, sock, sync_thread, sync_sock, first_time_sync_all
    # Set Globals
    email = user_email
    sock = regular_sock
    sync_sock = sync_socket
    username = user_username
    password = user_password
    server_ip_port = server_ip_port_
    first_time_sync_all = first_time_sync_mode
    os.makedirs(f"webroot\\{email}\\", exist_ok=True)
    communication = Com(email, password, server_ip_port)
    # Start sync thread
    sync_thread = threading.Thread(target=update, args=(communication, sync_sock, first_time_sync_all,), daemon=True)
    sync_thread.start()
    # Wait for first sync (so we will have all the data) and then launch the GUI
    while not first_sync_done and sync_thread.is_alive():
        time.sleep(0.1)
    if sync_thread.is_alive():
        # Launch GUI
        try:
            eel.init("webroot")
            port = 8080
            while True:
                try:
                    with socket.socket() as s:
                        s.bind(("127.0.0.1", port))
                    break
                except OSError:  # port taken
                    if port < 65535:
                        port += 1
                    else:
                        raise Exception("Couldn't find an open port for GUI local host.")
            eel.start("index.html", port=port)
        except (Exception, BaseException) as e:
            if not isinstance(e, SystemExit) and not isinstance(e, KeyboardInterrupt):
                traceback.print_exception(e)
        finally:
            if os.path.isdir(f"webroot\\{email}\\recordings"):
                shutil.rmtree(f"webroot\\{email}\\recordings")
            try:
                eel.close_window()
            except Exception:
                pass
    else:
        print("Error when syncing with server.")


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
