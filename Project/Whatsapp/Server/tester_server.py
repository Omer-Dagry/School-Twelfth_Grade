import socket
import threading
import traceback

from protocol_socket import EncryptedProtocolSocket


# Constants
CHUNK = 1024 * 2
BUFFER_SIZE = CHUNK * 4

# Globals
lock = threading.Lock()
addr_to_chat_id: dict[tuple[str, int], str] = {}
chat_id_to_addrs: dict[str, list[tuple[str, int]]] = {}


def broadcast_audio(server_sock_udp: EncryptedProtocolSocket, data: bytes,
                    sent_from_addr: tuple[str, int] | tuple[None, None]) -> None:
    remove = []
    lock.acquire()
    chat_id = addr_to_chat_id[sent_from_addr]
    clients = chat_id_to_addrs[chat_id].copy()
    lock.release()
    for addr in clients:
        try:
            if addr != sent_from_addr and data != b"":
                server_sock_udp.sendto(data, addr)
        except TimeoutError:
            print(f"{addr} timed out")
            remove.append(addr)
    lock.acquire()
    for addr in remove:
        addr_to_chat_id.pop(addr)
        chat_id_to_addrs[chat_id].remove(addr)
    lock.release()


def udp():
    server_sock_udp = EncryptedProtocolSocket(cert_file="private_key_and_crt\\certificate.crt",
                                              key_file="private_key_and_crt\\privateKey.key",
                                              family=socket.AF_INET, type=socket.SOCK_DGRAM, server_side=True)
    server_sock_udp.bind(("0.0.0.0", 8821))
    server_sock_udp.settimeout(0.01)
    while True:
        try:
            data, addr = server_sock_udp.recvfrom(BUFFER_SIZE)
            if addr not in addr_to_chat_id:
                # a message was sent from someone who isn't connected to the TCP socket
                continue
            broadcast_audio(server_sock_udp, data, addr)
        except ConnectionResetError:
            pass
        except socket.timeout:
            broadcast_audio(server_sock_udp, b"", (None, None))
        except Exception as e:
            # traceback.print_exception(e)
            pass


def tcp_connection():
    server_sock_tcp = EncryptedProtocolSocket(cert_file="private_key_and_crt\\certificate.crt",
                                              key_file="private_key_and_crt\\privateKey.key")
    server_sock_tcp.bind(("0.0.0.0", 8820))
    server_sock_tcp.listen()
    clients: dict[EncryptedProtocolSocket, tuple[str, int]] = {}
    addr_status: dict[tuple[str, int], bool] = {}
    server_sock_tcp.settimeout(0.01)
    while True:
        try:
            client_sock, addr = server_sock_tcp.accept()
            clients[client_sock] = addr
        except TimeoutError:
            pass
        for client in clients.keys():
            if not addr_status[clients[client]]:
                msg = client.receive_message()
                if msg.startswith(b"login".ljust(30)):
                    # TODO: check username and password and chat_id
                    # username_length
                    # username
                    # password (md5) length known
                    # chat_id (the rest of the message)
                    #
                    lock.acquire()
                    # if chat_id in chat_id_to_addrs:
                    #     chat_id_to_addrs[chat_id].append(clients[client])
                    # else:
                    #     chat_id_to_addrs[chat_id] = [clients[client]]
                    # addr_to_chat_id[clients[client]] = chat_id
                    lock.release()
                elif msg.startswith(b"check in".ljust(30)):
                    # check in every x seconds to make sure the client is still
                    # connected on the udp as well, if not cut connection with them
                    pass
                else:
                    client.close()
                    addr_status.pop(clients[client])
                    clients.pop(client)


def main():
    tcp_thread = threading.Thread(target=tcp_connection, daemon=True)
    tcp_thread.start()
    udp()


if __name__ == '__main__':
    main()
