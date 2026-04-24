import socket

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    host = 'localhost'
    port = 8910

    server_socket.bind((host, port))

    server_socket.listen(1)
    print(f"Server is listening on {host}:{port}")

    client_socket, addr = server_socket.accept()
    print(f"Connected to {addr}")

    data = client_socket.recv(1024).decode()
    print(f"Received from client: {data}")

    response = "Hello from server!"
    client_socket.send(response.encode())

    client_socket.close()
    server_socket.close()

if __name__ == "__main__":
    start_server()
