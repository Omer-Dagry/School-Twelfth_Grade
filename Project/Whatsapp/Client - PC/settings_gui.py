import os
import logging

from typing import *
from tkinter import *
from tkinter import colorchooser


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


class SettingsGUI(Toplevel):
    def __init__(self, root: Tk | Toplevel, email: str, change_background: Callable):
        logging.info(f"[SettingsGUI]: initializing GUI")
        Toplevel.__init__(self, root)
        #
        self.__email = email
        self.__change_main_gui_background = change_background
        #
        self.__setup()

    def __setup(self):
        logging.info(f"[SettingsGUI]: setup")
        size = 120
        color = "#ffffd0"
        window_x = self.winfo_screenwidth() / 2
        window_y = self.winfo_screenheight() / 2
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)
        self.rowconfigure(1, weight=1)
        self.rowconfigure(2, weight=1)
        self.title("Settings")
        self.geometry("250x%d+%d+%d" % (size, window_x, window_y))
        self.minsize(250, size)
        self.maxsize(250, size)
        self.__change_background_button = Button(self, text="Change Background Color", bg=color, justify=CENTER,
                                                 command=self.__change_background)
        self.__change_background_button.grid(row=0, column=0, sticky="news")
        # TODO: add more settings

    def __change_background(self):
        color = colorchooser.askcolor()[1]
        if color is not None:
            logging.info(f"[SettingsGUI]: __change_background, user picked: '{color}'")
            self.__change_main_gui_background(color)  # call ChatEaseGUI __change_background_color function
            self.deiconify()  # put the settings GUI back to focus
