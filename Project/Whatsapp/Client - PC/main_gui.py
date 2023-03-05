import os
import logging
import threading
import tkinter
import traceback

from tkinter import *
# from PIL.ImageOps import contain
# from PIL import Image as ImagePIL
# from multiprocessing import Process
# from PIL import ImageTk as ImageTkPIL
from settings_gui import SettingsGUI
from recording_gui import RecordingGUI
from protocol_socket import EncryptedProtocolSocket
from communication import Communication as Com  # upload_file, send_message, new_chat


# Constants
# logging
LOG_DIR = 'log'
LOG_LEVEL = logging.DEBUG
LOG_FILE = LOG_DIR + "/ChatEase-Client.log"
LOG_FORMAT = "%(levelname)s | %(asctime)s | %(processName)s | %(threadName)s | %(message)s"

# Create All Needed Directories & Files & Initialize logging
os.makedirs(LOG_DIR, exist_ok=True)
if not os.path.isfile(LOG_FILE):
    with open(LOG_FILE, "w"):
        pass
logging.basicConfig(format=LOG_FORMAT, filename=LOG_FILE, level=LOG_LEVEL)


class ChatEaseGUI(Tk):
    def __init__(self, email: str, password: str, server_ip_port: tuple[str, int], sock: EncryptedProtocolSocket,
                 screen_name=None, base_name=None, class_name='Tk', use_tk=True, sync=False, use=None,
                 app_name: str = "ChatEase", window_min_size: tuple[int, int] = (980, 520),
                 app_background_color: str = "#1E1F22"):
        #
        logging.info(f"[ChatEaseGUI]: initializing GUI ({email})")
        super().__init__(screen_name, base_name, class_name, use_tk, sync, use)
        #
        self.__app_name = app_name
        self.__window_min_size = window_min_size
        self.__app_background_color = app_background_color
        #
        self.__email: str = email
        self.__password: str = password
        self.__server_ip_port: tuple[str, int] = server_ip_port
        self.__sock = sock
        self.__communication = Com(self.__email, self.__password, self.__server_ip_port)
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
        #
        self.__add_to_update_dict: dict[Tk, str] = {}
        self.__update_dict: dict[Tk, str] = {self: "ChatEaseGUI"}
        #
        self.__setup()

    def __change_background_color(self, bg: str):
        """ changes __app_background_color and destroys all widgets and calls __setup """
        logging.info(f"[ChatEaseGUI]: __change_background_color, bg = '{bg}' ({self.__email})")
        self.__app_background_color = bg
        for widget in self.winfo_children():
            widget.destroy()
        self.__setup()

    def mainloop(self, n: int = 0) -> None:
        """ Call the mainloop of Tk. """
        # logging.info(f"[ChatEaseGUI]: mainloop ({self.__email})")
        # super().mainloop(n)
        raise NotImplementedError("Please Call 'fake_mainloop' instead of 'mainloop'")

    def fake_mainloop(self):
        logging.info(f"[ChatEaseGUI]: fake_mainloop ({self.__email})")
        while self in self.__update_dict:
            remove = []
            # update all the GUIs
            for gui in self.__update_dict.keys():
                try:
                    if gui.winfo_exists():
                        gui.update()
                    else:
                        remove.append(gui)
                except tkinter.TclError:
                    remove.append(gui)
            for gui in remove:  # remove closed GUI's
                if self.__update_dict[gui] == "SettingsGUI":
                    self.__settings_button["state"] = NORMAL
                self.__update_dict.pop(gui)
            for gui, name in self.__add_to_update_dict.items():  # add new GUI's (can't during iteration)
                self.__update_dict[gui] = name
            self.__add_to_update_dict = {}

    def __enter_key(self, event=None):
        if event is not None and event.type == EventType.KeyPress and self.__current_chat_name.text != "Home":
            msg = self.__msg_box.get()
            self.__msg_box.delete(0, END)
            self.__communication.send_message(self.__current_chat_name.chat_id, msg, self.__sock)

    def __search_user_focus_in(self, event: Event = None):
        if event is not None and event.type == EventType.FocusIn:
            text = self.__search_user.get()
            if text == "Start a new chat":
                self.__search_user.delete(0, END)
                self.__search_user.insert(END, self.__search_user.last_search)

    def __search_user_focus_out(self, event: Event = None):
        if event is not None and event.type == EventType.FocusOut:
            text = self.__search_user.get()
            self.__search_user.last_search = text
            self.__search_user.delete(0, END)
            self.__search_user.insert(END, "Start a new chat")

    def __search_user_enter(self, event: Event = None):
        if event is not None and event.type == EventType.KeyPress:
            user = self.__search_user.get()
            self.__search_user.delete(0, END)
            self.__search_user_focus_out()
            self.__communication.new_chat(user, self.__sock)

    def __setup(self):
        logging.info(f"[ChatEaseGUI]: setup ({self.__email})")
        # Configure Window
        self.title(self.__app_name)  # title of window
        self.iconbitmap(resource_path("ChatEase.ico"))  # icon of window
        self.config(bg=self.__app_background_color)  # background color of window
        self.minsize(self.__window_min_size[0], self.__window_min_size[1])  # minimum size of window
        self.state("zoomed")  # open window in full-screen windowed
        self.columnconfigure(2, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        #
        # Container for all the chat buttons
        self.__chat_buttons = Text(self, background=self.__app_background_color, width=42, cursor="arrow", height=27)
        self.__chat_buttons.grid(row=1, column=0, columnspan=2, rowspan=2, sticky="news")
        # Current chat name label
        self.__current_chat_name = Label(self, text="Home", height=2, font="bold",
                                         bg=self.__app_background_color, fg="white", justify="center")
        self.__current_chat_name.text = "Home"
        self.__current_chat_name.chat_id = None
        self.__current_chat_name.grid(row=0, column=2, sticky="news")
        # Call button
        self.__call_photo = PhotoImage(file=resource_path("call.png"))
        self.__call_button = Button(
            self, text="Call", width=4, height=1, bg=self.__app_background_color,
            fg="white", font=None, image=self.__call_photo,
            command=lambda: self.__communication.make_call(self.__current_chat_name.chat_id)
        )
        self.__call_button.grid(row=0, column=3, sticky='news')
        # Settings button
        self.__settings_photo = PhotoImage(file=resource_path("setting.png"))
        self.__settings_button = Button(
            self, text="Settings", width=4, height=1, bg=self.__app_background_color,
            fg="white", font=None, image=self.__settings_photo, command=self.__settings
        )
        self.__settings_button.grid(row=0, column=4, sticky='news')
        # Entry box for text
        self.__msg_box = Entry(self, width=121, bg=self.__app_background_color, fg="white", font=("helvetica", 16))
        self.__msg_box.bind('<Return>', self.__enter_key)
        self.__msg_box.grid(row=19, column=2, sticky='news')
        # Button to record audio
        self.__record_photo = PhotoImage(file=resource_path("microphone.png"))
        self.__record_button = Button(self, image=self.__record_photo, command=self.__record_audio, height=68,
                                      width=140, bg=self.__app_background_color, fg="#63C8D8", text="Record")
        self.__record_button.grid(row=19, column=3, columnspan=2, sticky='news')
        # Button to submit the input from the input box
        self.__send_photo = PhotoImage(file=resource_path("send.png"))
        self.__send_msg = Button(
            self, image=self.__send_photo, width=40, height=3, bg=self.__app_background_color, fg="white", font=None,
            command=lambda: (
                self.__communication.send_message(
                    self.__current_chat_name.chat_id, self.__msg_box.get(), self.__sock
                ),
                self.__msg_box.delete(0, END)
            )
        )
        self.__send_msg.grid(row=19, column=0, sticky='news')
        # Button to upload files
        self.__upload_photo = PhotoImage(file=resource_path("doc.png"))
        self.__file_upload = Button(self, image=self.__upload_photo, bg=self.__app_background_color, height=1, width=1,
                                    command=lambda: self.__communication.upload_file(self.__current_chat_name.chat_id))
        self.__file_upload.grid(row=19, column=1, sticky='news')
        # Create an input box to search a username and start chat with him
        self.__search_user = Entry(self, width=40, font=None)
        self.__search_user.bind("<FocusIn>", self.__search_user_focus_in)
        self.__search_user.bind("<FocusOut>", self.__search_user_focus_out)
        self.__search_user.bind('<Return>', self.__search_user_enter)
        self.__search_user.insert(END, "Start a new chat")
        self.__search_user.last_search = ""
        self.__search_user.grid(row=0, column=0, sticky='news')
        # Create a button to submit the input from the input box
        self.__search_chat = Button(self, text="Search", width=8, height=1, bg=self.__app_background_color, fg="white",
                                    command=self.__search_user_enter, font=None)
        self.__search_chat.grid(row=0, column=1, sticky='news')
        # Home window
        self.__home_chat = Text(self, height=9999999, width=9999999,
                                bg=self.__app_background_color, state=DISABLED, font=('helvetica', '16'))
        self.__home_chat.grid(row=1, column=2, sticky='news', columnspan=3)

    def __record_audio(self):
        """ Opens a thread and calls record_audio of RecordingGUI """
        # TODO: uncomment the following line
        # if self.__current_chat_name.text != "Home":
        logging.info(f"[ChatEaseGUI]: record audio called, creating RecordingGUI instance ({self.__email})")
        audio_gui = RecordingGUI(
            self.__email, self.__record_button, self.winfo_screenwidth(), self.winfo_screenheight(),
            self.__communication.upload_file, str(self.__current_chat_name.chat_id), self.__record_audio
        )
        t = threading.Thread(target=audio_gui.record_audio, daemon=True, name="RecordingGUI")
        t.start()
        logging.info(f"[ChatEaseGUI]: opened a thread and called RecordingGUI.record_audio ({self.__email})")

    def __settings(self):
        if self.__settings_button["state"] == NORMAL:
            logging.info(f"[ChatEaseGUI]: creating SettingsGUI instance ({self.__email})")
            settings_gui = SettingsGUI(self.__email, self.__change_background_color)
            self.__add_to_update_dict[settings_gui] = "SettingsGUI"
            self.__settings_button["state"] = DISABLED
            logging.info(f"[ChatEaseGUI]: added SettingsGUI to fake_mainloop ({self.__email})")

    def __del__(self):
        self.quit()


def resource_path(relative_path):
    """ return the path to a resource """
    return os.path.join(os.path.abspath("."), relative_path)


def main():
    gui = ChatEaseGUI("omerdagry@gmail.com", "123", ("127.0.0.1", 8820), None)
    gui.fake_mainloop()


if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt):
        exc = traceback.format_exc()
        print(exc)
        logging.debug(f"Received exception: {exc}")
    logging.info("Program Ended")
