import socket
import rsa
from multiprocessing import Process, Queue
from block import Block
from communicationsystem import CommunicationSystem

class Server:

    total_servers = 0
    log = []

    def __init__(self, servers_configuration, id):
        # Server information
        self.id = id
        self.servers_configuration = servers_configuration
        self.communication = CommunicationSystem(id, servers_configuration)
        self.ip = servers_configuration[id][0]
        self.port = servers_configuration[id][1]
        self.socket = servers_configuration[id][2]
        self.socket.bind((self.ip, self.port))

        # Protocol information
        self.epoch = 0
        self.public_key, self.private_key = rsa.newkeys(512)

        # Queues
        self.receive_queue = Queue()
        self.send_queue = Queue()

        Server.total_servers += 1

    def get_epoch_leader(self):
        return self.get_current_epoch() % Server.total_servers
    
    def get_current_epoch(self):
        return self.epoch
    
    def run(self):
        receiver_process = Process(target=self.receive)
        receiver_process.start()

        protocol_process = Process(target=self.start_new_epoch)
        protocol_process.start()


    def receive(self):
        print(f"Server {self.id} is ready to receive.")
        self.communication.receive(self.receive_queue)