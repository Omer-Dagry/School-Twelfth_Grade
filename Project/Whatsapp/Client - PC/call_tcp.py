import datetime
import socket
import threading
import time

import pyaudio
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


def send(client_socket: socket.socket, stream):
    while True:
        try:
            # Read audio data from the stream
            data = stream.read(CHUNK)
            client_socket.send(data)
        except Exception:
            break


def recv(client_socket: socket.socket, stream):
    
    while True:
        try:
            # write audio received from server to the stream
            data = client_socket.recv(BUFFER_SIZE)
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
    # Create the socket
    client_socket = socket.socket()
    client_socket.connect((HOST, PORT))
    client_socket.settimeout(0.01)
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
