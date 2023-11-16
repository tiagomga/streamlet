import rsa
from multiprocessing import Process, Queue
from communicationsystem import CommunicationSystem
import time

class Server:

    def __init__(self, servers_configuration, id):
        self.id = id
        self.servers_configuration = servers_configuration
        self.communication = CommunicationSystem(id, servers_configuration)
        self.public_key, self.private_key = rsa.newkeys(512)


    def run(self):
        self.communication.start()