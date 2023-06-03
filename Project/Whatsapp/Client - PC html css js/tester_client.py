from ClientSecureSocket import ClientEncryptedProtocolSocket


for _ in range(200):
    sock = ClientEncryptedProtocolSocket()
    sock.connect(("127.0.0.1", 8820))
    sock.send_message(b"unknown")
    sock.close()
