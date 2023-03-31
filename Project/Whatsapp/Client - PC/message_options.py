import os
import logging

from tkinter import *
from typing import Literal
from tkinter.scrolledtext import ScrolledText
from communication import Communication as Com


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


class MessageOptions(Toplevel):
    def __init__(self, root: Tk | Toplevel, email: str, password: str,
                 server_ip_port: tuple[str, int], msg: str, message_index: int,
                 message_type: Literal["mine", "other"], seen_by: list[str], chat_id: str) -> None:
        logging.info(f"[MessageOptions]: initializing")
        super().__init__(root)
        #
        self.__msg = msg
        self.__email = email
        self.__chat_id = chat_id
        self.__seen_by = seen_by
        self.__password = password
        self.__message_type = message_type
        self.__message_index = message_index
        self.__server_ip_port = server_ip_port
        #
        self.__communication_ = None
        self.__setup()

    @property
    def __communication(self) -> Com:
        """
            The purpose of the function is to open a connection
            to the server only if the client choose an options that
            requires to communicate with the server
        """
        if self.__communication_ is None:
            self.__communication_ = Com(self.__email, self.__password, self.__server_ip_port)
        return self.__communication_

    def copy2clipboard(self):
        self.clipboard_clear()
        self.clipboard_append(self.__msg)
        self.update()

    def __setup(self) -> None:
        logging.info(f"[MessageOptions]: setup")
        #
        for widget in self.winfo_children():
            widget.destroy()
        #
        width = 250
        height = 120
        location_x = self.winfo_pointerx() - 250 // 2
        location_y = self.winfo_pointery() - 120 // 2
        color = "#ffffd0" if self.__message_type == "mine" else "#d0ffff"
        self.maxsize(width, height)
        self.minsize(width, height)
        self.geometry(f"{width}x{height}+{location_x}+{location_y}")
        #
        copy = Button(self, text="Copy", bg=color, command=self.copy2clipboard, width=21)
        copy.grid(row=0, column=0, sticky="news")
        #
        delete_for_me = Button(self, text="Delete For Me", bg=color,
                               command=lambda: self.__communication.delete_message_for_me(
                                   self.__chat_id, self.__message_index, self))
        delete_for_me.grid(row=1, column=0, sticky="news")
        #
        delete_for_everyone = Button(self, text="Delete For Everyone", bg=color,
                                     command=lambda: self.__communication.delete_message_for_everyone(
                                         self.__chat_id, self.__message_index, self))
        delete_for_everyone.grid(row=2, column=0, sticky="news")
        #
        seen_by = Button(self, text="Seen By", bg=color, command=self.__setup_seen_by, width=21)
        seen_by.grid(row=3, column=0, sticky="news")
        #
        logging.info(f"[MessageOptions]: setup done")

    def __setup_seen_by(self):
        logging.info(f"[MessageOptions]: setup seen_by")
        #
        width = 250
        height = 250
        self.maxsize(width, height)
        self.minsize(width, height)
        #
        for widget in self.winfo_children():
            widget.destroy()
        #
        back = Button(self, text="Back", command=self.__setup)
        back.place(x=0, y=0)
        #
        seen_by_label = Label(self, text="Seen", anchor=CENTER, height=2)
        seen_by_label.pack(fill=X)
        #
        seen_by_list = ScrolledText(self, font=('helvetica', '16'))
        for i in range(len(self.__seen_by)):
            user_label = Label(self, text=self.__seen_by[i], bg="#d0ffff")
            seen_by_list.window_create(END, window=user_label)
            if i < len(self.__seen_by) - 1:
                seen_by_list.insert(END, "\r\n")
        seen_by_list.pack()
        #
        seen_by_label.lift()
        back.lift()
        #
        logging.info(f"[MessageOptions]: setup seen_by done")
