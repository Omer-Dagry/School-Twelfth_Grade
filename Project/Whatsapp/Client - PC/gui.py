import os
import logging
import threading

from tkinter import *
from PIL.ImageOps import contain
from PIL import Image as ImagePIL
from PIL import ImageTk as ImageTkPIL
from recording_gui import RecordingGUI
from communication import upload_file, send_message, new_chat


# logging
LOG_DIR = 'log'
LOG_LEVEL = logging.DEBUG
LOG_FILE = LOG_DIR + "/ChatEase-Client.log"
LOG_FORMAT = "%(levelname)s | %(asctime)s | %(processName)s | %(threadName)s | %(message)s"

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
    current_chat_name.text = "Hom"
    current_chat_name.chat_id = None
    current_chat_name.grid(row=0, column=2, columnspan=2, sticky="news")
    # Entry box for text
    msg_box = Entry(root, width=121, bg=APP_BACKGROUND_COLOR, fg="white", font=("helvetica", 16))
    msg_box.bind('<KeyPress>', enter_key)
    msg_box.grid(row=19, column=2, sticky='news')
    # Button to record audio
    photo = PhotoImage(file=resource_path("microphone.png"))
    record_button = Button(root, image=photo, command=record, bg=APP_BACKGROUND_COLOR,
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


def record():
    print("sdfsdfg")
    g = RecordingGUI(email, record_button, root.winfo_screenwidth(), root.winfo_screenheight(), upload_file, current_chat_name)
    t = threading.Thread(target=g.record_audio)
    t.start()


def update():
    pass


def main():
    mainloop("omerdagry@gmail.com")


if __name__ == '__main__':
    main()
