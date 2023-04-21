import socket

s = socket.socket()
s.bind(("0.0.0.0", 8822))
s.listen()

client_sock, client_addr = s.accept()
print(client_addr)

