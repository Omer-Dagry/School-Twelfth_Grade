import hashlib
import socket
import multiprocessing
import queue
from typing import *


IP = "127.0.0.1"
PORT = 8820
PACKET_LEN = 32
NUMBERS = "0123456789"
CPU_COUNT = multiprocessing.cpu_count()
LEN_OF_MD5_HASHED_DATA = 10


def brute_force_decrypt_md5(md5_hash: str, base_string_length: int, multiprocessing_queue: queue.Queue,
                            start_from: str, end_at: str, current_string: str = "") -> Union[str, None]:
    global NUMBERS
    # start from
    numbers = NUMBERS[NUMBERS.index(start_from[0]):]
    for number in numbers:
        if base_string_length > 1:
            # after 1 run do all the numbers
            if numbers.index(number) != 0:
                start_from = "0" * base_string_length
            res = brute_force_decrypt_md5(md5_hash, base_string_length - 1, multiprocessing_queue,
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
            current_string_ = current_string + number
            if hashlib.md5(current_string_.encode()).hexdigest().lower() == md5_hash.lower():
                return current_string_
            if current_string_ == end_at:
                return "stop, " + current_string_
    if base_string_length != 10:
        return None


# EC9C0F7EDCC18A98B1F31853B1813301
# 3735928559
def main():
    # # open socket to server
    # sock = socket.socket()
    # sock.connect((IP, PORT))
    # # get my range
    # my_range = sock.recv(20).decode()  # start from (10 digits) & end at (10 digits)
    # start_from = int(my_range[:10])
    # end_at = int(my_range[10:])
    # total = end_at - start_from
    # # get md5 hash to brute force
    # md5_hash = sock.recv(32).decode().lower()  # the md5 hash (32 digit)
    start_from = 0
    end_at = 9999999999
    total = end_at - start_from
    md5_hash = "EC9C0F7EDCC18A98B1F31853B1813301".lower()
    processes = []
    # communication
    multiprocessing_queue = multiprocessing.Queue()
    # open number of cores in the PC processes
    for i in range(CPU_COUNT):
        if i == CPU_COUNT - 1:
            p = multiprocessing.Process(target=brute_force_decrypt_md5,
                                        args=(md5_hash.lower(), LEN_OF_MD5_HASHED_DATA, multiprocessing_queue,
                                              str(start_from).rjust(10, "0"),
                                              str(int(end_at)).rjust(10, "0")),
                                        daemon=True)
            p.start()
            processes.append(p)
            print("Thread %d Range:" % (i + 1),
                  str(start_from).rjust(10, "0"), "-",
                  str(int(end_at)).rjust(10, "0"))
        else:
            p = multiprocessing.Process(target=brute_force_decrypt_md5,
                                        args=(md5_hash.lower(), LEN_OF_MD5_HASHED_DATA, multiprocessing_queue,
                                              str(start_from).rjust(10, "0"),
                                              str(start_from + (total // CPU_COUNT)).rjust(10, "0")),
                                        daemon=True)
            p.start()
            processes.append(p)
            print("Thread %d Range:" % (i + 1),
                  str(start_from).rjust(10, "0"), "-",
                  str(start_from + (total // CPU_COUNT)).rjust(10, "0"))
            start_from += (total // CPU_COUNT)
    # wait for processes to return the md5 message
    # or until all processes finish
    decrypted_md5_hash = None
    while processes and decrypted_md5_hash is None:
        for p in processes:
            if not p.is_alive() and decrypted_md5_hash is None:
                try:
                    decrypted_md5_hash = multiprocessing_queue.get(timeout=5)
                    if decrypted_md5_hash is not None and "not found" in decrypted_md5_hash:
                        print("Process Finished And Returned: Not Found.")
                        decrypted_md5_hash = None
                    print("Process Finished And Found The Encrypted Data:", decrypted_md5_hash)
                    # got result close all other processes
                    for p_ in processes:
                        if p_ is not multiprocessing.current_process():
                            p_.kill()
                    print("killed all processes")
                except queue.Empty:
                    print("empty")
                processes.remove(p)
    if decrypted_md5_hash is not None:
        print(decrypted_md5_hash)


if __name__ == '__main__':
    main()
