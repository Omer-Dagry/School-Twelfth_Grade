import time
import socket
import threading
import multiprocessing

# Constants
HOST = 'localhost'
PORT = 16400
CHUNK = 1024 * 2
BUFFER_SIZE = CHUNK * 4


# Function to broadcast audio stream to all connected clients
def broadcast_audio(data_queue: multiprocessing.Queue, server_socket: socket.socket, open_thread: bool = True):
    if open_thread:
        threading.Thread(
            target=broadcast_audio, args=(data_queue, server_socket, False), daemon=True
        ).start()
    while True:
        data, sent_from, clients = data_queue.get(block=True)
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


def receive_audio_and_handle_queue(server_socket: socket.socket, clients_ips: set[str],
                                   data_queue: multiprocessing.Queue, clients: dict | None = None,
                                   open_thread: bool = True):
    clients = {} if clients is None else clients
    if open_thread:
        threading.Thread(
            target=receive_audio_and_handle_queue,
            args=(server_socket, clients_ips, data_queue, clients, False),
            daemon=True
        ).start()
    last_msg = time.perf_counter()
    while (time.perf_counter() - last_msg) < 20:  # TODO: remove last_msg when implementing the TCP connections
        try:
            data, addr = server_socket.recvfrom(BUFFER_SIZE)
            if addr[0] in clients_ips:
                # if addr not in clients:
                #     print(f'new connection from {addr}')
                clients[addr] = last_msg = time.perf_counter()
                data_queue.put((data, addr, clients))
        # except Exception as e:
        #     traceback.print_exception(e)
        except BlockingIOError:
            time.sleep(0.005)
        except TimeoutError:
            pass
        except (ConnectionError, socket.error):
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
    data_queue = multiprocessing.Queue()

    # the broadcast processes
    broadcast_processes = [
        multiprocessing.Process(target=broadcast_audio, args=(data_queue, server_socket), daemon=True)
        for _ in range(2)
    ]
    for broadcast_process in broadcast_processes:
        broadcast_process.start()

    # the receiving process
    receive_process = multiprocessing.Process(
        target=receive_audio_and_handle_queue, args=(server_socket, clients_ips, data_queue,), daemon=True
    )
    receive_process.start()

    # the tcp connections to the clients
    # TODO: manage TCP connections
    #

    # before exit
    receive_process.join()  # TODO: remove when implementing the TCP connections
    # receive_process.kill()
    for broadcast_process in broadcast_processes:
        broadcast_process.kill()


if __name__ == '__main__':
    main({"127.0.0.1"})
