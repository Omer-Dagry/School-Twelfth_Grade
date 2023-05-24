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
import pyaudio
import threading

from ClientSecureSocket import ClientEncryptedProtocolSocket


# Constants
# PyAudio
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
# Others
CHUNK = 1024 * 8
BUFFER_SIZE = CHUNK * 4

# Globals
stop = False
connected = False


def get_sound(stream: pyaudio.Stream, client_socket: socket.socket):
    """ a loop to get UDP audio packets from the server """
    global stop
    data = b""
    while not stop:
        try:
            # write audio received from server to the stream
            data = client_socket.recvfrom(BUFFER_SIZE)[0]
        except socket.timeout:
            continue
        except (ConnectionError, socket.error):
            stop = True
            break
        except KeyboardInterrupt:
            pass
        if data != b"":
            stream.write(data)


def send_sound(stream: pyaudio.Stream, client_socket: socket.socket, server_addr: tuple[str, int]):
    """ a loop to send UDP audio packets to the server """
    global stop
    while not stop:
        # Read audio data from the stream
        data = stream.read(CHUNK)
        try:
            # Send the audio data to the server
            client_socket.sendto(data, server_addr)
        except socket.timeout:
            pass
        except (ConnectionError, socket.error):
            stop = True
            break
        except KeyboardInterrupt:
            pass
        time.sleep(0.02)


def handle_tcp_connection(server_addr: tuple[str, int], email: str, password: str):
    """ the TCP connection to the server """
    global connected, stop
    tcp_sock = ClientEncryptedProtocolSocket()
    tcp_sock.connect(server_addr)
    connected = True
    try:
        tcp_sock.send_message(pickle.dumps([email, password]))
        if tcp_sock.recv_message() != b"ok    ":
            print("Failed to connect to call.")
            raise ConnectionError
        print("Connected to call.")
        while True:
            tcp_sock.send_message(b"hi")
            time.sleep(5)
    except (ConnectionError, socket.error):
        pass
    except KeyboardInterrupt:
        pass
    finally:
        stop = True
        tcp_sock.close()


def join_call(server_addr: tuple[str, int], email: str, password: str):
    """
        calls all the needed functions and start the PyAudio stream
        open a process when calling this function
    """
    global stop
    #
    tcp_connection_thread = threading.Thread(
        target=handle_tcp_connection, args=(server_addr, email, password,), daemon=True
    )
    tcp_connection_thread.start()
    #
    while not connected:
        if stop:
            pass  # TODO: display error of connection to server
        time.sleep(0.1)
    #
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Create PyAudio stream for recording and playing audio
    p = pyaudio.PyAudio()
    # info = p.get_host_api_info_by_index(0)
    # device_count = info.get('deviceCount')
    # devices = [p.get_device_info_by_host_api_device_index(0, i) for i in range(device_count)]
    # input_devices = [device for device in devices if "maxInputChannels" in device and device["maxInputChannels"] > 0]
    # output_devices = [device for device in devices
    #                   if "maxOutputChannels" in device and device["maxOutputChannels"] > 0]
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, output=True, frames_per_buffer=CHUNK)
    send_sound_thread = threading.Thread(target=send_sound, args=(stream, client_socket, server_addr), daemon=True)
    try:
        client_socket.settimeout(0.1)
        send_sound_thread.start()
        get_sound(stream, client_socket)
    except KeyboardInterrupt:
        pass
    finally:
        stop = True
        send_sound_thread.join(1)
        # Clean up PyAudio and close the connection
        stream.stop_stream()
        stream.close()
        p.terminate()
        client_socket.close()


if __name__ == '__main__':
    join_call(("127.0.0.1", 16400), "omer", hashlib.md5("omer".encode()).hexdigest().lower())
