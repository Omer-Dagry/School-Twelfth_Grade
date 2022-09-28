import hashlib
import itertools
import socket
import multiprocessing
import queue
import time

IP = "127.0.0.1"
PORT = 8820
PACKET_LEN = 32
ABC = "abcdefghigklmnopqrstuvwxyz"
NUMBERS = "1234567890"
SIGNS = "!?:|\\/.,<>;'@#$%^&*(){}[]~`" + '"'


def brute_force_decrypt_md5(md5_hash, repeat, queue_):
    if repeat == 0:
        time.sleep(10)
        queue_.put("sadfasdf")


def main():
    # sock = socket.socket()
    # sock.connect((IP, PORT))
    # my_range = sock.recv(PACKET_LEN).decode()
    # md5_hash = sock.recv(PACKET_LEN).decode().lower()
    processes = []
    multiprocessing_queue = multiprocessing.Queue()
    for i in range(multiprocessing.cpu_count()):
        repeat = None
        p = multiprocessing.Process(target=brute_force_decrypt_md5,
                                    args=("", i, multiprocessing_queue,),
                                    daemon=True)
        p.start()
        processes.append(p)
    print(len(processes))
    decrypted_md5_hash = None
    while processes and decrypted_md5_hash is None:
        for p in processes:
            if not p.is_alive() and decrypted_md5_hash is None:
                try:
                    decrypted_md5_hash = multiprocessing_queue.get(timeout=5)
                    print("process returned:", decrypted_md5_hash)
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
