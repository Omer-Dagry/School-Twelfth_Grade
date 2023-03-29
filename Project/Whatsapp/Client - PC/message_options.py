import os
import logging

from tkinter import *
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
    def __init__(self, root: Tk | Toplevel, email: str, password: str, server_ip_port: tuple[str, int],
                 message_index: int) -> None:
        logging.info(f"[MessageOptions]: init ({email})")
        super().__init__(root)
        self.__email = email
        self.__password = password
        self.__message_index = message_index
        self.__communication = Com(email, password, server_ip_port)
        self.__setup()

    def __setup(self) -> None:
        logging.info(f"[MessageOptions]: setup ({self.__email})")
        #
        # TODO: add buttons: delete for me, delete for everyone, copy

