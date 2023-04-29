import rsa
import socket
import multiprocessing

from aes import AESCipher
from protocol_socket import EncryptedProtocolSocket


def recvall(buffsize: int, sock: socket.socket) -> bytes:
    data = b""
    while len(data) < buffsize:
        data += sock.recv(buffsize - len(data))
    return data


def recv_message(sock: socket.socket, aes: AESCipher) -> bytes:
    data_length = int(recvall(30, sock).decode().strip())
    return aes.decrypt(recvall(data_length, sock))


def recvall_no_encryption(buffsize: int, sock: socket.socket) -> bytes:
    data = b""
    while len(data) < buffsize:
        data += sock.recv(buffsize - len(data))
    return data


def send_message(data: bytes, sock: socket.socket, aes: AESCipher) -> None:
    data = aes.encrypt(data)
    sock.sendall(f"{len(data)}".ljust(30).encode())
    sock.sendall(data)


def exchange_aes_key(my_public_key: rsa.PublicKey, my_private_key: rsa.PrivateKey,
                     sock: socket.socket) -> bytes:
    my_public_key_bytes = my_public_key.save_pkcs1("PEM")
    sock.sendall(f"{len(my_public_key_bytes)}".ljust(30).encode() + my_public_key_bytes)
    aes_key_len = int(recvall_no_encryption(30, sock).decode().strip())
    aes_key_encrypted = recvall_no_encryption(aes_key_len, sock)
    return rsa.decrypt(aes_key_encrypted, my_private_key)


def main_regular():
    s = socket.socket()
    s.bind(("0.0.0.0", 8820))
    s.listen()
    my_public_key, my_private_key = rsa.newkeys(2048, poolsize=multiprocessing.cpu_count())
    print("done generating")
    client_sock, client_ip_port = s.accept()
    print(client_ip_port)
    aes_key = exchange_aes_key(my_public_key, my_private_key, client_sock)
    aes_cipher = AESCipher(aes_key)
    print(aes_key)
    print("finished exchanging")
    msg = recv_message(client_sock, aes_cipher)
    print(f"{len(msg) = }")
    send_message(msg, client_sock, aes_cipher)
    client_sock.close()
    s.close()


def main():
    s = EncryptedProtocolSocket(cert_file="private_key_and_crt\\certificate.crt",
                                key_file="private_key_and_crt\\privateKey.key",
                                server_side=True)
    s.bind(("0.0.0.0", 8820))
    s.listen()
    client_sock, client_ip_port = s.accept()
    msg = client_sock.receive_message()
    print(f"{len(msg) = }")
    client_sock.send_message(msg)
    client_sock.close()
    s.close()


if __name__ == '__main__':
    main_regular()

