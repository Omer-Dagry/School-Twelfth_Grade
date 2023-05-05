import os
import rsa
import socket

from aes import AESCipher


class ClientEncryptedProtocolSocket:
    def __init__(self, family: socket.AddressFamily | int = None, type: socket.SocketKind | int = None,
                 proto: int = None, fileno: int | None = None):
        kwargs = {"family": family, "type": type, "proto": proto, "fileno": fileno}
        kwargs = {key_word: arg for key_word, arg in kwargs.items() if arg is not None}
        self.__sock = socket.socket(**kwargs)
        self.__aes_key = os.urandom(16)
        self.__aes_cipher = AESCipher(self.__aes_key)
        self.settimeout(10)

    # Public:

    def recv_message(self, timeout: int = None) -> bytes:
        current_timeout = self.__sock.timeout
        self.settimeout(timeout)
        data_length = b""
        while len(data_length) != 30:
            try:
                data_length += self.__recvall(30 - len(data_length))
            except socket.timeout:
                if data_length == b"":
                    return b""
        data_length = int(data_length.decode().strip())
        data = b""
        while len(data) != data_length:
            try:
                data += self.__recvall(data_length - len(data))
            except socket.timeout:
                if data_length == b"":
                    return b""
        self.settimeout(current_timeout)
        return self.__aes_cipher.decrypt(data)

    def send_message(self, data: bytes) -> bool:
        try:
            data = self.__aes_cipher.encrypt(data)
            self.__sock.sendall(f"{len(data)}".ljust(30).encode())
            self.__sock.sendall(data)
        except ConnectionError:
            return False
        return True

    def connect(self, address: tuple[str, int]) -> None:
        self.__sock.connect(address)
        self.__exchange_aes_key()

    def settimeout(self, __value: float | None) -> None:
        return self.__sock.settimeout(__value)

    def get_timeout(self) -> float | None:
        return self.__sock.timeout

    def getpeername(self) -> tuple[str, int]:
        return self.__sock.getpeername()

    def close(self):
        try:
            self.settimeout(1)
            self.send_message(b"bye")
        except (ConnectionError, socket.error):
            pass
        self.__sock.close()

    # Private:

    def __recvall(self, buffsize: int) -> bytes:
        data = b""
        while len(data) < buffsize:
            data += self.__sock.recv(buffsize - len(data))
        return data

    # Exchange the random aes key using server public key
    def __recvall_no_encryption(self, buffsize: int) -> bytes:
        data = b""
        while len(data) < buffsize:
            data += self.__sock.recv(buffsize - len(data))
        return data

    def __exchange_aes_key(self) -> None:
        server_public_key_len = int(self.__recvall_no_encryption(30).decode().strip())
        server_public_key = rsa.PublicKey.load_pkcs1(self.__recvall_no_encryption(server_public_key_len), "PEM")
        #
        enc_key = rsa.encrypt(self.__aes_key, server_public_key)
        self.__sock.sendall(f"{len(enc_key)}".ljust(30).encode() + enc_key)
