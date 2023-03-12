import os
import logging
import threading
import traceback

from tkinter import *
# from PIL.ImageOps import contain
# from PIL import Image as ImagePIL
# from multiprocessing import Process
# from PIL import ImageTk as ImageTkPIL
from settings_gui import SettingsGUI
from recording_gui import RecordingGUI
from communication import Communication as Com
from photo_tools import format_photo, check_size
from protocol_socket import EncryptedProtocolSocket


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
                 app_background_color: str = "#1E1F22") -> None:
        #
        logging.info(f"[ChatEaseGUI]: initializing GUI ({email})")
        super().__init__(screen_name, base_name, class_name, use_tk, sync, use)
        #
        self.__app_name = app_name
        self.__window_min_size = window_min_size
        self.__app_background_color = app_background_color
        #
        self.__sock = sock
        self.__email: str = email
        self.__password: str = password
        self.__server_ip_port: tuple[str, int] = server_ip_port
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
        self.__profile_picture: Label | None = None
        self.__current_chat_name: Label | None = None
        #
        self.__call_photo: PhotoImage | None = None
        self.__send_photo: PhotoImage | None = None
        self.__upload_photo: PhotoImage | None = None
        self.__record_photo: PhotoImage | None = None
        self.__settings_photo: PhotoImage | None = None
        self.__profile_picture_photo: PhotoImage | None = None
        #
        self.setting_gui: SettingsGUI | None = None
        self.__add_to_update_dict: dict[Tk, str] = {}
        self.__update_dict: dict[Tk, str] = {self: "ChatEaseGUI"}
        #
        self.__setup()

    def __change_background_color(self, bg: str) -> None:
        """ changes __app_background_color and destroys all widgets and calls __setup """
        logging.info(f"[ChatEaseGUI]: __change_background_color, bg = '{bg}' ({self.__email})")
        self.__app_background_color = bg
        top_levels = self.get_top_levels(self)
        for widget in self.winfo_children():
            if widget not in top_levels:
                widget.destroy()
        self.__setup()

    def get_top_levels(self, root: Tk | Toplevel) -> list[Toplevel]:
        top = []
        for k, v in root.children.items():
            if isinstance(v, Toplevel):
                top.append(v)
                return top + self.get_top_levels(v)
        return []

    def __enter_key(self, event=None) -> None:
        if event is not None and event.type == EventType.KeyPress and self.__current_chat_name.text != "Home":
            msg = self.__msg_box.get()
            self.__msg_box.delete(0, END)
            self.__communication.send_message(self.__current_chat_name.chat_id, msg, self.__sock)

    def __search_user_focus_in(self, event: Event = None) -> None:
        if event is not None and event.type == EventType.FocusIn:
            text = self.__search_user.get()
            if text == "Start a new chat":
                self.__search_user.delete(0, END)
                self.__search_user.insert(END, self.__search_user.last_search)

    def __search_user_focus_out(self, event: Event = None) -> None:
        if event is not None and event.type == EventType.FocusOut:
            text = self.__search_user.get()
            self.__search_user.last_search = text
            self.__search_user.delete(0, END)
            self.__search_user.insert(END, "Start a new chat")

    def __search_user_enter(self, event: Event = None) -> None:
        if event is not None and event.type == EventType.KeyPress:
            user = self.__search_user.get()
            self.__search_user.delete(0, END)
            self.__search_user_focus_out()
            self.__communication.new_chat(user, self.__sock)

    def __setup(self) -> None:
        logging.info(f"[ChatEaseGUI]: setup ({self.__email})")
        # Configure Window
        self.title(self.__app_name)  # title of window
        self.iconbitmap(resource_path("images\\ChatEase.ico"))  # icon of window
        self.config(bg=self.__app_background_color)  # background color of window
        self.minsize(self.__window_min_size[0], self.__window_min_size[1])  # minimum size of window
        self.state("zoomed")  # open window in full-screen windowed
        self.columnconfigure(3, weight=1)
        self.rowconfigure(1, weight=1)

        # --------------------------- ROW 0 ---------------------------

        # Create an input box to search a username and start chat with him
        self.__search_user = Entry(self, width=40, font=None)
        self.__search_user.bind("<FocusIn>", self.__search_user_focus_in)
        self.__search_user.bind("<FocusOut>", self.__search_user_focus_out)
        self.__search_user.bind('<Return>', self.__search_user_enter)
        self.__search_user.insert(END, "Start a new chat")
        self.__search_user.last_search = ""
        self.__search_user.grid(row=0, column=0, sticky='news')

        # Create a button to submit the input from the input box
        self.__search_chat = Button(self, text="Search", width=8, height=4, bg=self.__app_background_color, fg="white",
                                    command=self.__search_user_enter, font=None, cursor="hand2")
        self.__search_chat.grid(row=0, column=1, sticky='news')

        # Profile Picture (of current chat, if 'home chat' your profile picture)
        format_photo(resource_path(f"{self.__email}\\{self.__email}_profile_picture.png"))
        self.__profile_picture_photo = PhotoImage(
            file=resource_path(f"{self.__email}\\{self.__email}_profile_picture.png"))
        self.__profile_picture = Label(self, image=self.__profile_picture_photo, justify="center", fg="orange",
                                       bg=self.__app_background_color, borderwidth=2, relief="groove")
        self.__profile_picture.grid(row=0, column=2, sticky='news')

        # Current chat name label
        self.__current_chat_name = Label(self, text="Home", font="bold",
                                         bg=self.__app_background_color, fg="white", justify="center")
        self.__current_chat_name.text = "Home"
        self.__current_chat_name.chat_id = None
        self.__current_chat_name.grid(row=0, column=3, sticky="news")

        # Call button
        self.__call_photo = PhotoImage(file=resource_path("images\\call.png"))
        self.__call_button = Button(
            self, text="Call", width=4, bg=self.__app_background_color,
            fg="white", font=None, image=self.__call_photo, cursor="hand2",
            command=lambda: self.__communication.make_call(self.__current_chat_name.chat_id)
        )
        self.__call_button.grid(row=0, column=4, sticky='news')

        # Settings button
        self.__settings_photo = PhotoImage(file=resource_path("images\\setting.png"))
        self.__settings_button = Button(
            self, text="Settings", width=4, height=1, bg=self.__app_background_color, cursor="hand2",
            fg="white", font=None, image=self.__settings_photo, command=self.__settings
        )
        self.__settings_button.grid(row=0, column=5, sticky='news')

        # --------------------------- ROW 1 ---------------------------

        # Container for all the chat buttons
        self.__chat_buttons = Text(self, background=self.__app_background_color, width=42,
                                   cursor="hand2", height=27, state=DISABLED)
        self.__chat_buttons.grid(row=1, column=0, columnspan=2, sticky="news")

        # Home window
        self.__home_chat = Text(self, height=9999999, width=9999999, cursor="arrow",
                                bg=self.__app_background_color, state=DISABLED, font=('helvetica', '16'))
        self.__home_chat.grid(row=1, column=2, sticky='news', columnspan=4)

        # --------------------------- ROW 2 ---------------------------

        # Button to submit the input from the input box
        self.__send_photo = PhotoImage(file=resource_path("images\\send.png"))
        self.__send_msg = Button(
            self, image=self.__send_photo, width=40, height=3, bg=self.__app_background_color, fg="white", font=None,
            command=lambda: (
                self.__communication.send_message(
                    self.__current_chat_name.chat_id, self.__msg_box.get(), self.__sock
                ),
                self.__msg_box.delete(0, END)
            ), cursor="hand2"
        )
        self.__send_msg.grid(row=2, column=0, sticky='news')

        # Button to upload files
        self.__upload_photo = PhotoImage(file=resource_path("images\\doc.png"))
        self.__file_upload = Button(self, image=self.__upload_photo, bg=self.__app_background_color, height=1, width=1,
                                    command=lambda: self.__communication.upload_file(self.__current_chat_name.chat_id),
                                    cursor="hand2")
        self.__file_upload.grid(row=2, column=1, sticky='news')

        # Entry box for text
        self.__msg_box = Entry(self, width=121, bg=self.__app_background_color, fg="white", font=("helvetica", 16))
        self.__msg_box.bind('<Return>', self.__enter_key)
        self.__msg_box.grid(row=2, column=2, columnspan=2, sticky='news')

        # Button to record audio
        self.__record_photo = PhotoImage(file=resource_path("images\\microphone.png"))
        self.__record_button = Button(self, image=self.__record_photo, command=self.__record_audio, height=68,
                                      width=140, bg=self.__app_background_color, fg="#63C8D8", text="Record",
                                      cursor="hand2")
        self.__record_button.grid(row=2, column=4, columnspan=2, sticky='news')

    def update(self) -> None:
        """ update the current open chat in the GUI (load the new msgs, don't recreate everything) """
        # TODO: finish
        raise NotImplementedError

    def load_chat(self, chat_id: str) -> None:
        """ loads 2 files of msgs of the chat (1600 msgs) """
        # TODO: finish
        raise NotImplementedError

    def load_more_messages(self, chat_id: str) -> None:
        """ loads more messages in the current chat (from another file of msgs - 800 more msgs) """
        # TODO: finish
        raise NotImplementedError

    def __record_audio(self) -> None:
        """ Opens a thread and calls record_audio of RecordingGUI """
        # TODO: uncomment the following line
        # if self.__current_chat_name.text != "Home":
        logging.info(f"[ChatEaseGUI]: record audio called, creating RecordingGUI instance ({self.__email})")
        audio_gui = RecordingGUI(
            self, self.__email, self.__record_button, self.winfo_screenwidth(), self.winfo_screenheight(),
            self.__communication.upload_file, str(self.__current_chat_name.chat_id), self.__record_audio
        )
        t = threading.Thread(target=audio_gui.record_audio, daemon=True, name="RecordingGUI")
        t.start()
        logging.info(f"[ChatEaseGUI]: opened a thread and called RecordingGUI.record_audio ({self.__email})")

    def __settings(self) -> None:
        top_levels = [isinstance(v, SettingsGUI) for v in self.get_top_levels(self)]
        if not all(top_levels) or not top_levels:  # check that there isn't already an open setting menu
            logging.info(f"[ChatEaseGUI]: creating SettingsGUI instance ({self.__email})")
            self.setting_gui = SettingsGUI(self, self.__email, self.__change_background_color)
        else:  # if there is a settings gui, bring it back to focus
            self.setting_gui.deiconify()

    def __del__(self) -> None:
        self.quit()


def resource_path(relative_path) -> str:
    """ return the path to a resource """
    return os.path.join(os.path.abspath("."), relative_path)


def main():
    gui = ChatEaseGUI("omerdagry@gmail.com", "123", ("127.0.0.1", 8820), EncryptedProtocolSocket())
    gui.mainloop()


if __name__ == '__main__':
    try:
        main()
    except (Exception, KeyboardInterrupt):
        exc = traceback.format_exc()
        print(exc)
        logging.debug(f"Received exception: {exc}")
    logging.info("Program Ended")
