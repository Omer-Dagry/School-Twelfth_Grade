import os
import time
import logging
import threading
import pyperclip
import multiprocessing

from tkinter import *
from threading import Thread
from PIL.ImageOps import contain
from PIL import Image as ImagePIL
from multiprocessing import Process
from PIL import ImageTk as ImageTkPIL
from recording_gui import RecordingGUI
from communication import upload_file, send_message, new_chat


# logging
LOG_DIR = 'log'
LOG_LEVEL = logging.DEBUG
LOG_FILE = LOG_DIR + "/ChatEase-Client.log"
LOG_FORMAT = "%(levelname)s | %(asctime)s | %(processName)s | %(message)s"


class ChatEaseGUI(Tk):
    def __init__(self, email: str,
                 screen_name=None, base_name=None, class_name='Tk', use_tk=True, sync=False, use=None,
                 app_name: str = "ChatEase", window_min_size: tuple[int, int] = (980, 520),
                 app_background_color: str = "#1E1F22"):
        super().__init__(screen_name, base_name, class_name, use_tk, sync, use)
        #
        self.__app_name = app_name
        self.__window_min_size = window_min_size
        self.__app_background_color = app_background_color
        #
        self.__email: str = email
        #
        self.__msg_box: Entry | None = None
        self.__home_chat: Text | None = None
        self.__send_msg: Button | None = None
        self.__chat_buttons: Text | None = None
        self.__search_user: Entry | None = None
        self.__search_chat: Button | None = None
        self.__file_upload: Button | None = None
        self.__record_button: Button | None = None
        self.__current_chat_name: Label | None = None

    def change_background(self, bg):
        raise NotImplemented

    def __setup(self):
        # Configure Window
        self.title(self.__app_name)  # title of window
        self.iconbitmap(resource_path("ChatEase.ico"))  # icon of window
        self.config(bg=self.__app_background_color)  # background color of window
        self.minsize(self.__window_min_size[0], self.__window_min_size[1])  # minimum size of window
        self.state("zoomed")  # open window in full-screen windowed
        self.columnconfigure(2, weight=1)
        self.rowconfigure((1, 2), weight=1)
        #
        # Container for all the chat buttons
        self.__chat_buttons = Text(self, background=self.__app_background_color, width=42, cursor="arrow", height=27)
        self.__chat_buttons.grid(row=1, column=0, columnspan=2, rowspan=2, sticky="news")
        # Current chat name label
        self.__current_chat_name = Label(self, text="Home", height=2, font="bold",
                                         bg=self.__app_background_color, fg="white", justify="center")
        self.__current_chat_name.text = "Home"
        self.__current_chat_name.chat_id = None
        self.__current_chat_name.grid(row=0, column=2, columnspan=2, sticky="news")
        # Entry box for text
        self.__msg_box = Entry(self, width=121, bg=self.__app_background_color, fg="white", font=("helvetica", 16))
        self.__msg_box.bind('<KeyPress>', enter_key)
        self.__msg_box.grid(row=19, column=2, sticky='news')
        # Button to record audio
        photo = PhotoImage(file=resource_path("microphone.png"))
        self.__record_button = Button(self, image=photo, command=record_, bg=self.__app_background_color,
                                      height=68, width=140, fg="#63C8D8", text="Record")
        self.__record_button.grid(row=19, column=3, sticky='news')
        # Button to submit the input from the input box
        photo2 = PhotoImage(file=resource_path("send.png"))
        self.__send_msg = Button(self, image=photo2, width=40, height=3, bg=self.__app_background_color,
                                 fg="white", font=None,
                                 command=lambda: send_message(self.__current_chat_name, self.__msg_box.get()))
        self.__send_msg.grid(row=19, column=0, sticky='news')
        # Button to upload files
        photo3 = PhotoImage(file=resource_path("doc.png"))
        self.__file_upload = Button(self, image=photo3, bg=self.__app_background_color, height=1, width=1,
                                    command=lambda: upload_file(self.__current_chat_name))
        self.__file_upload.grid(row=19, column=1, sticky='news')
        # Create an input box to search a username and start chat with him
        self.__search_user = Entry(self, width=40, font=None)
        self.__search_user.bind('<Button-1>', search_delete_on_click)
        self.__search_user.bind('<KeyPress>', enter_key_search_user)
        self.__search_user.insert(END, "Start a new chat")
        self.__search_user.grid(row=0, column=0, sticky='news')
        # Create a button to submit the input from the input box
        self.__search_chat = Button(self, text="Search", width=8, height=1, bg=self.__app_background_color, fg="white",
                                    command=lambda: new_chat(search_user, self.__email), font=None)
        self.__search_chat.grid(row=0, column=1, sticky='news')
        # Home window
        self.__home_chat = Text(self, height=9999999, width=9999999,
                                bg=self.__app_background_color, state=DISABLED, font=('helvetica', '16'))
        self.__home_chat.grid(row=1, column=2, sticky='news', columnspan=2)

    def record_audio(self):
        if self.__current_chat_name.text != "Home":
            audio_gui = RecordingGUI(self.__email, self.__record_button,
                                     self.winfo_screenwidth(), self.winfo_screenheight(),
                                     upload_file, self.__current_chat_name)
            t = threading.Thread(target=audio_gui.record_audio)
            t.start()


def resource_path(relative_path):
    """ return the path to a resource """
    return os.path.join(os.path.abspath("."), relative_path)


gui = ChatEaseGUI("omerdagry@gmail.com")
gui.mainloop()
