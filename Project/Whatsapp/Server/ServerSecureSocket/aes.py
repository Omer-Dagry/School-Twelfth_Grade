import hashlib

from Crypto import Random
from Crypto.Cipher import AES


class AESCipher:
    """ a class to wrap the AES encryption and decryption """
    def __init__(self, key: str | bytes):
        self.bs = AES.block_size
        key = key.encode() if isinstance(key, str) else key
        self.key = hashlib.sha256(key).digest()

    def encrypt(self, raw: bytes) -> bytes:
        raw = self._pad(raw)
        iv = Random.new().read(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        # return base64.b64encode(iv + cipher.encrypt(raw))
        return iv + cipher.encrypt(raw)

    def decrypt(self, enc: bytes) -> bytes:
        # enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        return self._unpad(cipher.decrypt(enc[AES.block_size:]))

    def _pad(self, s: bytes) -> bytes:
        return s + ((self.bs - len(s) % self.bs) * chr(self.bs - len(s) % self.bs)).encode()

    @staticmethod
    def _unpad(s: bytes) -> bytes:
        return s[:-s[-1]]
