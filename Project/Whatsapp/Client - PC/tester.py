import socket
import pyaudio
import traceback


# PyAudio
CHUNK = 1024 * 2
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 44100
# Server
HOST = None
PORT = 8820
BUFFER_SIZE = CHUNK * 4


def main():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Create PyAudio stream for recording and playing audio
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, output=True, frames_per_buffer=CHUNK)
    try:
        client_socket.settimeout(0.01)
        while True:
            try:
                # Read audio data from the stream
                data = stream.read(CHUNK)
                # Send the audio data to the server
                client_socket.sendto(data, (HOST, PORT))
                # write audio received from server to the stream
                data = client_socket.recvfrom(BUFFER_SIZE)[0]
                if data != b"":
                    # print(data)
                    stream.write(data)
            except socket.timeout:
                pass
            except Exception as e:
                traceback.print_exception(e)
                break
    finally:
        # Clean up PyAudio and close the connection
        stream.stop_stream()
        stream.close()
        p.terminate()
        client_socket.close()


if __name__ == '__main__':
    main()
