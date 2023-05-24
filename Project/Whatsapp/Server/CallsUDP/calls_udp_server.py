"""
###############################################
Author: Omer Dagry
Mail: omerdagry@gmail.com
Date: 30/05/2023 (dd/mm/yyyy)
###############################################
"""

import time
import pickle
import socket
import hashlib
import traceback
import multiprocessing
import concurrent.futures

from multiprocessing.managers import DictProxy, SyncManager


# Constants
CHUNK = 1024 * 8
BUFFER_SIZE = CHUNK * 4


def broadcast_audio(server_socket: socket.socket, data: bytes, sent_from: tuple[str, int], clients: DictProxy):
    """ broadcast audio stream to all connected clients """
    try:
        time_ = time.perf_counter()
        for addr in clients.keys():  # type: tuple[str, int]
            try:
                # if this ip:port didn't send data for more than 5 seconds stop sending to him
                if (time_ - clients[addr]) > 5:
                    continue
                if addr != sent_from:
                    server_socket.sendto(data, addr)
            except Exception as e:
                # print(f"closed {addr}, ({str(e)})")
                pass
    except KeyboardInterrupt:
        pass


def receive_audio_and_broadcast(server_socket: socket.socket, clients_ips: DictProxy, clients: DictProxy):
    """ receive audio from clients and submit work for the broadcast func """
    try:
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as x:
            while True:
                try:
                    data, sent_from = server_socket.recvfrom(BUFFER_SIZE)
                    if sent_from in clients or sent_from[0] in clients_ips:
                        # if addr not in clients: print(f'new connection from {addr}')
                        clients[sent_from] = time.perf_counter()
                        x.submit(broadcast_audio, server_socket, data, sent_from, clients)
                except BlockingIOError:
                    time.sleep(0.005)
                except (ConnectionError, socket.error, TimeoutError):
                    pass
    except KeyboardInterrupt:
        pass


def accept(server_socket: socket.socket) -> tuple[socket.socket, tuple[str, int]] | tuple[None, None]:
    """ accept a client with a timeout of 1 sec """
    server_socket.settimeout(1)
    try:
        client, addr = server_socket.accept()
    except socket.timeout:
        return None, None
    return client, addr


def recvall(sock: socket.socket, bufsize: int):
    """ recv bufsize from sock """
    data = b""
    while len(data) < bufsize:
        res = sock.recv(bufsize - len(data))
        data += res
        if res == b"":  # connection closed
            return res
    return data


def disconnect_client(client_sock: socket.socket, addr: tuple[str, int], clients_ips: DictProxy,
                      clients_socket_addr: dict, client_sock_last_checkin: dict) -> None:
    """ close connection with client & remove from all databases """
    if (time.perf_counter() - client_sock_last_checkin[client_sock]) > 12:
        if len(clients_ips[addr[0]]) == 1:
            clients_ips.pop(addr[0])
        else:
            ports: list = clients_ips[addr[0]]
            ports.remove(addr[1])
            clients_ips[addr[0]] = ports
        clients_socket_addr.pop(client_sock)
        client_sock_last_checkin.pop(client_sock)
        print("%s:%d Disconnected." % addr)


def handle_tcp_connections(tcp_server_socket: socket.socket, clients_ips: DictProxy,
                           clients_passwords: dict[str, str]) -> None:
    """ handle TCP connections with clients """
    try:
        clients_socket_addr: dict[socket.socket, tuple[str, int]] = {}
        client_sock_last_checkin: dict[socket.socket, float] = {}
        last_msg = time.perf_counter()
        one_client: None | float = None
        while (time.perf_counter() - last_msg) < 20 and (one_client is None or (time.perf_counter() - one_client) < 15):
            try:
                client, addr = accept(tcp_server_socket)
                if client is not None and addr is not None:
                    client: socket.socket
                    addr: tuple[str, int]
                    print("New Connection From %s:%d" % addr)
                    # check password
                    client.settimeout(0.05)
                    msg_length = int(recvall(client, 30).strip().decode())
                    try:
                        username, password = pickle.loads(recvall(client, msg_length))  # type: str, str
                    except pickle.PickleError:
                        username = ""
                        password = ""
                    if username in clients_passwords and \
                            clients_passwords[username] == hashlib.md5(password.encode()).hexdigest().lower():
                        client.sendall(b"ok    ")
                        print(f"%s:%d Connected as '{username}'." % addr)
                        # allow receiving UDP messages from this ip
                        if addr[0] in clients_ips:
                            clients_ips[addr[0]] = clients_ips[addr[0]] + [addr[1]]
                        else:
                            clients_ips[addr[0]] = [addr[1]]
                        clients_socket_addr[client] = addr
                        client_sock_last_checkin[client] = time.perf_counter()
                    else:
                        client.sendall(b"not ok")
                        client.close()
            except Exception as err:
                traceback.format_exception(err)
                #
            if one_client is None and len(clients_socket_addr) == 1:
                one_client = time.perf_counter()
            else:
                one_client = None
            for client, addr in list(clients_socket_addr.items()):
                try:
                    msg = client.recv(2)
                    if msg == b"hi":
                        client_sock_last_checkin[client] = time.perf_counter()
                    else:
                        disconnect_client(client, addr, clients_ips, clients_socket_addr, client_sock_last_checkin)
                    last_msg = time.perf_counter()
                except (socket.timeout, ConnectionError, socket.error):
                    disconnect_client(client, addr, clients_ips, clients_socket_addr, client_sock_last_checkin)
    except KeyboardInterrupt:
        pass


def main(tcp_server_sock: socket.socket, port: int, clients_passwords: dict[str, str],
         clients_ips: DictProxy, clients: DictProxy):
    """ start all the processes and call handle_tcp_connections
    
    :param tcp_server_sock: the TCP socket of the server
    :param port: the port of the server
    :param clients_passwords: dictionary of username and password (hashed twice)
    :param clients_ips: a dictionary that can be shared between processes, will contain all
                        the ips of the verified TCP connections
    :param clients: a dictionary that can be shared between processes, will contain all the
                    clients ip:port and the time of last msg
    """
    # server UDP socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("0.0.0.0", port))
    server_socket.settimeout(0.05)

    # the receiving process (also calls broadcast), 2 sounds better
    receive_process = multiprocessing.Process(
        target=receive_audio_and_broadcast, args=(server_socket, clients_ips, clients)
    )
    receive_process.start()
    receive_process2 = multiprocessing.Process(
        target=receive_audio_and_broadcast, args=(server_socket, clients_ips, clients)
    )
    receive_process2.start()

    try:
        # the tcp connections to the clients
        handle_tcp_connections(tcp_server_sock, clients_ips, clients_passwords)
    finally:
        receive_process.kill()
        receive_process2.kill()


def start_call_server(tcp_server_sock: socket.socket, port: int, clients_passwords: dict[str, str]):
    """ call this to start the server """
    try:
        with multiprocessing.Manager() as manager:  # type: SyncManager
            main(tcp_server_sock, port, clients_passwords, manager.dict(), manager.dict())
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    s = socket.socket()
    s.bind(("0.0.0.0", 16400))
    s.listen()
    start_call_server(
        s, 16400, {"omer": hashlib.md5(hashlib.md5("omer".encode()).hexdigest().lower().encode()).hexdigest().lower()})
