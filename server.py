import socket
import rsa
from block import Block

class Server:

    total_servers = 0
    log = []

    def __init__(self):
        self.id = 0
        self.epoch = 0
        self.public_key, self.private_key = rsa.newkeys(512)
        Server.total_servers += 1

    def get_epoch_leader(self):
        return self.get_current_epoch() % Server.total_servers
    
    def get_current_epoch(self):
        return self.epoch
    
    def run(self, host="127.0.0.1", port=50000):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind((host, port))
            s.listen(1)
            client, addr = s.accept()
            with client:
                while True:
                    data = client.recv(1024)
                    if data:
                        Server.log.append(data.decode())
                        client, addr = s.accept()