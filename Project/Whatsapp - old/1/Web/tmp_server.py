import os
import socket
import threading

from typing import *


# CONSTANTS
STATUS_CODES = {"ok": "200 OK", "bad": "400 BAD REQUEST", "not found": "404 NOT FOUND",
                "forbidden": "403 FORBIDDEN", "moved": "302 FOUND",
                "server error": "500 INTERNAL SERVER ERROR"}
FILE_TYPE = {"html": "text/html;charset=utf-8", "jpg": "image/jpeg", "css": "text/css",
             "js": "text/javascript; charset=UTF-8", "txt": "text/plain", "ico": "image/x-icon",
             "gif": "image/jpeg", "png": "image/png"}
ERRORS_IMAGES_LOCATION = {"400": "/imgs/400.png", "404": "/imgs/404.png", "403": "/imgs/403.png",
                          "500": "/imgs/403.png"}
CONTENT_TYPE = "Content-Type"
CONTENT_LENGTH = "Content-Length"
INDEX_HTML = "index.html"
HTTP_1_1 = "HTTP/1.1"
WEB_ROOT = "webroot"

# GLOBALS
print_lock = threading.Lock()


def start_server(ip: str, port: int, sock_type: tuple = (socket.AF_INET, socket.SOCK_STREAM)) \
        -> Union[socket.socket, None]:
    server_sock = socket.socket(*sock_type)
    try:
        server_sock.bind((ip, port))
        server_sock.listen()
    except OSError:
        print(f"Error Starting Server Socket, Port {port} Is Taken.")
        return None
    except socket.error:
        print("Error Starting Server Socket.")
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


def print_(*args, sep=' ', end='\n', file=None):
    global print_lock
    print_lock.acquire()
    print(*args, sep=sep, end=end, file=file)
    print_lock.release()


def send_all(client_sock: socket.socket, data: bytes):
    try:
        while data != b"":
            sent = client_sock.send(data)
            data = data[sent:]
    except (socket.error, ConnectionError) as err:
        print_(f"Error Sending Data: {err}")


def get_file_data(file: str) -> bytes:
    with open(file, "rb") as f:
        data = f.read()
    return data


def bad():
    """
    assembles a http 400 bad-request response
    """
    return f"{HTTP_1_1} {STATUS_CODES['bad']}\r\n" \
           f"{CONTENT_LENGTH}: {os.path.getsize(WEB_ROOT + ERRORS_IMAGES_LOCATION['400'])}\r\n" \
           f"{CONTENT_TYPE}: {FILE_TYPE['png']}\r\n\r\n".encode() + \
           get_file_data(WEB_ROOT + ERRORS_IMAGES_LOCATION['400'])


def not_found():
    """
    assembles a http 404 not found response
    """
    return f"{HTTP_1_1} {STATUS_CODES['not found']}\r\n" \
           f"{CONTENT_LENGTH}: {os.path.getsize(WEB_ROOT + ERRORS_IMAGES_LOCATION['404'])}\r\n" \
           f"{CONTENT_TYPE}: {FILE_TYPE['png']}\r\n\r\n".encode() + \
           get_file_data(WEB_ROOT + ERRORS_IMAGES_LOCATION['404'])


def handle_get_requests(request: str, client_sock: socket.socket):
    # GET / HTTP/1.1\r\nHEADER\r\nHEADER\r\nHEADER\r\n\r\n
    request = request[:-4]  # remove the last \r\n\r\n
    resource = request.split()[1]
    headers_list = request.split("\r\n")[1:]
    response: list[bytes] = [f"{HTTP_1_1} {STATUS_CODES['ok']}".encode()]
    if resource == "/":
        response.append(f"{CONTENT_LENGTH}: {os.path.getsize(WEB_ROOT + '/' + INDEX_HTML)}".encode())
        response.append(f"{CONTENT_TYPE}: {FILE_TYPE['html']}".encode())
        response.append(get_file_data(WEB_ROOT + '/' + INDEX_HTML))
    else:
        resource = WEB_ROOT + resource if resource[0] == "/" else WEB_ROOT + "/" + resource
        if os.path.isfile(resource):
            response.append(f"{CONTENT_LENGTH}: {os.path.getsize(resource)}".encode())
            response.append(f"{CONTENT_TYPE}: {FILE_TYPE[resource.split('.')[-1]]}".encode())
            response.append(get_file_data(resource))
        else:  # requested file doesn't exist
            response = not_found().split(b"\r\n")
    response: bytes = b"\r\n".join(response[:-1]) + b"\r\n\r\n" + response[-1]
    send_all(client_sock, response)


def handle_post_requests(request: str, client_sock: socket.socket):
    # POST / HTTP/1.1\r\nHEADER\r\nHEADER\r\nHEADER\r\n\r\nDATA
    request = request[:-4]  # remove the last \r\n\r\n
    resource = request.split()[1]
    headers_list = request.split("\r\n")[1:]
    for header in headers_list:
        if header.lower().startswith(CONTENT_LENGTH.lower()):
            content_length = int(header.split(header[:16])[1])
            break
    else:
        return  # request isn't valid
    print(resource)
    print(headers_list)
    print(content_length)
    data = b""
    while len(data) < content_length:
        data += client_sock.recv(content_length - len(data))


def handle_client(client_sock: socket.socket, client_ip_port: tuple[str, str]):
    request = ""
    while "\r\n\r\n" not in request:
        request += client_sock.recv(1).decode()
    # print(request.encode())
    # "GET / HTTP/1.1\r\n\r\n"
    if request.startswith("GET"):
        handle_get_requests(request, client_sock)
        pass
    elif request.startswith("POST"):
        pass
    elif request.startswith("HEAD"):
        pass


def main():
    server_sock = start_server("0.0.0.0", 80)
    while True:
        connection_data = accept_client(server_sock)
        if connection_data is not None:
            handle_client(*connection_data)


if __name__ == '__main__':
    main()
