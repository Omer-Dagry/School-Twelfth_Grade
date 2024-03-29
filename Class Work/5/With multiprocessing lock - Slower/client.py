import datetime
import hashlib
import socket
import multiprocessing
import queue
import time
from typing import *


# Constants
IP = "127.0.0.1"
PORT = 8820
NUMBERS = "0123456789"
CPU_COUNT = multiprocessing.cpu_count()
LEN_OF_MD5_HASHED_DATA: int = 10

# Globals
multiprocessing_lock = multiprocessing.Lock()


def recv_full(sock: socket.socket, msg_len: int) -> str:
    """ Loop On recv Until Received msg_len bytes From The Server """
    sock.settimeout(2)
    data = ""
    res = None
    count = 0
    while len(data) != msg_len and res != "" and count != 10:
        try:
            res = sock.recv(msg_len - len(data)).decode()
        except (ConnectionAbortedError, ConnectionError, ConnectionResetError, socket.error) as err:
            if not isinstance(err, socket.error):
                sock.close()
                main()
                break
        if res is not None:
            data += res
        count += 1
        time.sleep(0.5)
    sock.settimeout(None)
    if res is None or res == "no work".rjust(20, " ") or res == "":
        print("Server Has No Work")
        exit()
    return data


def recv_range_and_hash_from_server(sock: socket.socket) -> tuple[int, int, str]:
    """ Receives The Range And MD5 hash From The Server """
    print("Trying To Receive Range From The Server")
    # get my range
    my_range = recv_full(sock, 20)  # start_from (10 digits) & end_at (10 digits)
    start_from = int(my_range[:10])
    end_at = int(my_range[10:])
    md5_hash = recv_full(sock, 32).lower()  # the md5 hash (32 digit)
    return start_from, end_at, md5_hash


def brute_force_decrypt_md5(md5_hash: str, base_string_length: int,
                            multiprocessing_queue: queue.Queue, number_of_checked_options: multiprocessing.Value,
                            start_from: str, end_at: str, current_string: str = "") -> Union[str, None]:
    """
    The Brute Force Function
    Recursive Function, Runs From start_from To end_at including both.
    Sends A Signal If The Result Is Found
    Sends A Signal If Finished Range And Didn't Found Result
    """
    # because this func runs in other processes the try except in the main process isn't
    # catching KeyboardInterrupt in these processes, so another try except is added here
    # so if the user closes the program it will exit without a bunch of errors
    try:
        global NUMBERS, multiprocessing_lock
        # start from
        numbers = NUMBERS[NUMBERS.index(start_from[0]):]
        for number in numbers:
            if base_string_length > 1:
                # after 1 run do all the numbers
                if numbers.index(number) != 0:
                    start_from = "0" * base_string_length
                res = brute_force_decrypt_md5(md5_hash, base_string_length - 1, multiprocessing_queue,
                                              number_of_checked_options,
                                              start_from[1:], end_at, current_string=current_string + number)
                if res is not None and "stop" in res and base_string_length != 10:
                    return res
                elif res is not None and "stop" in res:
                    multiprocessing_queue.put("not found, stopped at '%s'" % res.split("top, ")[1])
                    break
                elif res is not None and base_string_length != 10:
                    return res
                elif res is not None:
                    multiprocessing_queue.put(res)
                    break
            else:
                multiprocessing_lock.acquire()
                number_of_checked_options.value += 1
                multiprocessing_lock.release()
                current_string_ = current_string + number
                if hashlib.md5(current_string_.encode()).hexdigest().lower() == md5_hash.lower():
                    return current_string_
                if current_string_ == end_at:
                    return "stop, " + current_string_
        if base_string_length != 10:
            return None
    except KeyboardInterrupt:
        pass


def close_all_processes(processes: list[multiprocessing.Process]):
    """ Kills All The Processes That Were Created """
    for p_ in processes:
        if p_ is not multiprocessing.current_process():
            p_.kill()
    print("killed all processes")


def main():
    global multiprocessing_lock
    print("Trying To Connect To The Server...")
    # open socket to server
    sock = socket.socket()
    try:
        sock.connect((IP, PORT))
    except ConnectionRefusedError:
        print("Can't Reach The Server.")
        exit()
    print("Connected To Server.")
    # recv data
    start_from, end_at, md5_hash = recv_range_and_hash_from_server(sock)
    print("Server Sent: "
          "Start From:", str(start_from).rjust(10, "0"),
          "| End At:", str(end_at).rjust(10, "0"),
          "| MD5 Hash To Brute Force:", md5_hash)
    # ------------------ just for testing, skip until result in range ------------------
    # if not start_from < 3735928559 < end_at:
    #     msg = "not found.".rjust(32, " ").encode()
    #     sent_amount = sock.send(msg)
    #     while sent_amount != 32:
    #         sent_amount += sock.send(msg[sent_amount:])
    #     sock.close()
    #     main()
    # ----------------------------------------------------------------------------------
    total: int = end_at - start_from
    processes: list[multiprocessing.Process] = []
    # communication with processes
    multiprocessing_queue = multiprocessing.Queue()
    number_of_checked_options = multiprocessing.Value("i", 0)
    # open processes (the number of processes is the number of cores)
    # each process gets a portion of the range that the server has sent
    for i in range(CPU_COUNT):
        # if it is the last process the range will be up to end_at
        # if the range isn't dividable by the cpu_count we will miss some options
        # so this fixes that problem
        if i == CPU_COUNT - 1:
            p = multiprocessing.Process(target=brute_force_decrypt_md5,
                                        args=(md5_hash.lower(), LEN_OF_MD5_HASHED_DATA, multiprocessing_queue,
                                              number_of_checked_options,
                                              str(start_from).rjust(10, "0"),
                                              str(int(end_at)).rjust(10, "0")),
                                        daemon=True)
            p.start()
            processes.append(p)
            print("Process %d Range:" % (i + 1),
                  str(start_from).rjust(10, "0"), "-",
                  str(int(end_at)).rjust(10, "0"))
        # each process gets the same amount of options to go through
        else:
            p = multiprocessing.Process(target=brute_force_decrypt_md5,
                                        args=(md5_hash.lower(), LEN_OF_MD5_HASHED_DATA, multiprocessing_queue,
                                              number_of_checked_options,
                                              str(start_from).rjust(10, "0"),
                                              str(start_from + (total // CPU_COUNT) - 1).rjust(10, "0")),
                                        daemon=True)
            p.start()
            processes.append(p)
            print("Process %d Range:" % (i + 1),
                  str(start_from).rjust(10, "0"), "-",
                  str(start_from + (total // CPU_COUNT)).rjust(10, "0"))
            start_from += (total // CPU_COUNT)
    # wait for processes to finish
    # or until one of them will send the md5 message through the multiprocessing queue
    decrypted_md5_hash: Union[None, str] = None
    sock.settimeout(2)
    res = b""
    at_least_one_process_finished: bool = False
    last_check_in = datetime.datetime.now()
    while processes and decrypted_md5_hash is None:
        # send the server the amount of options that were checked since the last time we sent
        if (datetime.datetime.now() - last_check_in).seconds >= 5:
            try:
                multiprocessing_lock.acquire()
                msg = ("checked '%d' more" % number_of_checked_options.value).rjust(32, " ").encode()
                sent_amount = sock.send(msg)
                while sent_amount != 32:
                    sent_amount += sock.send(msg[sent_amount:])
                number_of_checked_options.value = 0
                multiprocessing_lock.release()
                last_check_in = datetime.datetime.now()
            except (ConnectionAbortedError, ConnectionError, ConnectionResetError):
                print("Lost Connection To Server. Exiting.")
                close_all_processes(processes)
                exit()
        # loop on all active processes
        for p in processes:
            # check if server sent stop msg
            try:
                res = sock.recv(4)
            except (ConnectionAbortedError, ConnectionError, ConnectionResetError, socket.error) as err:
                if not isinstance(err, socket.error):
                    print("Lost Connection To Server. Exiting.")
                    close_all_processes(processes)
                    exit()
            if res == b"stop":
                close_all_processes(processes)
                sock.close()
                exit()
            # check if there is a process that finished
            if not p.is_alive() and decrypted_md5_hash is None:
                at_least_one_process_finished = True
                try:
                    # check if the process sent the result or sent not found msg
                    decrypted_md5_hash = multiprocessing_queue.get(timeout=5)
                    if decrypted_md5_hash is not None and "not found" in decrypted_md5_hash:
                        print("Process Finished And Returned: Not Found.")
                        decrypted_md5_hash = None
                    else:
                        print("\n\n" + "-" * 64)
                        print("Process Finished And Found The Hashed Data:", decrypted_md5_hash)
                        print("-" * 64 + "\n\n")
                        # got result close all other processes
                        close_all_processes(processes)
                except queue.Empty:
                    pass
                processes.remove(p)
    # sent result to server if found
    # else tell server that the range doesn't contain the result and
    # close connection to server and start again (a new range will be given)
    if decrypted_md5_hash is not None and at_least_one_process_finished:
        try:
            msg = decrypted_md5_hash.rjust(32, " ").encode()
            sent_amount = sock.send(msg)
            while sent_amount != 32:
                sent_amount += sock.send(msg[sent_amount:])
            sock.close()
            print("MD5 Hash Result Sent To Server.")
        except (ConnectionAbortedError, ConnectionError, ConnectionResetError, socket.error):
            print("Couldn't Send Result To Server. Connection Error")
        exit()
    elif at_least_one_process_finished:
        print("Didn't Found Result In Range.")
        try:
            msg = "not found.".rjust(32, " ").encode()
            sent_amount = sock.send(msg)
            while sent_amount != 32:
                sent_amount += sock.send(msg[sent_amount:])
            sock.close()
        except (ConnectionAbortedError, ConnectionError, ConnectionResetError, socket.error):
            print("Couldn't Send not found To Server. Connection Error")
            exit()
        print("-" * 64)
        print("Starting Again.")
        try:
            main()
        except ConnectionError as err:
            print(str(err))
    else:
        sock.close()


if __name__ == '__main__':
    try:
        main()
    except (ConnectionError, KeyboardInterrupt) as e:
        if isinstance(e, KeyboardInterrupt):
            print("\nReceived KeyboardInterrupt")
        else:
            print(str(e))
