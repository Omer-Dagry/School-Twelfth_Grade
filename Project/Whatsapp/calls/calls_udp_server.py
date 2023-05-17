import time
import socket
import multiprocessing
import concurrent.futures


# Constants
PORT = 16400
CHUNK = 1024 * 4
BUFFER_SIZE = CHUNK * 4


# Function to broadcast audio stream to all connected clients
def broadcast_audio(server_socket: socket.socket, data: bytes, sent_from: tuple[str, int], clients: dict):
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
                print(f"closed {addr}, ({str(e)})")
    except KeyboardInterrupt:
        pass


def receive_audio_and_broadcast(server_socket: socket.socket, clients_ips: set[str], clients: dict = None):
    try:
        clients = {} if clients is None else clients
        last_msg = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as x:
            while (time.perf_counter() - last_msg) < 20:  # TODO: remove last_msg when implementing the TCP connections
                try:
                    data, sent_from = server_socket.recvfrom(BUFFER_SIZE)
                    if sent_from[0] in clients or sent_from[0] in clients_ips:
                        # if addr not in clients: print(f'new connection from {addr}')
                        clients[sent_from] = last_msg = time.perf_counter()
                        x.submit(broadcast_audio, server_socket, data, sent_from, clients)
                except BlockingIOError:
                    time.sleep(0.005)
                except (ConnectionError, socket.error, TimeoutError):
                    pass
    except KeyboardInterrupt:
        pass


def handle_tcp_connections():
    # TODO: implement this function
    pass


def main(clients_ips: set[str]):
    """
    :param clients_ips: all the ips that this server should accept connection from
    """
    # server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("0.0.0.0", PORT))
    server_socket.settimeout(0.05)

    # the receiving process (also calls broadcast)
    receive_process = multiprocessing.Process(target=receive_audio_and_broadcast, args=(server_socket, clients_ips,))
    receive_process.start()
    receive_process2 = multiprocessing.Process(target=receive_audio_and_broadcast, args=(server_socket, clients_ips,))
    receive_process2.start()

    # the tcp connections to the clients
    # TODO: manage TCP connections
    handle_tcp_connections()
    #

    # before exit
    receive_process.join()  # TODO: remove when implementing the TCP connections
    receive_process2.kill()
    # receive_process.kill()


# TODO: change it to get no ips, and the clients need to identify through
#  the tcp connection and then their ip is accepted
def start(clients_ips: set[str]):
    try:
        main(clients_ips)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    start({"127.0.0.1", "79.179.79.155", "87.69.235.161"})
