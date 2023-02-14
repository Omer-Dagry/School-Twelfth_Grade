import base64
import hashlib

from typing import *
from Crypto import Random
from Crypto.Cipher import AES


class AESCipher:
    def __init__(self, key):
        self.bs = AES.block_size
        self.key = hashlib.sha256(key.encode()).digest()

    def encrypt(self, raw: str, file_data: bytes = None) -> bytes:
        raw = self.to_ascii_values(raw)
        if file_data is None:
            raw = self.pad(raw.encode())
        else:
            file_data = b"file:" + file_data
            raw = self.pad(raw.encode() + file_data)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return base64.b64encode(iv + cipher.encrypt(raw))

    def decrypt(self, enc: bytes) -> tuple[str, Union[bytes, None]]:
        if enc == b"":
            return "", None
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self.to_ascii_chars(self.unpad(cipher.decrypt(enc[AES.block_size:])))

    def pad(self, s: Union[str, bytes]) -> Union[str, bytes]:
        if s is str:
            return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)
        else:
            return s + (self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs).encode()

    @staticmethod
    def unpad(s: Union[str, bytes]) -> Union[str, bytes]:
        return s[:-ord(s[len(s)-1:])]

    @staticmethod
    def to_ascii_values(data: str) -> str:
        data_ascii = [str(ord(char)) for char in data]
        return ",".join(data_ascii)

    @staticmethod
    def to_ascii_chars(data_ascii: bytes) -> tuple[str, Union[bytes, None]]:
        if b"file:" in data_ascii:
            file_data = b"file:".join(data_ascii.split(b"file:")[1:])  # get file data
            list_data_ascii = data_ascii.split(b"file:")[0].decode().split(",")  # get msg metadata
            return "".join([chr(int(char)) for char in list_data_ascii if char != ""]), file_data[5:]
        else:
            list_data_ascii = data_ascii.decode().split(",")
            return "".join([chr(int(char)) for char in list_data_ascii if char != ""]), None
