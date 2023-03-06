import socket
import pyaudio
import traceback


# Set up PyAudio
CHUNK = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 2
RATE = 44100
# Set up the socket
HOST = 'localhost'
PORT = 8820
BUFFER_SIZE = CHUNK * 4


def main():
    # Create the socket
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    # Create PyAudio stream for recording audio
    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, output=True, frames_per_buffer=CHUNK)
    try:
        while True:
            try:
                # Read audio data from the stream
                data = stream.read(CHUNK)

                # Send the audio data to the server
                client_socket.sendto(data, (HOST, PORT))

                # write audio received from server to the stream
                stream.write(client_socket.recvfrom(BUFFER_SIZE)[0])
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
