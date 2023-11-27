import rsa
import time
from communicationsystem import CommunicationSystem
from message import Message

class Server:

    def __init__(self, servers_configuration, id):
        self.id = id
        self.servers_configuration = servers_configuration
        self.communication = CommunicationSystem(id, servers_configuration)
        self.public_key, self.private_key = rsa.newkeys(512)


    def run(self):
        """
        Start server execution.
        """
        self.communication.start()
        
        # Test for communication between replicas
        try:
            time.sleep(5)
            data = f"Hey (from replica {self.id})"
            m = Message(None, data, self.id)
            m_byte = Message.to_bytes(m)
            self.communication.send(m_byte)
        except Exception:
            pass
        self.show_queue()


    def show_queue(self):
        """
        Debug method to see what's in the queue.
        """
        result = []
        while not self.communication.received_queue.empty():
            result.append(self.communication.received_queue.get().__str__())
        for i in result:
            self.communication.received_queue.put(i)
        print(result)