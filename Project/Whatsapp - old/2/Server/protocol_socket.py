from __future__ import annotations

import socket as s
import _socket

from _socket import *


class ProtocolSocket(s.socket, _socket.socket):
    def send_message(self, data: bytes, flags: None | int = None):
        """ send a message according to the protocol """
        # add the length of the data unencrypted before the data itself
        data = str(len(data)).ljust(120).encode() + data
        flags = [] if flags is None else [flags]
        while data != b"":
            sent = super().send(data, *flags)
            data = data[sent:]

    def receive_message(self, timeout: int | None = None) -> bytes:
        """ receive a message according to the protocol
        :param timeout: set a timeout to receive a message, if timeout is passed but part
                        of the message is received, the timeout is ignored
        """
        current_timeout = self.timeout
        super().settimeout(timeout)
        data_length = b""
        while len(data_length) < 120:
            try:
                received = super().recv(120 - len(data_length))
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
                received = super().recv(data_length - len(data))
                data += received
                if received == b"":  # connection closed
                    return b""
            except socket.timeout:  # return only if received nothing
                if data == b"":
                    return b""
        super().settimeout(current_timeout)
        return data

    def accept(self) -> tuple[ProtocolSocket, tuple[str, str]]:
        """accept() -> (socket object, address info)

        Wait for an incoming connection.  Return a new socket
        representing the connection, and the address of the client.
        For IP sockets, the address info is a pair (hostaddr, port).
        """
        #
        """
            copied from socket.py (the built-in socket module), only changed to 
            create a new ProtocolSocket instead of creating a new regular socket
        """
        fd, addr = super()._accept()
        sock = ProtocolSocket(self.family, self.type, self.proto, fileno=fd)
        # Issue #7995: if no default timeout is set and the listening
        # socket had a (non-zero) timeout, force the new socket in blocking
        # mode to override platform-specific socket flags inheritance.
        if getdefaulttimeout() is None and self.gettimeout():
            sock.setblocking(True)
        return sock, addr

    # override all the methods that send or receive data
    def send(self, *args, **kwargs):
        raise NotImplemented

    def sendto(self, *args, **kwargs):
        raise NotImplemented

    def sendfile(self, *args, **kwargs):
        raise NotImplemented

    def sendall(self, *args, **kwargs):
        raise NotImplemented

    def sendmsg(self, *args, **kwargs):
        raise NotImplemented

    def sendmsg_afalg(self, *args, **kwargs):
        raise NotImplemented

    def recv(self, *args, **kwargs):
        raise NotImplemented

    def recvmsg(self, *args, **kwargs):
        raise NotImplemented

    def recvfrom(self, *args, **kwargs):
        raise NotImplemented

    def recv_into(self, *args, **kwargs):
        raise NotImplemented

    def recvfrom_into(self, *args, **kwargs):
        raise NotImplemented

    def recvmsg_into(self, *args, **kwargs):
        raise NotImplemented

    def makefile(self, *args, **kwargs):
        raise NotImplemented
