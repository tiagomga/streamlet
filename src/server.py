import time
import logging
import crypto
from message import Message
from streamlet import Streamlet
from messagetype import MessageType
from communicationsystem import CommunicationSystem

class Server:

    def __init__(self, servers_configuration: dict, id: int) -> None:
        """
        Constructor.

        Args:
            servers_configuration (dict): dictionary that contains \
            information about every server (host, port and socket)
            id (int): server's ID
        """
        self.id = id
        self.servers_configuration = servers_configuration
        self.communication = CommunicationSystem(id, servers_configuration)
        self.public_key, self.private_key = crypto.generate_keys()
        self.servers_public_key = {}


    def exchange_public_keys(self) -> None:
        """
        Exchange public keys between all servers.
        """
        # Send public key to every server
        public_key = Message(
            MessageType.PK_EXCHANGE,
            crypto.serialize_public_key(self.public_key),
            self.id
        ).to_bytes()
        self.communication.send(public_key)

        # Receive and store other servers' public keys
        logging.info("Getting public keys from other servers...\n")
        self.servers_public_key[self.id] = self.public_key
        num_replicas = len(self.servers_configuration)
        while len(self.servers_public_key) != num_replicas:
            message = self.communication.get_message(timeout=None)
            sender = message.get_sender()
            received_public_key = crypto.load_public_key(message.get_content())
            self.servers_public_key[sender] = received_public_key
        logging.info("Public keys were retrieved successfully.\n")


    def run(self) -> None:
        """
        Start server execution.
        """
        self.communication.start()
        time.sleep(1)
        self.exchange_public_keys()
        protocol = Streamlet(self.id, self.communication, self.private_key, self.servers_public_key)
        protocol.start()


    def show_queue(self) -> None:
        """
        Debug method to see what's in the queue.
        """
        result = []
        while not self.communication.received_queue.empty():
            result.append(self.communication.received_queue.get().__str__())
        for i in result:
            self.communication.received_queue.put(i)
        print(result)