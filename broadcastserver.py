import socket

class BroadcastServer:

    log = []

    def __init__(self, host="127.0.0.1", port=50000):
        self.host = host
        self.port = port

    def run(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((self.host, self.port))
            s.listen(1)
            client, addr = s.accept()
            with client:
                while True:
                    data = client.recv(1024)
                    if data:
                        BroadcastServer.log.append(data.decode())
                        self.broadcast(data)
                        client, addr = s.accept()

    def broadcast(self, message, port=20000, num_servers=4):
        for i in range(1, num_servers+1):
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.connect((self.host, port+i))
                s.sendall(message)