"""
###############################################
Author: Omer Dagry
Mail: omerdagry@gmail.com
Date: 30/05/2023 (dd/mm/yyyy)
###############################################
"""
import sys
import time
import server
import datetime
import threading
import multiprocessing

from tkinter import *
from importlib import reload
from multiprocessing.managers import DictProxy, SyncManager


# Globals
server_console: Text | None = None
blocked_ips_text: Text | None = None
print_queue = multiprocessing.Queue()
online_clients_text: Text | None = None
server_process: multiprocessing.Process | None = None
online_clients: DictProxy | None | dict[str, None] = None
blocked_ips: DictProxy | None | dict[str, datetime.datetime] = None


def start_server(start_stop_server_btn: Button):
    """ Starts the server """
    global server_process
    if server_process is None:
        online_clients.clear()
        blocked_ips.clear()
        server_process = multiprocessing.Process(
            target=server.start, args=(online_clients, blocked_ips, print_queue)
        )
        server_process.start()
        start_stop_server_btn.configure(text="Stop Server", command=lambda: stop_server(start_stop_server_btn))


def stop_server(start_stop_server_btn: Button):
    """ Stops the server """
    global server_process
    if server_process is not None:
        server_process.kill()
        start_stop_server_btn.configure(text="Start Server", command=lambda: start_server(start_stop_server_btn))
        #
        server_console.configure(state=NORMAL)
        server_console.delete("1.0", END)
        server_console.configure(state=DISABLED)
        #
        online_clients_text.configure(state=NORMAL)
        online_clients_text.delete("1.0", END)
        online_clients_text.configure(state=DISABLED)
        #
        blocked_ips_text.configure(state=NORMAL)
        blocked_ips_text.delete("1.0", END)
        blocked_ips_text.configure(state=DISABLED)
    server_process = None


def reload_server_and_start_again(start_stop_server_btn: Button):
    """ Stops the server, reloads the import of the server.py, starts the updated server """
    stop_server(start_stop_server_btn)
    reload(server)
    start_server(start_stop_server_btn)


def start_gui():
    """ initializes the server GUI and enters the mainloop """
    global server_console, online_clients_text, blocked_ips_text
    root = Tk()
    # root configuration
    root.title("Server GUI")
    root.iconbitmap("favicon.ico")
    root.minsize(600, 400)
    root.geometry("1400x600")
    root.configure(bg="black")
    root.columnconfigure((0, 1), minsize=100, weight=2)
    root.columnconfigure((2, 3), minsize=50, weight=1)
    root.rowconfigure(1, weight=1)
    root.rowconfigure(2, weight=3)
    #
    start_stop_server_btn = Button(root, text="Start Server", width=10, bg="black", fg="white",
                                   command=lambda: start_server(start_stop_server_btn))
    start_stop_server_btn.grid(row=0, column=0, sticky="news")
    reload_server_btn = Button(root, text="Reload Server", width=12, bg="black", fg="white",
                               command=lambda: reload_server_and_start_again(start_stop_server_btn))
    reload_server_btn.grid(row=0, column=1, sticky="news")
    server_console = Text(root, bg="black", fg="white", width=200, height=99999999)
    server_console.grid(row=1, column=0, columnspan=2, sticky="news")
    server_console.configure(state=DISABLED)
    server_console.tag_configure("red", foreground="red")
    #
    online_clients_label = Label(root, text="Online Users", bg="black", fg="white")
    online_clients_label.grid(row=0, column=2, sticky="news")
    online_clients_text = Text(root, bg="black", fg="white", height=99999999)
    online_clients_text.grid(row=1, column=2, sticky="news")
    online_clients_text.configure(state=DISABLED)
    blocked_ips_label = Label(root, text="Blocked IPs", bg="black", fg="white")
    blocked_ips_label.grid(row=0, column=3, sticky="news")
    blocked_ips_text = Text(root, bg="black", fg="white", height=99999999)
    blocked_ips_text.grid(row=1, column=3, sticky="news")
    blocked_ips_text.configure(state=DISABLED)
    #
    threading.Thread(target=update_server_console, daemon=True).start()
    threading.Thread(target=update_online_users, daemon=True).start()
    threading.Thread(target=update_blocked_ips, daemon=True).start()
    #
    root.mainloop()


def update_server_console() -> None:
    """ print queue """
    while True:
        std_out_or_err, data = print_queue.get()  # blocking action
        server_console.configure(state=NORMAL)
        if std_out_or_err == "stdout":
            server_console.insert(END, data)
        else:
            server_console.insert(END, data, "red")
        server_console.configure(state=DISABLED)


def update_online_users() -> None:
    """ updates the online clients from shared memory online_clients dict every 5 seconds """
    while True:
        online_clients_text.configure(state=NORMAL)
        online_clients_text.delete("1.0", END)
        online_clients_text.insert(END, "\n".join(list(online_clients.keys())))
        online_clients_text.configure(state=DISABLED)
        time.sleep(5)


def update_blocked_ips() -> None:
    """ updates the blocked IPs from shared memory blocked_ips dict every 10 seconds """
    while True:
        blocked_ips_text.configure(state=NORMAL)
        blocked_ips_text.delete("1.0", END)
        blocked_ips_text.insert(END, "\n".join(list(blocked_ips.keys())))
        blocked_ips_text.configure(state=DISABLED)
        time.sleep(10)


def main():
    global online_clients, blocked_ips
    #

    class STDRedirect:
        def __init__(self, std_type):
            assert std_type == "stdout" or std_type == "stderr"
            self.std_type = std_type

        def write(self, data):
            print_queue.put((self.std_type, data))

    sys.stdout = STDRedirect("stdout")
    sys.stderr = STDRedirect("stderr")
    # create a shared dict for online clients and blocked IPs and then start the GUI
    with multiprocessing.Manager() as manager:  # type: SyncManager
        online_clients = manager.dict()
        blocked_ips = manager.dict()
        start_gui()
    if server_process is not None:  # if server still running when GUI closed, close it
        server_process.kill()


if __name__ == '__main__':
    main()
