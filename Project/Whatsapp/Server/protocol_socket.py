from __future__ import annotations

import os
import ssl
import socket


class EncryptedProtocolSocket:
    def __init__(self, cert_file: os.PathLike = None, key_file: os.PathLike = None, server_side: bool = False,
                 family: socket.AddressFamily | int = None, type: socket.SocketKind | int = None,
                 proto: int = None, fileno: int | None = None, ssl_socket: ssl.SSLSocket = None) -> None:
        #
        self.__server_side = server_side
        if ssl_socket is not None:
            kwargs = {"family": family, "type": type, "proto": proto, "fileno": fileno}
            kwargs = {key_word: arg for key_word, arg in kwargs.items() if arg is not None}
            self.__sock = socket.socket(**kwargs)
            self.__context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER) if server_side else ssl.create_default_context()
            if server_side:
                if cert_file is None or key_file is None:
                    c_f = 'cert_file' if cert_file is None else ''
                    k_f = ', key_file' if key_file is None and cert_file is None \
                        else 'key_file' if key_file is None else ''
                    raise ValueError(f"missing {c_f}{k_f}")
                self.__context.load_cert_chain(cert_file, key_file)
            else:
                self.__context.check_hostname = False
                self.__context.verify_mode = ssl.CERT_NONE
        else:
            if not isinstance(ssl_socket, ssl.SSLSocket):
                raise TypeError("'ssl_socket' must be a ssl.SSLSocket.")
        self.__encrypted_sock: ssl.SSLSocket | None = None if ssl_socket is None else ssl_socket
        self.__block = False if ssl_socket is None else True
        self.__listening = False

    def connect(self, ip_port: tuple[str, int]) -> None:
        if self.__server_side:
            raise OSError("server socket can't use 'connect'.")
        if self.__block:
            raise OSError("already connected")
        if self.__encrypted_sock is None:
            self.__encrypted_sock: ssl.SSLSocket = self.__context.wrap_socket(self.__sock, server_hostname=ip_port[0])
        return self.__encrypted_sock.connect(ip_port)

    def bind(self, ip_port: tuple[str, int]) -> None:
        if not self.__server_side:
            raise OSError("client socket can't use 'bind'.")
        if self.__block:
            raise OSError("already bounded")
        if self.__encrypted_sock is None:
            self.__encrypted_sock: ssl.SSLSocket = self.__context.wrap_socket(self.__sock,
                                                                              server_side=self.__server_side)
        return self.__encrypted_sock.bind(ip_port)

    def listen(self, __backlog: int = None) -> None:
        if not self.__server_side:
            raise OSError("client socket can't use 'listen'.")
        if self.__encrypted_sock is None:
            raise OSError("Please call 'bind' before calling 'listen'.")
        __backlog = [] if __backlog is None else [__backlog]
        self.__encrypted_sock.listen(*__backlog)
        self.__listening = True

    def accept(self) -> tuple[EncryptedProtocolSocket, tuple[str, int]]:
        if not self.__server_side:
            raise OSError("client socket can't use 'listen'.")
        if self.__encrypted_sock is None:
            raise OSError("Please call 'bind' and then 'listen' before calling 'accept'.")
        if not self.__listening:
            raise OSError("Please call 'listen' before calling 'accept'.")
        ssl_socket, ip_port = self.__encrypted_sock.accept()
        return EncryptedProtocolSocket(ssl_socket=ssl_socket), ip_port

    def send_message(self, data: bytes, flags: None | int = None):
        """ send a message according to the protocol """
        # check that encrypted socket isn't None
        if self.__encrypted_sock is None:
            raise OSError(f"Please Call '{'bind' if self.__server_side else 'connect'}' before sending a message.")
        # add the length of the data unencrypted before the data itself
        data = str(len(data)).ljust(30).encode() + data
        flags = [] if flags is None else [flags]
        while data != b"":
            sent = self.__encrypted_sock.send(data, *flags)
            data = data[sent:]

    def receive_message(self, timeout: int | None = None) -> bytes:
        """ receive a message according to the protocol
        :param timeout: set a timeout to receive a message, if timeout is passed but part
                        of the message is received, the timeout is ignored
        """
        # check that encrypted socket isn't None
        if self.__encrypted_sock is None:
            raise OSError(f"Please Call '{'bind' if self.__server_side else 'connect'}' before receiving a message.")
        current_timeout = self.__encrypted_sock.timeout
        self.settimeout(timeout)
        data_length = b""
        while len(data_length) < 30:
            try:
                received = self.__encrypted_sock.recv(120 - len(data_length))
                data_length += received
                if received == b"":  # connection closed
                    return b""
            except socket.timeout:  # return only if received nothing
                if data_length == b"":
                    return b""
        data_length = int(data_length.strip())
        data = b""
        while len(data) < data_length:
            try:
                received = self.__encrypted_sock.recv(data_length - len(data))
                data += received
                if received == b"":  # connection closed
                    return b""
            except socket.timeout:  # return only if received nothing
                if data == b"":
                    return b""
        self.settimeout(current_timeout)
        return data

    def settimeout(self, __value: float | None) -> None:
        return self.__encrypted_sock.settimeout(__value)

    def get_timeout(self) -> float | None:
        if self.__encrypted_sock is None:
            raise OSError(f"Please Call '{'bind' if self.__server_side else 'connect'}' before 'get_timeout'.")
        return self.__encrypted_sock.timeout

    def getpeername(self) -> tuple[str, int]:
        if self.__encrypted_sock is None:
            raise OSError(f"Please Call '{'bind' if self.__server_side else 'connect'}' before 'getpeername'.")
        return self.__encrypted_sock.getpeername()

    def close(self):
        if self.__encrypted_sock is not None:
            self.__encrypted_sock.close()
