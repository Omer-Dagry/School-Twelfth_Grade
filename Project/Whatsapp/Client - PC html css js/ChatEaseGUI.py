"""
###############################################
Author: Omer Dagry
Mail: omerdagry@gmail.com
Date: 30/05/2023 (dd/mm/yyyy)


bindings between the communication.py to the eel website
and some more function to get chats & users data
###############################################
"""

import io
import multiprocessing
import os
import sys
import wave
import time
import json
import socket
import shutil
import pickle
import easygui
import hashlib
import imaplib
import pyaudio
import threading
import traceback
import email as email_lib
# for .exe
if not os.path.dirname(__file__).endswith("Client - PC html css js"):
    os.chdir(os.path.dirname(__file__))  # change working dir to were the .exe was unpacked in
    # no stderr & stdout because the .exe is created without a console, so redirect it
    logfile = io.StringIO()
    sys.stdout = logfile
    sys.stderr = logfile
# import eel only after handling stdout and stderr
import eel

from calls_udp_client import join_call
from communication import Communication as Com
from ClientSecureSocket import ClientEncryptedProtocolSocket
from communication import signup_request, send_confirmation_code, reset_password_request, reset_password_choose_password


# Constants
SERVER_PORT = 8820

# Globals
email: None | str = None
username: None | str = None
password: None | str = None
communication: None | Com = None
sock: None | ClientEncryptedProtocolSocket = None
sync_sock: None | ClientEncryptedProtocolSocket = None
waiting_for_confirmation_code_reset: bool = False
waiting_for_confirmation_code_signup: bool = False
sync_thread: threading.Thread | None = None
first_time_sync_all: bool = True
open_chat_files_lock = threading.Lock()
open_chat_files: set[str] = set()
chat_folder: str = ""
stop_rec: bool = True
stop: bool = False
send_file_active: list[bool] = [False]
call_process: multiprocessing.Process | None = None


"""                                                 Chat                                                             """


@eel.expose
def get_all_chat_ids() -> str:
    """ returns all chat ids as json dict, {chat_ids: [chat_name, last_msg, last_msg_time, chat_type, users]} """
    chat_ids = [chat_id for chat_id in os.listdir(f"webroot\\{email}") if os.path.isdir(f"webroot\\{email}\\{chat_id}")]
    if "profile_pictures" in chat_ids:
        chat_ids.remove("profile_pictures")
    if "recordings" in chat_ids:
        chat_ids.remove("recordings")
    # {chat_id,
    #  [chat_name, last_message, time, chat_type - group or the email of the other user, users, num_of_unread_msgs]
    #  }
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
            msgs_index = set(last_chat_msgs.keys())
            last_msg_index = max(msgs_index)
            last_msg = last_chat_msgs[last_msg_index]
            if email not in last_msg[3]:
                sender = last_msg[0].split('@')[0] if last_msg[0] != email else "You"
                msg = f"{sender}: {last_msg[1]}"
                msg = msg if len(msg) <= 25 else msg[:25] + "..."
            else:
                msg = ""
            msg_time = last_msg[-1]
            number_of_unread_msgs = 0
            if os.path.isfile(f"webroot\\{email}\\{chat_id}\\unread_msgs"):
                with open(f"webroot\\{email}\\{chat_id}\\unread_msgs", "rb") as f:
                    try:
                        unread_msgs_dict: dict = pickle.loads(f.read())
                    except EOFError:
                        unread_msgs_dict = {}
                if email in unread_msgs_dict:
                    number_of_unread_msgs = unread_msgs_dict[email]
            chat_id_last_msg_and_time[chat_id] = [chat_name, msg, msg_time, chat_type, users, number_of_unread_msgs]
        except FileNotFoundError:
            pass
    return json.dumps(chat_id_last_msg_and_time)


@eel.expose
def get_user_last_seen(user_email: str) -> str:
    """ returns the time 'user_email' was last seen or 'Online' if he is online """
    with open(f"webroot\\{email}\\users_status", "rb") as f:
        try:
            users_status: dict = pickle.loads(f.read())
        except EOFError:
            users_status = {}
    return users_status.get(user_email, "")


@eel.expose
def get_chat_msgs(chat_id: str) -> str:
    """ returns the last file of msgs + the file before it (max 1600 msgs) """
    global chat_folder, open_chat_files
    latest_file_path = f"webroot\\{email}\\{chat_id}\\data\\chat\\"
    latest_file = max(os.listdir(latest_file_path))
    data: dict = {}
    open_chat_files = set()
    if latest_file != "0":
        with open(f"{latest_file_path}{int(latest_file) - 1}", "rb") as f:
            data = pickle.loads(f.read())
        open_chat_files.add(f"{latest_file_path}{int(latest_file) - 1}")
    latest_file_path += latest_file
    with open(latest_file_path, "rb") as f:
        data.update(pickle.loads(f.read()))
    open_chat_files_lock.acquire()
    open_chat_files.add(latest_file_path)
    chat_folder = os.path.dirname(latest_file_path)
    open_chat_files_lock.release()
    return json.dumps(data)


@eel.expose
def get_more_msgs() -> str:
    """ checks if there is an older chat file that isn't already loaded, if there is it returns the msgs (800 msgs) """
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
    """ returns all the users that are known to the user """
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


def update(first_time_sync_mode: bool) -> None:
    """ syncs with the sever and updates the GUI """
    global sync_sock, stop
    while not stop:
        try:
            # sends nothing, waits for sync msg from server
            new_data, modified_files, deleted_files, ongoing_calls = communication.sync(sync_sock)
        except (ConnectionError, socket.error, UnicodeError):
            sync_sock.close()
            status, sync_sock, reason = \
                communication.login_sync(verbose=False, sync_mode="all" if first_time_sync_mode else "new")
            if not status:
                # TODO: display error (reason)
                break
            continue
        if new_data:
            try:
                if first_time_sync_mode:
                    raise AttributeError
                open_chat_id = eel.get_open_chat_id()()
            except AttributeError:  # GUI haven't loaded up yet
                open_chat_id = ""
            if open_chat_id != "":
                # let the server know that the user saw all the messages in the chat
                mark_as_seen(open_chat_id)
                for file_path in modified_files:
                    if open_chat_id == file_path.split("\\")[2] and file_path in open_chat_files:
                        try:
                            with open(file_path, "rb") as f:
                                data = json.dumps(pickle.loads(f.read()))
                            eel.update(open_chat_id, data)()
                        except (pickle.UnpicklingError, AttributeError):
                            pass
            # delete a file, if the user who sent it deleted the msg
            for file_path in deleted_files:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            if ongoing_calls.keys():
                # update GUI about new calls
                for group_name, port in ongoing_calls.items():
                    print(group_name, port)
                    eel.ongoing_call(group_name, port)()
                    print("called ongoing call")
        if first_time_sync_mode and new_data:
            os.makedirs(f"webroot\\{email}\\first sync done", exist_ok=True)
            first_time_sync_mode = False


"""                                   Communication Wrapper Functions                                                """


@eel.expose
def mark_as_seen(open_chat_id: str) -> None:
    """ let the server know that the user saw all the messages in the chat """
    if sync_sock is not None and open_chat_id is not None and open_chat_id != "":
        communication.mark_as_seen(sync_sock, open_chat_id)


@eel.expose
def login(email_: str, password_: str) -> tuple[bool, str]:
    """ login & start sync """
    global communication, sock, email, password, username, sock, first_time_sync_all, sync_sock
    if email_ is None or email_ == "" or password_ is None or password_ == "":
        return False, ""
    if sock is not None:
        try:
            sock.close()
        except (ConnectionError, socket.error):
            pass
    sock = None
    password_ = hashlib.md5(password_.encode()).hexdigest().lower()
    communication = Com(email_, password_, SERVER_IP_PORT)
    status, regular_sock, username_or_reason = communication.login(verbose=False)
    if status:
        sock = regular_sock
        username = username_or_reason
        email = email_
        password = password_
        start_app()  # start sync thread
        while not os.path.isdir(f"webroot\\{email}\\first sync done"):  # wait for first sync to finish
            time.sleep(0.01)
        return True, ""
    communication = None
    return False, username_or_reason


@eel.expose
def signup_stage1(email_: str, password_: str, username_: str) -> tuple[bool, str]:
    """ make a request to signup """
    if email_ is None or username_ is None or email_ == "" or username_ == "" or password_ is None or password_ == "":
        return False, ""
    global sock, email, password, username, waiting_for_confirmation_code_signup
    password_ = hashlib.md5(password_.encode()).hexdigest().lower()
    status, regular_sock, reason = signup_request(username_, email_, password_, SERVER_IP_PORT, return_status=True)
    if status:
        sock = regular_sock
        username = username_
        email = email_
        password = password_
        waiting_for_confirmation_code_signup = True
        return True, reason
    return False, reason


@eel.expose
def signup_stage2(confirmation_code: str) -> bool:
    """ confirmation code for signup request """
    global waiting_for_confirmation_code_signup, sock
    if sock is None or not waiting_for_confirmation_code_signup or confirmation_code is None or confirmation_code == "":
        return False
    waiting_for_confirmation_code_signup = False
    status = send_confirmation_code(sock, confirmation_code, False, "signup")
    if not status:
        sock = None
    return status


@eel.expose
def reset_password_stage1(email_: str, username_: str) -> bool:
    """ make a request to reset password """
    if email_ is None or username_ is None or email_ == "" or username_ == "":
        return False
    global sock, waiting_for_confirmation_code_reset
    status, regular_sock = reset_password_request(username_, email_, SERVER_IP_PORT)
    if status:
        waiting_for_confirmation_code_reset = True
        sock = regular_sock
    return status


@eel.expose
def reset_password_stage2(confirmation_code: str, password_: str) -> bool:
    """ confirmation code and password reset """
    global waiting_for_confirmation_code_reset, sock
    if sock is None or not waiting_for_confirmation_code_reset or \
            password_ is None or confirmation_code is None or password == "" or confirmation_code == "":
        return False
    waiting_for_confirmation_code_reset = False
    status = send_confirmation_code(sock, confirmation_code, False, "reset")
    if not status:
        sock = None
        return False
    password_ = hashlib.md5(password_.encode()).hexdigest().lower()
    status = reset_password_choose_password(sock, password_)
    if not status:
        sock = None
    return status


@eel.expose
def send_file(chat_id: str, file_path: str) -> None:
    """ send a file """
    global communication, send_file_active
    if send_file_active[0]:
        return None
    send_file_active[0] = True
    if chat_id == "" or chat_id is None:
        return None
    if os.path.isfile(file_path):
        communication.upload_file(chat_id, filename=file_path, send_file_active=send_file_active)
        return None
    file_path = f"webroot\\{file_path}"
    if os.path.isfile(file_path):
        communication.upload_file(chat_id, filename=file_path, send_file_active=send_file_active)
    elif file_path == "webroot\\":
        communication.upload_file(chat_id, send_file_active=send_file_active)
    return None


@eel.expose
def send_message(message: str, chat_id: str) -> bool:
    """ send a message """
    global sock
    if chat_id == "" or message == "" or message is None or chat_id is None:
        return False
    res = communication.send_message(chat_id, message, sock)
    if not res:
        sock.close()
        status, sock, reason = communication.login(verbose=False)
        res = communication.send_message(chat_id, message, sock)
        if not res:
            pass
            # TODO: display error
    return res


@eel.expose
def familiarize_user_with(other_email: str) -> bool:
    """ check if other_email exists and if it does make him "known" to this user """
    return communication.familiarize_user_with(other_email, sock)


@eel.expose
def new_chat(other_email: str) -> bool:
    """ create a new chat (one on one) """
    return communication.new_chat(other_email, sock)


@eel.expose
def new_group(other_emails: list[str], group_name: str) -> bool:
    """ create a new group """
    print(other_emails, group_name)
    return communication.new_group(other_emails, group_name, sock)[0]


@eel.expose
def add_user_to_group(other_email: str, chat_id: str) -> bool:
    """ add a user to a group """
    return communication.add_user_to_group(other_email, chat_id, sock)


@eel.expose
def remove_user_from_group(other_email: str, chat_id: str) -> bool:
    """ remove a user from a group """
    return communication.remove_user_from_group(other_email, chat_id, sock)


@eel.expose
def make_call(chat_id: str) -> bool:
    """ start a call """
    global call_process
    call_server_port = communication.make_call(chat_id) if chat_id != "" else None
    if call_server_port is None:
        return False
    if call_process is not None:
        call_process.kill()
        call_process = None
    call_process = multiprocessing.Process(
        # TODO:             change to SERVER_IP
        target=join_call, args=((SERVER_IP, call_server_port), email, password,), daemon=True
    )
    call_process.start()
    return True


@eel.expose
def answer_call(port: int) -> None:
    global call_process
    if call_process is not None:
        call_process.kill()
        call_process = None
    call_process = multiprocessing.Process(
        # TODO:             change to SERVER_IP
        target=join_call, args=((SERVER_IP, port), email, password,), daemon=True
    )
    call_process.start()


@eel.expose
def check_ongoing_call():
    """ returns True if there is an ongoing call otherwise False """
    global call_process
    if call_process is not None and call_process.is_alive():
        return True
    call_process = None
    return False


@eel.expose
def hang_up_call() -> None:
    """ exit call """
    global call_process
    if call_process is not None:
        call_process.kill()
        call_process = None


@eel.expose
def upload_profile_picture() -> bool:
    """ upload a new profile picture """
    return communication.upload_profile_picture()


@eel.expose
def upload_group_picture(chat_id: str) -> bool:
    """ upload a new picture for a group """
    return communication.upload_group_picture(chat_id)


@eel.expose
def delete_message_for_me(chat_id: str, message_index: int) -> bool:
    """ delete a message for yourself """
    return communication.delete_message_for_me(chat_id, message_index, sock)


@eel.expose
def delete_message_for_everyone(chat_id: str, message_index: int) -> bool:
    """ delete a message for everyone """
    return communication.delete_message_for_everyone(chat_id, message_index, sock)


"""                                           Recording                                                              """


@eel.expose
def start_recording(chat_id: str) -> bool:
    """ start audio recording """
    global stop_rec
    if stop_rec:
        stop_rec = False
        recording_thread = threading.Thread(target=record_audio, args=(chat_id,), daemon=True)
        recording_thread.start()
        return True
    return False


def record_audio(chat_id: str) -> None:
    """ this function is the actual function the records audio """
    global stop_rec
    skip = False
    os.makedirs(f"webroot\\{email}\\recordings", exist_ok=True)
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
        stop_rec = True
    if not skip:
        time.sleep(1)
        eel.display_recording_options(recording_file_path[8:], chat_id)()
        # send_file(chat_id, recording_file_path)


@eel.expose
def stop_recording() -> bool:
    """ stop recording """
    global stop_rec
    if not stop_rec:
        stop_rec = True
        time.sleep(2)
        return True
    return False


@eel.expose
def delete_recording(recording_file_path: str):
    """ delete recording """
    if os.path.isfile(f"webroot\\{recording_file_path}"):
        os.remove(f"webroot\\{recording_file_path}")


"""                                           Other Functions                                                        """


@eel.expose
def start_file(file_path: str) -> bool:
    """ open a file """
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
    """ called when there is a refresh / a redirect in order to restart the sync """
    global sync_thread, stop, call_process
    stop = True
    if sync_thread is not None:
        sync_thread.join()
        if sync_sock is not None:
            sync_sock.close()
        sync_thread = None
        if call_process is not None:
            call_process.kill()
        call_process = None


def get_server_ip() -> str | None:
    """ try to get the server IP from the email that is shared between all the clients """
    try:
        connection = imaplib.IMAP4_SSL("imap.gmail.com")
        connection.login("project.twelfth.grade.get.ip@gmail.com", "wkqakclcvgfwyitn")
        connection.select()
        result, data = connection.uid('search', None, "ALL")
        if result == 'OK':
            for num in reversed(data[0].split()):
                result, data = connection.uid('fetch', num, '(RFC822)')
                if result == 'OK':
                    email_message = email_lib.message_from_bytes(data[0][1])
                    from_email = str(email_message['From'])
                    if from_email != "project.twelfth.grade@gmail.com":
                        continue
                    subject = str(email_message['Subject'])
                    if subject == "server up":
                        content = str(email_message.get_payload()[0])
                        return content.split('server_ip=')[-1].strip()
                    elif subject == "server down":
                        return None
        connection.close()
        connection.logout()
    except Exception as e:
        traceback.format_exception(e)  # returns the formatted exception
        return None


"""                                 Connect To Server & Start GUI & Sync                                             """


@eel.expose
def start_app() -> None:
    """ start sync """
    global sync_thread, sync_sock, first_time_sync_all, stop
    os.makedirs(f"webroot\\{email}\\", exist_ok=True)
    close_program()
    if sync_sock is not None:
        sync_sock.close()
    status, sync_sock, reason = \
        communication.login_sync(verbose=False, sync_mode="all" if first_time_sync_all else "new")
    if not status:
        pass  # TODO: display error
        print("error restarting sync sock")
    stop = False
    if sync_thread is None or not sync_thread.is_alive():
        # Start sync thread
        sync_thread = threading.Thread(target=update, args=(first_time_sync_all,), daemon=True)
        sync_thread.start()
        first_time_sync_all = False


def main():
    """ launch eel """
    # Launch GUI
    try:
        if os.path.isdir(f"webroot\\{email}\\first sync done"):
            shutil.rmtree(f"webroot\\{email}\\first sync done")
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
        eel.start("login.html", port=port, cmdline_args=["-incognito"])
    except (Exception, BaseException) as e:
        if not isinstance(e, SystemExit) and not isinstance(e, KeyboardInterrupt):
            traceback.print_exception(e)
    finally:
        if os.path.isdir(f"webroot\\{email}"):
            shutil.rmtree(f"webroot\\{email}")
            # shutil.rmtree(f"webroot\\{email}\\recordings")
            # shutil.rmtree(f"webroot\\{email}\\first sync done")
        try:
            if sync_sock is not None:
                sync_sock.close()
        except (ConnectionError, socket.error):
            pass
        try:
            if sock is not None:
                sock.close()
        except (ConnectionError, socket.error):
            pass


if __name__ == '__main__':
    # More Constants
    # Server IP - try to get through clients shared email, if not ask from user
    SERVER_IP = None  # get_server_ip()
    while SERVER_IP != "no" and \
            (SERVER_IP is None or SERVER_IP.count(".") != 3 or not
            all((i.isnumeric() and -1 < int(i) < 256 for i in SERVER_IP.split(".")))):
        SERVER_IP = easygui.enterbox("Please Enter Server IP: ", "Server IP")
    if SERVER_IP == "no":  # cancel run
        sys.exit(1)
    assert SERVER_IP.count(".") == 3 and all((i.isnumeric() and -1 < int(i) < 256 for i in SERVER_IP.split("."))), \
        "Invalid Server IP"
    SERVER_IP_PORT = (SERVER_IP, SERVER_PORT)
    main()
