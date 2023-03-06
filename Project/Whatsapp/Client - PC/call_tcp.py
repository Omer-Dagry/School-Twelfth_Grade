import datetime
import socket
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


def main():
    # Create the socket
    client_socket = socket.socket()
    client_socket.connect((HOST, PORT))
    # Create PyAudio stream for recording audio
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, output=True, frames_per_buffer=CHUNK)
    try:
        client_socket.settimeout(0.01)
        while True:
            try:
                # Read audio data from the stream
                data = stream.read(CHUNK)
                client_socket.send(data)

                # write audio received from server to the stream
                data = client_socket.recv(BUFFER_SIZE)
                if data != b"":
                    # print(data)
                    stream.write(data)
            except socket.timeout:
                pass
            except Exception:
                traceback.print_exc()
                break
    finally:
        # Clean up PyAudio and close the connection
        stream.stop_stream()
        stream.close()
        p.terminate()
        client_socket.close()


if __name__ == '__main__':
    main()
