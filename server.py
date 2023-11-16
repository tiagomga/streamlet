import rsa
from multiprocessing import Process, Queue
from communicationsystem import CommunicationSystem
import time

class Server:

    def __init__(self, servers_configuration, id):
        # Server information
        self.id = id
        self.servers_configuration = servers_configuration
        self.communication = CommunicationSystem(id, servers_configuration)

        # Protocol information
        self.epoch = 0
        self.public_key, self.private_key = rsa.newkeys(512)

        # Queues
        self.receive_queue = Queue()
        self.send_queue = Queue()
        

    def get_epoch_leader(self):
        return self.get_current_epoch() % Server.total_servers
    

    def get_current_epoch(self):
        return self.epoch
    
    
    def run(self):
        self.communication.start()