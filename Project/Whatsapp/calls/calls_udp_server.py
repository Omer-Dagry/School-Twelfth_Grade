import time
import socket
import threading
import multiprocessing
from multiprocessing.connection import PipeConnection


# Constants
HOST = 'localhost'
PORT = 16400
CHUNK = 1024 * 4
BUFFER_SIZE = CHUNK * 4


# Function to broadcast audio stream to all connected clients
def broadcast_audio(recv_pipe: PipeConnection, server_socket: socket.socket):
    try:
        while True:
            data, sent_from, clients = recv_pipe.recv()
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


def receive_audio_and_handle_queue(server_socket: socket.socket, clients_ips: set[str],
                                   send_pipe1: PipeConnection, clients: dict = None,
                                   open_thread: bool = True, send_pipe2: PipeConnection = None):
    try:
        clients = {} if clients is None else clients
        if open_thread and send_pipe2 is not None:
            threading.Thread(target=receive_audio_and_handle_queue,
                             args=(server_socket, clients_ips, send_pipe2, clients, False), daemon=True).start()
        last_msg = time.perf_counter()
        while (time.perf_counter() - last_msg) < 20:  # TODO: remove last_msg when implementing the TCP connections
            try:
                data, sent_from = server_socket.recvfrom(BUFFER_SIZE)
                if sent_from[0] in clients_ips:
                    # if addr not in clients: print(f'new connection from {addr}')
                    clients[sent_from] = last_msg = time.perf_counter()
                    send_pipe1.send((data, sent_from, clients))
            except BlockingIOError:
                time.sleep(0.005)
            except (ConnectionError, socket.error, TimeoutError):
                pass
    except KeyboardInterrupt:
        pass


def main(clients_ips: set[str]):
    """
    :param clients_ips: all the ips that this server should accept connection from
    """
    # server socket
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("0.0.0.0", PORT))
    server_socket.settimeout(0.05)

    # queue to transfer data from the receiving process to the broadcasting processes
    send_pipe1, recv_pipe1 = multiprocessing.Pipe()  # type: PipeConnection
    send_pipe2, recv_pipe2 = multiprocessing.Pipe()  # type: PipeConnection

    # the broadcast processes
    broadcast_process1 = multiprocessing.Process(target=broadcast_audio, args=(recv_pipe1, server_socket), daemon=True)
    broadcast_process1.start()
    broadcast_process2 = multiprocessing.Process(target=broadcast_audio, args=(recv_pipe2, server_socket), daemon=True)
    broadcast_process2.start()

    # the receiving process
    receive_process = multiprocessing.Process(
        target=receive_audio_and_handle_queue, args=(server_socket, clients_ips, send_pipe1,),
        kwargs={"send_pipe2": send_pipe2}, daemon=True
    )
    receive_process.start()

    # the tcp connections to the clients
    # TODO: manage TCP connections
    #

    # before exit
    receive_process.join()  # TODO: remove when implementing the TCP connections
    # receive_process.kill()
    broadcast_process1.kill()
    broadcast_process2.kill()


def start(clients_ips: set[str]):
    try:
        main(clients_ips)
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    start({"127.0.0.1", "79.179.79.155", "87.69.235.161"})
