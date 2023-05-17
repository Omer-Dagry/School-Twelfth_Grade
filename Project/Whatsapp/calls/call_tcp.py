import time
import socket
import pyaudio
import threading
import traceback


# Set up PyAudio
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
# Set up the socket
HOST = '127.0.0.1'
PORT = 8820
BUFFER_SIZE = CHUNK * 4


def send(client_socket: socket.socket, stream):
    while True:
        try:
            data = stream.read(CHUNK)
            sent = 0
            while sent < BUFFER_SIZE:
                sent = client_socket.send(data[sent:])
        except socket.timeout:
            pass
        except Exception:
            traceback.print_exc()
            break


def recv(client_socket: socket.socket, stream):
    while True:
        try:
            data = b""
            while len(data) != BUFFER_SIZE:
                data = client_socket.recv((BUFFER_SIZE - len(data)))
            if data == b"":
                raise Exception("disconnected")
            print(data)
            stream.write(data)
        except socket.timeout:
            pass
        except Exception:
            traceback.print_exc()
            break


def main():
    client_socket = socket.socket()
    client_socket.connect((HOST, PORT))
    # client_socket.settimeout(0.05)
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, output=True, frames_per_buffer=CHUNK)
    try:
        recv_thread = threading.Thread(target=recv, args=(client_socket, stream,), daemon=True)
        recv_thread.start()
        send_thread = threading.Thread(target=send, args=(client_socket, stream,), daemon=True)
        send_thread.start()
        while send_thread.is_alive() and recv_thread.is_alive():
            time.sleep(0.5)
    finally:
        stream.stop_stream()
        stream.close()
        p.terminate()
        client_socket.close()


if __name__ == '__main__':
    main()
