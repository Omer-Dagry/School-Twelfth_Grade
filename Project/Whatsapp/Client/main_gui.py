import socket
import time
import sys

from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QApplication, QMainWindow
from typing import *
from communication import send_file, send_message, sync_with_server
# from emoji_window import
# from new_group_window import


# Globals
msg_row_height: int = 40
status_row_height: int = 30


class MainGUI:
    def __init__(self, sock: socket.socket, user_password: str, server_ip: str, server_port: int):
        # socket to server, for regular communication
        self.user_password = user_password
        self.sock = sock
        self.server_ip = server_ip
        self.server_port = server_port
        # constants
        self.bg_color: str = "white"
        self.bg_color_chats: str = "#e9ebf0"
        self.bg_color_buttons: str = "#e9ebf0"
        self.bg_color_input_boxes: str = "#d3d7de"
        # create app and window
        self.app = QApplication(sys.argv)
        self.win = QMainWindow()
        self.window_size: tuple[int, int] = (1000, 600)
        self.window_location: tuple[int, int] = (
            (self.app.screens()[0].size().width() // 2) - self.window_size[0] // 2,
            (self.app.screens()[0].size().height() // 2) - self.window_size[1] // 2
        )
        # create worker (sync thread)
        self.worker: Union[None, WorkerThread] = None
        # list of chat buttons
        self.chat_buttons: list[QtWidgets.QPushButton] = []
        # create grid
        self.widget = QtWidgets.QWidget(self.win)
        self.grid = QtWidgets.QGridLayout(self.widget)
        # basic buttons, chats list, chat, inputs
        self.search_user_button = QtWidgets.QPushButton("Search", self.widget)
        self.search_user_box = QtWidgets.QLineEdit("", self.widget)
        self.new_chat_button = QtWidgets.QPushButton("New", self.widget)
        self.current_chat_label = QtWidgets.QLabel("Home", self.widget)
        self.chats_list = QtWidgets.QListWidget(self.widget)
        self.chat = QtWidgets.QTextEdit(self.widget)
        self.voice_msg_button = QtWidgets.QPushButton("Voice Msg", self.widget)
        self.upload_file_button = QtWidgets.QPushButton("Upload File", self.widget)
        self.emoji_button = QtWidgets.QPushButton("emoji", self.widget)
        self.input_box = QtWidgets.QTextEdit("Type Something", self.widget)
        self.send_button = QtWidgets.QPushButton("Send", self.widget)
        # set GUI structure
        self.set_gui_structure()

    def set_gui_structure(self):
        # set some settings for the GUI window
        self.win.setWindowTitle("Whatsapp")
        self.win.setMinimumSize(300, 300)
        # set starting size and location
        self.win.setGeometry(self.window_location[0], self.window_location[1],
                             self.window_size[0], self.window_size[1])
        # --------------- grid layout settings ---------------
        self.widget.setStyleSheet("background-color:" + self.bg_color)
        self.win.setCentralWidget(self.widget)
        self.grid.setSpacing(0)
        self.grid.setContentsMargins(0, 0, 0, 0)
        # --------------- add widgets ---------------
        # search user button
        self.search_user_button.setStyleSheet("background-color:" + self.bg_color_buttons)
        self.search_user_button.setMaximumWidth(100)
        self.search_user_button.setFixedHeight(status_row_height)
        self.grid.addWidget(self.search_user_button, 0, 0)
        # search user box
        self.search_user_box.setStyleSheet("background-color:" + self.bg_color_input_boxes)
        self.search_user_box.setFixedSize(220, status_row_height)
        self.grid.addWidget(self.search_user_box, 0, 1)
        # new chat button
        self.new_chat_button.setStyleSheet("background-color:" + self.bg_color_buttons)
        self.new_chat_button.setMaximumWidth(100)
        self.new_chat_button.setFixedHeight(status_row_height)
        self.grid.addWidget(self.new_chat_button, 0, 2)
        # current chat title
        self.current_chat_label.setStyleSheet("background-color:" + self.bg_color_buttons)
        self.current_chat_label.setAlignment(QtCore.Qt.AlignCenter)
        self.current_chat_label.setFixedHeight(status_row_height)
        self.grid.addWidget(self.current_chat_label, 0, 3, 1, 5)
        # chats list
        self.chats_list.setStyleSheet("background-color:" + self.bg_color_chats)
        self.grid.addWidget(self.chats_list, 1, 0, 2, 3)
        # chat
        self.chat.setStyleSheet("background-color:" + self.bg_color_chats)
        self.grid.addWidget(self.chat, 1, 3, 1, 5)
        # record voice msg button
        self.voice_msg_button.setStyleSheet("background-color:" + self.bg_color_buttons)
        self.voice_msg_button.setFixedHeight(msg_row_height)
        self.grid.addWidget(self.voice_msg_button, 2, 3)
        # upload file button
        self.upload_file_button.setStyleSheet("background-color:" + self.bg_color_buttons)
        self.upload_file_button.setFixedHeight(msg_row_height)
        self.grid.addWidget(self.upload_file_button, 2, 4)
        # emoji button
        self.emoji_button.setStyleSheet("background-color:" + self.bg_color_buttons)
        self.emoji_button.setFixedHeight(msg_row_height)
        self.grid.addWidget(self.emoji_button, 2, 5)
        # input box
        self.input_box.setStyleSheet("background-color:" + self.bg_color_input_boxes)
        self.input_box.setFixedHeight(msg_row_height)
        self.grid.addWidget(self.input_box, 2, 6)
        # send button
        self.send_button.setStyleSheet("background-color:" + self.bg_color_buttons)
        self.send_button.setFixedHeight(msg_row_height)
        self.send_button.setMaximumWidth(100)
        self.grid.addWidget(self.send_button, 2, 7)

    def link_buttons(self):
        # TODO link all the buttons to there actions
        pass

    def launch(self, sync_sock: socket.socket):
        # launch the app
        self.sync_(sync_sock)
        self.win.show()
        sys.exit(self.app.exec_())

    def sync_(self, sync_sock: socket.socket):
        """ connects the worker thread to the update_gui function """
        # sync socket, is a different socket from the regular socket,
        # it will be used **only** to sync
        self.worker = WorkerThread(sync_sock, self.user_password)
        self.worker.start()
        # self.worker.my_signal[()].connect(self.update)
        self.worker.my_signal.connect(self.update_gui)

    def update_gui(self, new_data: bool):
        """ updates the GUI if there is new data """
        # TODO finish the update GUI function
        if new_data:
            pass


class WorkerThread(QtCore.QThread):
    """ QThread class for syncing in the background """
    my_signal = pyqtSignal(bool)

    def __init__(self, sync_sock: socket.socket, user_password: str):
        super(WorkerThread, self).__init__()
        self.sync_sock = sync_sock
        self.user_password = user_password

    def run(self):
        """ syncs with the server
        if new data received emits True
        else emits False
        """
        new_data = sync_with_server(self.sync_sock, self.user_password, first_time_all=True)
        self.my_signal.emit(new_data)
        while True:
            time.sleep(2)
            new_data = sync_with_server(self.sync_sock, self.user_password)
            self.my_signal.emit(new_data)
