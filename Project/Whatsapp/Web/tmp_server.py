import socket

from typing import *


def start_server(ip: str, port: int, sock_type: tuple=(socket.AF_INET, socket.SOCK_STREAM)) \
        -> Union[socket.socket, None]:
    server_sock = socket.socket(*sock_type)
    try:
        server_sock.bind((ip, port))
        server_sock.listen()
    except socket.error:
        print("Error Starting Server Socket.")
        return None
    except OSError:
        print(f"Error Starting Server Socket, Port {port} Is Taken.")
        return None
    return server_sock


def accept_client(server_socket: socket.socket) -> Union[tuple[socket.socket, tuple[str, str]], None]:
    time_out = server_socket.timeout
    server_socket.settimeout(2)
    try:
        client_sock, client_ip_port = server_socket.accept()
    except socket.error:
        server_socket.settimeout(time_out)
        return None
    server_socket.settimeout(time_out)
    return client_sock, client_ip_port


def send_index_html(client_sock: socket.socket):
    with open("index.html", "rb") as file:
        index_html = file.read()
    client_sock.send("200 OK ")


def handle_client(client_sock: socket.socket, client_ip_port: tuple[str, str]):
    data = ""
    while "\r\n\r\n" not in data:
        data += client_sock.recv(1).decode()
    print(data.encode())
    if data.startswith("GET / HTTP/1.1\r\n\r\n"):
        send_index_html(client_sock)
    elif data.startswith("GET / HTTP/1.1\r\n\r\n"):
        pass


def main():
    server_sock = start_server("0.0.0.0", 80)
    while True:
        connection_data = accept_client(server_sock)
        if connection_data is not None:
            handle_client(*connection_data)


if __name__ == '__main__':
    main()
