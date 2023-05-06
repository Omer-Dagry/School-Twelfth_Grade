import queue
import socket
import datetime
import multiprocessing


HOST = 'localhost'
PORT = 16400
CHUNK = 1024 * 2
BUFFER_SIZE = CHUNK * 4

# Globals
stop: None | datetime.datetime = None


# Function to broadcast audio stream to all connected clients
def broadcast_audio(data_queue: multiprocessing.Queue,
                    server_socket: socket.socket, remove_queue: multiprocessing.Queue):
    while True:
        data, sent_from, clients = data_queue.get()
        for addr in clients.keys():
            try:
                if (datetime.datetime.now() - clients[addr]).seconds > 5:
                    raise TimeoutError
                if addr != sent_from and data != b"":
                    server_socket.sendto(data, addr)
            except TimeoutError:
                print(f"{addr} timed out")
                remove_queue.put(sent_from)
            except Exception as e:
                print(f"closed {addr}, ({str(e)})")
                remove_queue.put(sent_from)


def main():
    global stop
    clients = {}
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind(("0.0.0.0", PORT))
    #
    data_queue = multiprocessing.Queue()
    remove_queue = multiprocessing.Queue()
    broadcast_audio_thread = multiprocessing.Process(
        target=broadcast_audio, args=(data_queue, server_socket, remove_queue), daemon=True
    )
    broadcast_audio_thread.start()
    #
    server_socket.settimeout(0.01)
    stop = datetime.datetime.now()
    last_msg = stop
    while (clients.keys() or (datetime.datetime.now() - stop).seconds < 20) and \
            (len(clients.keys()) <= 1 and (datetime.datetime.now() - last_msg).seconds < 20):
        try:
            data, addr = server_socket.recvfrom(BUFFER_SIZE)
            if addr not in clients:
                print(f"new connection from {addr}")
            time = datetime.datetime.now()
            clients[addr] = time
            last_msg = time
            data_queue.put((data, addr, clients))
        except ConnectionResetError:
            pass
        except socket.timeout:
            pass
        except Exception as e:
            # traceback.print_exception(e)
            pass
        try:
            remove = data_queue.get(block=False)
            print(remove)
            if remove in clients:
                clients.pop(remove)
        except queue.Empty:
            pass


if __name__ == '__main__':
    main()
