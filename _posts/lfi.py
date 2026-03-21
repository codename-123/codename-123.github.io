import socket
import paramiko

class SSHServer(paramiko.ServerInterface):
    def check_auth_password(self, username, password):
        print(f"{username}:{password}")
        return paramiko.AUTH_SUCCESSFUL

server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind(('0.0.0.0', 2222))
server_socket.listen(5)

server_key = paramiko.RSAKey.generate(2048)

client_sock, addr = server_socket.accept()

transport = paramiko.Transport(client_sock)
transport.add_server_key(server_key)
server = SSHServer()
transport.start_server(server=server)

while True:
    channel = transport.accept(20)
    if channel is None:
        continue
    print("Client connected!")
    channel.close()