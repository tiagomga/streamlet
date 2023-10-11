import socket
import rsa
from block import Block

class Server:

    total_servers = 0

    def __init__(self):
        self.id = 0
        self.epoch = 0
        self.public_key, self.private_key = rsa.newkeys(512)
        Server.total_servers += 1

    def get_epoch_leader(self):
        return self.get_current_epoch() % Server.total_servers
    
    def get_current_epoch(self):
        return self.epoch