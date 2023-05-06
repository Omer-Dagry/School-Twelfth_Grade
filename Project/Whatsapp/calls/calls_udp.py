import threading
import time
import socket
import pyaudio
import traceback


# PyAudio
CHUNK = 1024 * 2
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
# Server
HOST = "127.0.0.1"
PORT = 16400
BUFFER_SIZE = CHUNK * 4

# Globals
stop = False


def get_sound(stream: pyaudio.Stream, client_socket: socket.socket):
    global stop
    while not stop:
        try:
            # write audio received from server to the stream
            data = client_socket.recvfrom(BUFFER_SIZE)[0]
        except socket.timeout:
            continue
        except Exception as e:
            traceback.print_exception(e)
            stop = True
            break
        if data != b"":
            # print(data)
            stream.write(data)


def send_sound(stream: pyaudio.Stream, client_socket: socket.socket):
    global stop
    while not stop:
        # Read audio data from the stream
        data = stream.read(CHUNK)
        try:
            # Send the audio data to the server
            client_socket.sendto(data, (HOST, PORT))
        except socket.timeout:
            pass
        except Exception as e:
            traceback.print_exception(e)
            stop = True
            break
        time.sleep(0.02)


def main():
    global stop
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
    send_sound_thread = threading.Thread(target=send_sound, args=(stream, client_socket,), daemon=True)
    try:
        client_socket.settimeout(0.1)
        send_sound_thread.start()
        get_sound(stream, client_socket)
    finally:
        stop = True
        send_sound_thread.join(1)
        # Clean up PyAudio and close the connection
        stream.stop_stream()
        stream.close()
        p.terminate()
        client_socket.close()


if __name__ == '__main__':
    main()
