from __future__ import annotations

import rsa
import socket

from aes import AESCipher


class AESKeyMissing(Exception):
    """ Raised when there is an attempt to send or receive data and '__exchange_aes_key' wasn't called yet """


class ServerEncryptedProtocolSocket:
    def __init__(self, my_public_key: rsa.PublicKey, my_private_key: rsa.PrivateKey,
                 family: socket.AddressFamily | int = None, type: socket.SocketKind | int = None,
                 proto: int = None, fileno: int | None = None, sock: socket.socket = None):
        self.__my_public_key: rsa.PublicKey = my_public_key
        self.__my_private_key: rsa.PrivateKey = my_private_key
        #
        self.__aes_key: None | bytes = None
        self.__aes_cipher: None | AESCipher = None
        if sock is None:
            kwargs = {"family": family, "type": type, "proto": proto, "fileno": fileno}
            kwargs = {key_word: arg for key_word, arg in kwargs.items() if arg is not None}
            self.__sock = socket.socket(**kwargs)
        else:
            self.__sock = sock
            self.__exchange_aes_key()

    # Public:

    def recv_message(self, timeout: int = None) -> bytes:
        if self.__aes_cipher is None:
            raise AESKeyMissing("aes_cipher is None, please call connect before calling recv_message")
        current_timeout = self.__sock.timeout
        self.settimeout(timeout)
        data_length = b""
        while len(data_length) != 30:
            try:
                res = self.__recvall(30 - len(data_length))
                data_length += res
                if res == b"":  # connection closed
                    return res
            except socket.timeout:
                if data_length == b"":
                    return b""
        data_length = int(data_length.decode().strip())
        data = b""
        while len(data) != data_length:
            try:
                res = self.__recvall(data_length - len(data))
                data += res
                if res == b"":  # connection closed
                    return res
            except socket.timeout:
                if data_length == b"":
                    return b""
        self.settimeout(current_timeout)
        return self.__aes_cipher.decrypt(data)

    def send_message(self, data: bytes) -> bool:
        if self.__aes_cipher is None:
            raise AESKeyMissing("aes_cipher is None, please call connect before calling send_message")
        try:
            data = self.__aes_cipher.encrypt(data)
            self.__sock.sendall(f"{len(data)}".ljust(30).encode())
            self.__sock.sendall(data)
        except ConnectionError:
            return False
        return True

    def bind(self, __address: tuple[str, int]) -> None:
        return self.__sock.bind(__address)

    def listen(self, __backlog: int = None) -> None:
        args = () if __backlog is None else (__backlog,)
        return self.__sock.listen(*args)

    def accept(self) -> tuple[ServerEncryptedProtocolSocket, tuple[str, int]]:
        client_sock, client_addr = self.__sock.accept()
        return ServerEncryptedProtocolSocket(self.__my_public_key, self.__my_private_key, sock=client_sock), client_addr

    def settimeout(self, __value: float | None) -> None:
        return self.__sock.settimeout(__value)

    def get_timeout(self) -> float | None:
        return self.__sock.timeout

    def getpeername(self) -> tuple[str, int]:
        return self.__sock.getpeername()

    def close(self):
        self.__sock.close()

    # Private:

    def __recvall(self, buffsize: int) -> bytes:
        data = b""
        while len(data) < buffsize:
            res = self.__sock.recv(buffsize - len(data))
            data += res
            if res == b"":  # connection closed
                return res
        return data

    # Exchange the random aes key using server public key
    def __recvall_no_encryption(self, buffsize: int) -> bytes:
        data = b""
        while len(data) < buffsize:
            data += self.__sock.recv(buffsize - len(data))
        return data

    def __exchange_aes_key(self) -> None:
        my_public_key_bytes = self.__my_public_key.save_pkcs1("PEM")
        self.__sock.sendall(f"{len(my_public_key_bytes)}".ljust(30).encode() + my_public_key_bytes)
        aes_key_len = int(self.__recvall_no_encryption(30).decode().strip())
        aes_key_encrypted = self.__recvall_no_encryption(aes_key_len)
        self.__aes_key = rsa.decrypt(aes_key_encrypted, self.__my_private_key)
        self.__aes_cipher = AESCipher(self.__aes_key)
