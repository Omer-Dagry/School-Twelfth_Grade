import socket
import pyaudio
import datetime
import traceback
import threading


# Set up PyAudio
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
# Set up the socket
HOST = 'localhost'
PORT = 8820
BUFFER_SIZE = CHUNK * 4

# Globals
server_socket = socket.socket()
server_socket.bind(("0.0.0.0", PORT))
server_socket.listen()
clients: dict[tuple[str, int], socket.socket] = {}
lock = threading.Lock()
stop: None | datetime.datetime = None


# Function to broadcast audio stream to all connected clients
def broadcast_audio(data: bytes, sent_from: tuple):
    global stop
    remove = []
    for addr, sock in clients.items():
        try:
            if addr != sent_from:
                sent = 0
                while sent < BUFFER_SIZE:
                    sent = sock.send(data[sent:])
        except Exception:
            print(f"closed {addr} 2")
            remove.append(addr)
            traceback.print_exc()
    lock.acquire()
    for addr in remove:
        if addr in clients:
            clients.pop(addr)
    lock.release()


def handle_client(sock: socket.socket, addr: tuple[str, int]):
    global stop
    while clients or (datetime.datetime.now() - stop).seconds < 5:
        try:
            data = sock.recv(BUFFER_SIZE)
            if data == b"":
                raise Exception("client disconnected (received null)")
            broadcast_audio(data, addr)
        except Exception:
            print(f"disconnected '%s:%s', exc: {traceback.format_exc()}" % addr)
            lock.acquire()
            if addr in clients:
                clients.pop(addr)
            lock.release()
            break


def main():
    global stop
    clients_threads = []
    stop = datetime.datetime.now()
    while clients or (datetime.datetime.now() - stop).seconds < 5:
        sock, addr = server_socket.accept()
        sock: socket.socket
        addr: tuple[str, int]
        print("new connection '%s:%s'" % addr)
        lock.acquire()
        clients[addr] = sock
        lock.release()
        t = threading.Thread(target=handle_client, args=(sock, addr,), daemon=True)
        t.start()
        clients_threads.append(t)


if __name__ == '__main__':
    main()
