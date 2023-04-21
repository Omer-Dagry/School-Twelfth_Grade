import socket
import datetime
import traceback


HOST = 'localhost'
PORT = 8822
CHUNK = 1024 * 2
BUFFER_SIZE = CHUNK * 4

# Globals
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(("0.0.0.0", PORT))
clients = {}
stop: None | datetime.datetime = None


# Function to broadcast audio stream to all connected clients
def broadcast_audio(data: bytes, sent_from: tuple):
    remove = []
    for addr in clients.keys():
        try:
            if (datetime.datetime.now() - clients[addr]).seconds > 5:
                raise TimeoutError
            if addr != sent_from and data != b"":
                server_socket.sendto(data, addr)
        except TimeoutError:
            print(f"{addr} timed out")
            remove.append(addr)
        except Exception as e:
            print(f"closed {addr}, ({str(e)})")
            traceback.print_exception(e)
            remove.append(addr)
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
        except Exception as e:
            traceback.print_exception(e)


if __name__ == '__main__':
    main()
