import socket
import pyaudio
import datetime
import traceback


# Set up PyAudio
CHUNK = 1024 * 2
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
# Set up the socket
HOST = 'localhost'
PORT = 8820
BUFFER_SIZE = CHUNK * 4

# Globals
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(("0.0.0.0", PORT))
clients = {}
stop: None | datetime.datetime = None


# Function to broadcast audio stream to all connected clients
def broadcast_audio(data: bytes, sent_from: tuple):
    global stop
    remove = []
    for addr in clients.keys():
        try:
            if (datetime.datetime.now() - clients[addr]).seconds > 5:
                raise TimeoutError
            if addr != sent_from and data != b"":
                server_socket.sendto(data, addr)
        except TimeoutError:
            print(f"closed {addr} 1")
            remove.append(addr)
        except Exception:
            print(f"closed {addr} 2")
            remove.append(addr)
            traceback.print_exc()
    for addr in remove:
        clients.pop(addr)


def main():
    global stop
    server_socket.settimeout(0.01)
    stop = datetime.datetime.now()
    while clients.keys() or (datetime.datetime.now() - stop).seconds < 5:
        try:
            data, addr = server_socket.recvfrom(BUFFER_SIZE)
            if addr not in clients:
                print(f"new connection from {addr}")
            clients[addr] = datetime.datetime.now()
            broadcast_audio(data, addr)
        except ConnectionResetError:
            pass
        except socket.timeout:
            broadcast_audio(b"", (None, None))
        except Exception:
            traceback.print_exc()


if __name__ == '__main__':
    main()
