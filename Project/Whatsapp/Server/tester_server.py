import os

from protocol_socket import EncryptedProtocolSocket


def main():
    s = EncryptedProtocolSocket(cert_file=os.path.abspath("private_key_and_crt\\certificate.crt"),
                                key_file=os.path.abspath("private_key_and_crt\\privateKey.key"),
                                server_side=True)
    s.bind(("0.0.0.0", 8820))
    s.listen()
    c_sock, c_ip_port = s.accept()
    print(c_ip_port)
    print(c_sock.receive_message())
    c_sock.close()
    s.close()


if __name__ == '__main__':
    main()
