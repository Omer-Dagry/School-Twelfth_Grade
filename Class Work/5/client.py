import hashlib
import itertools
import socket
import multiprocessing
import queue
import string


IP = "127.0.0.1"
PORT = 8820
PACKET_LEN = 32
ABC_LOW = "abcdefghijklmnopqrstuvwxyz"
ABC_HIGH = ABC_LOW.upper()
NUMBERS = "0123456789"
SIGNS = "!#$%&'()*+,-./:;<=>?@[\\]^_`{|}~ " + '"'
ALL = string.printable


def brute_force_decrypt_md5(md5_hash, repeat, multiprocessing_queue):
    message = None
    for option in itertools.product(ALL, repeat=repeat):
        if hashlib.md5("".join(option).encode('utf-8')).hexdigest() == md5_hash:
            message = "".join(option)
            break
    if message is not None:
        multiprocessing_queue.put(message)


def main():
    # open socket to server
    sock = socket.socket()
    sock.connect((IP, PORT))
    # get my range
    my_range = sock.recv(PACKET_LEN).decode()
    # get md5 hash to brute force
    md5_hash = sock.recv(PACKET_LEN).decode().lower()
    processes = []
    # communication
    multiprocessing_queue = multiprocessing.Queue()
    # open number of cores in the PC processes
    for i in range(multiprocessing.cpu_count()):
        repeat = None
        p = multiprocessing.Process(target=brute_force_decrypt_md5,
                                    args=(md5_hash, repeat, multiprocessing_queue,),
                                    daemon=True)
        p.start()
        processes.append(p)
    # wait for processes to return the md5 message
    # or until all processes finish
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
