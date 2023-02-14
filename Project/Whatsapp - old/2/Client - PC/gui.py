import os
import time
import wave
import pyaudio
import logging
import pyperclip
import playsound
import multiprocessing

from tkinter import *
from threading import Thread
from PIL.ImageOps import contain
from PIL import Image as ImagePIL
from PIL import ImageTk as ImageTkPIL
from communication import upload_file, send_message, new_chat


# logging
LOG_FORMAT = "%(levelname)s | %(asctime)s | %(processName)s | %(message)s"
LOG_LEVEL = logging.DEBUG
LOG_DIR = 'log'
LOG_FILE = LOG_DIR + "/Chats-Client.log"

# Constants
APP_NAME = "ChatEase"
WINDOW_MIN_SIZE = (980, 520)
APP_BACKGROUND_COLOR = "#1E1F22"

# Globals
playing_file_path = None
playing_thread = None
playing_button = None
root: Tk
email: str
stop_rec: bool
msg_box: Entry
chat_buttons: Text
record_button: Button
current_chat_name: Label
send_msg: Button
file_upload: Button
search_user: Entry
search_chat: Button


def resource_path(relative_path):
    """ return the path to a resource """
    return os.path.join(os.path.abspath("."), relative_path)


def enter_key(event=None):
    """
    allows to press on the enter key to send a message
    :param event: because this function is called from a button press it can send this func an event
    """
    global msg_box, current_chat_name
    if len(event.char) > 0 and ord(event.char) == 13:
        pass
        # TODO: call send_message func


def play_audio_thread(filepath: str, button: Button):
    """ Creates a thread that plays the audio file and changes the button text
    :param filepath: the path to the audio file
    :param button: the button that got pressed
    """
    global playing_thread, playing_file_path, playing_button
    if playing_file_path is not None:  # if there is something playing right now it will terminate it
        terminate_and_restore_button(playing_thread, playing_button, playing_file_path)
    play_ = multiprocessing.Process(target=playsound.playsound, args=(filepath,), daemon=True)
    play_.start()
    playing_thread = play_
    playing_file_path = filepath
    playing_button = button
    text = button.name
    if text is not None:
        button.configure(text="\n".join(text.split("\n")[:-1]) + "\nPress To Stop")
        button.name = text
    else:
        button.configure(text="Stop")
    button.configure(command=lambda: terminate_and_restore_button(play_, button, filepath))
    check_if_finished = Thread(target=check_if_process_alive, args=(play_, button, filepath,), daemon=True)
    check_if_finished.start()


def check_if_process_alive(play_: multiprocessing.Process, button: Button, filepath: str):
    """ Checks if the audio file is still being played, if not shuts the process """
    while True:
        if not play_.is_alive():
            terminate_and_restore_button(play_, button, filepath)
            break
        time.sleep(0.5)


def terminate_and_restore_button(play_: multiprocessing.Process, button: Button, filepath: str):
    """
    Terminates the process of the audio file
    Restores button
    :param play_: the thread that the file is being played from
    :param button: the button that got pressed
    :param filepath: the path to the audio file
    """
    global playing_thread, playing_file_path, playing_button
    play_.terminate()
    if playing_button == button and playing_thread == play_ and playing_file_path == filepath:
        playing_thread = None
        playing_file_path = None
        playing_button = None
    text = button.name
    if text is not None:
        button.configure(text="\n".join(text.split("\n")[:-1]) + "\nPress To Play")
        button.name = text
    else:
        button.configure(text="Play")
    button.configure(command=lambda: play_audio_thread(filepath,  button))


def recording_options():
    """
    after recording this function will be called to open a window with 3 options
    1) play - plays the voice recording
    2) delete - deletes the voice recording (doesn't send it)
    3) send - send the voice recording
    """
    color = "#ffffd0"
    size = 120
    window_x = root.winfo_screenwidth() / 2
    window_y = root.winfo_screenheight() / 2
    # create options window & configure it
    options_window = Tk()
    options_window.title("Options")
    options_window.geometry("250x%d+%d+%d" % (size, window_x, window_y))
    options_window.minsize(250, size)
    options_window.maxsize(250, size)
    play = Button(options_window, text="Play", bg=color, width=21)
    play.configure(command=lambda: play_audio_thread(r"%s\temp.wav" % email, play))
    play.grid(row=0, column=0, sticky="news")
    delete = Button(options_window, text="Delete", bg=color,
                    command=lambda: delete_file_close_window(r"%s\temp.wav" % email, options_window))
    delete.grid(row=1, column=0, sticky="news")
    send = Button(options_window, text="Send", bg=color,
                  command=lambda: upload_file(current_chat_name, r"%s\temp.wav" % email, options_window))
    send.grid(row=2, column=0, sticky="news")
    root.mainloop()
    # if user didn't press anything and closed the window the recording file still exist so this deletes it
    if os.path.isfile(r"%s\temp.wav" % email):
        os.remove(r"%s\temp.wav" % email)


def stop_recording():
    """ Changes the global variable stop_rec to False """
    global stop_rec
    stop_rec = True


def record_():
    """ Creates a Thread to record """
    global stop_rec, record_button, current_chat_name
    if current_chat_name.text != "Home":
        stop_rec = False
        rec_ = Thread(target=record, daemon=True)
        rec_.start()
        record_button.configure(command=stop_recording, text="Stop Recording")


def record():
    """
    Records Audio
    Saves it to a file named temp.wav in the user folder
    calls the upload_file__ function to send the file to the other user
    """
    global stop_rec, record_button, email
    skip = False
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
        sound_file = wave.open(r"%s\temp.wav" % email, "wb")
        sound_file.setnchannels(1)
        sound_file.setsampwidth(audio.get_sample_size(pyaudio.paInt16))
        sound_file.setframerate(44100)
        sound_file.writeframes(b''.join(frames))
        sound_file.close()
    except:  # in case there is no microphone
        skip = True
    finally:
        record_button.configure(command=record_, text="Record", state=DISABLED)  # disable recording button
        stop_rec = True
    if not skip:
        options_thread = Thread(target=recording_options, daemon=True)
        options_thread.start()


def delete_file_close_window(filepath: str, window: Tk):
    """ Deletes the voice recording and closes the voice recording options window
    :param filepath: the path of the voice recording file
    :param window: the root of the options window
    """
    os.remove(filepath)
    window.destroy()


def delete_for_me(chat_id: str, index: int, window: Tk):
    """ deletes the msg in chat_id at index for the user only """
    global email
    # TODO: call delete_message_for_me
    window.destroy()


def delete_for_all(chat_id: str, index: int, window: Tk):
    """ deletes the msg in chat_id at index for everyone """
    global email
    # TODO: call delete_message_for_all
    window.destroy()


def search_delete_on_click(event=None):
    """"
    deletes the text in the entry box of user search when it's clicked on
    :param event: because this function is called from a button press it can send this func an event
    """
    global search_user
    text = search_user.get()
    if text == "" or text == "Start a new chat" or text == "Error" or text == "Invalid User Name" or \
            text == "Please Type A User Name" or text == "You Can't Start A Chat With Yourself" or \
            text == "Username Doesn't Exists" or text == "Chat Already Exists":
        search_user.delete(0, END)
        search_user.insert(END, '')


def enter_key_search_user(event=None):
    """
    allows to press on the enter key to search a user
    :param event: because this function is called from a button press it can send this func an event
    """
    global search_user, email
    if len(event.char) > 0 and ord(event.char) == 13:
        new_chat(search_user, email)


def mainloop(user_email: str):
    global chat_buttons, current_chat_name, msg_box, root, email, record_button, \
        send_msg, file_upload, search_user, search_chat
    email = user_email
    # Create Window
    root = Tk()
    # Configure Window
    root.title(APP_NAME)  # title of window
    root.iconbitmap(resource_path("ChatEase.ico"))  # icon of window
    root.config(bg=APP_BACKGROUND_COLOR)  # background color of window
    root.minsize(WINDOW_MIN_SIZE[0], WINDOW_MIN_SIZE[1])  # minimum size of window
    root.state("zoomed")  # open window in full-screen windowed
    root.columnconfigure(2, weight=1)
    root.rowconfigure((1, 2), weight=1)
    #
    # Container for all the chat buttons
    chat_buttons = Text(root, background=APP_BACKGROUND_COLOR, width=42, cursor="arrow", height=27)
    chat_buttons.grid(row=1, column=0, columnspan=2, rowspan=2, sticky="news")
    # Current chat name label
    current_chat_name = Label(root, text="Home", height=2, font="bold",
                              bg=APP_BACKGROUND_COLOR, fg="white", justify="center")
    current_chat_name.text = "Home"
    current_chat_name.chat_id = None
    current_chat_name.grid(row=0, column=2, columnspan=2, sticky="news")
    # Entry box for text
    msg_box = Entry(root, width=121, bg=APP_BACKGROUND_COLOR, fg="white", font=("helvetica", 16))
    msg_box.bind('<KeyPress>', enter_key)
    msg_box.grid(row=19, column=2, sticky='news')
    # Button to record audio
    photo = PhotoImage(file=resource_path("microphone.png"))
    record_button = Button(root, image=photo, command=record_, bg=APP_BACKGROUND_COLOR,
                           height=68, width=140, fg="#63C8D8", text="Record")
    record_button.grid(row=19, column=3, sticky='news')
    # Button to submit the input from the input box
    photo2 = PhotoImage(file=resource_path("send.png"))
    send_msg = Button(root, image=photo2, width=40, height=3, bg=APP_BACKGROUND_COLOR, fg="white", font=None,
                      command=lambda: send_message(current_chat_name, msg_box.get()))
    send_msg.grid(row=19, column=0, sticky='news')
    # Button to upload files
    photo3 = PhotoImage(file=resource_path("doc.png"))
    file_upload = Button(root, image=photo3, bg=APP_BACKGROUND_COLOR, height=1, width=1,
                         command=lambda: upload_file(current_chat_name))
    file_upload.grid(row=19, column=1, sticky='news')
    # Create an input box to search a username and start chat with him
    search_user = Entry(root, width=40, font=None)
    search_user.bind('<Button-1>', search_delete_on_click)
    search_user.bind('<KeyPress>', enter_key_search_user)
    search_user.insert(END, "Start a new chat")
    search_user.grid(row=0, column=0, sticky='news')
    # Create a button to submit the input from the input box
    search_chat = Button(root, text="Search", width=8, height=1, bg=APP_BACKGROUND_COLOR, fg="white",
                         command=lambda: new_chat(search_user, email), font=None)
    search_chat.grid(row=0, column=1, sticky='news')
    # Home window
    home_chat = Text(root, height=9999999, width=9999999,
                     bg=APP_BACKGROUND_COLOR, state=DISABLED, font=('helvetica', '16'))
    home_chat.grid(row=1, column=2, sticky='news', columnspan=2)
    # mainloop
    root.mainloop()


mainloop("omerdagry@gmail.com")


def update():
    pass
