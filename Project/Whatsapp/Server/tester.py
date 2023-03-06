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
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind((HOST, PORT))
clients = {}


# Function to broadcast audio stream to all connected clients
def broadcast_audio(data: bytes):
    remove = []
    for addr in clients.keys():
        try:
            if (datetime.datetime.now() - clients[addr]).seconds > 5:
                raise TimeoutError
            server_socket.sendto(data, addr)
        except TimeoutError:
            print(f"closed {addr}")
            remove.append(addr)
        except Exception:
            print(f"closed {addr}")
            remove.append(addr)
            traceback.print_exc()
    for addr in remove:
        clients.pop(addr)


def main():
    server_socket.settimeout(1)
    while True:
        try:
            data, addr = server_socket.recvfrom(BUFFER_SIZE)
            if addr not in clients:
                print(f"new connection from {addr}")
            clients[addr] = datetime.datetime.now()
            broadcast_audio(data)
        except ConnectionResetError:
            pass
        except socket.timeout:
            broadcast_audio(b"")
        except Exception:
            traceback.print_exc()


if __name__ == '__main__':
    main()
