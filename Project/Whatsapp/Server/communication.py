import socket


def send_all(sock: socket.socket, msg: bytes) -> bool:
    try:
        sent_amount = 0
        while sent_amount != len(msg):
            sent_amount += sock.send(msg[sent_amount:])
        return True
    except (ConnectionError, socket.error):
        return False


def receive_all(sock: socket.socket, data_len: int) -> bytes:
    try:
        data = b""
        while len(data) != data_len:
            res = sock.recv(data_len - len(data))
            if res == b"":
                raise ConnectionError
            data += res
        return data
    except (ConnectionError, socket.error, ValueError):
        return b""


def receive_a_msg_by_the_protocol(sock: socket.socket) -> bytes:
    len_of_msg = receive_all(sock, 120).decode()
    while len_of_msg.startswith(" "):
        len_of_msg = len_of_msg[1:]
    return receive_all(sock, int(len_of_msg))


def send_a_msg_by_the_protocol(sock: socket.socket, msg: bytes) -> bool:
    return send_all(sock, str(len(msg)).rjust(120, " ").encode() + msg)
