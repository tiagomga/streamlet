import selectors
import logging
import socket
from multiprocessing import Process, Queue
from message import Message
from messagetype import MessageType

class CommunicationSystem:
    """
    Manages communication between replicas.
    """

    def __init__(self, server_id: int, configuration: dict) -> None:
        """
        Constructor.

        Args:
            server_id (int): id of the server/replica
            configuration (dict): configuration settings that contains servers' IP, port and socket
        """
        self.configuration = configuration
        self.server_id = server_id
        self.selector = None
        self.ip = configuration[server_id][0]
        self.port = configuration[server_id][1]
        self.socket = configuration[server_id][2]
        self.received_queue = Queue()
    

    def send(self, message: Message, server_id: int) -> None:
        """
        Send `message` to server with `server_id`.

        Args:
            message (Message): message to send
            server_id (int): id of receiving server
        """
        receiver_info = self.configuration[server_id]
        receiver_address = (receiver_info[0], receiver_info[1])
        sender_socket = receiver_info[2]
        try:
            sender_socket.send(message)
        # Handle server disconnection
        except BrokenPipeError:
            logging.error(f"Server {server_id} disconnected.\n")
            self.configuration.pop(server_id)
        # Connect to server before sending data, if it is the first time
        except OSError:
            sender_socket.connect(receiver_address)
            sender_socket.send(message)


    def broadcast(self, message: Message) -> None:
        """
        Broadcast `message` to every server.

        Args:
            message (Message): message to broadcast
        """
        for id in list(self.configuration.keys()):
            if id != self.server_id:
                self.send(message, id)


    def receive(self, socket: socket.socket) -> None:
        """
        Handles receiving messages from all replicas.

        Args:
            socket (Socket): socket for receiving data
        """
        data = socket.recv(2048)
        if data:
            message = Message.from_bytes(data)
            self.received_queue.put(message)
            # Print received data
            logging.debug(f"Received message - {Message.from_bytes(data)}")


    def accept(self, socket: socket.socket) -> None:
        """
        Accept new connections.

        Args:
            socket (Socket): current server socket
        """
        connection_socket, connection_address = socket.accept()
        connection_socket.setblocking(False)
        self.selector.register(connection_socket, selectors.EVENT_READ, self.receive)


    def listen(self) -> None:
        """
        Listen for new or existing connections.
        """
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.socket, selectors.EVENT_READ, self.accept)
        try:
            while True:
                events = self.selector.select()
                for key, mask in events:
                    callback = key.data
                    callback(key.fileobj)
        except KeyboardInterrupt:
            self.selector.close()


    def start(self) -> None:
        """
        Prepare socket for listening to connections and launch process to handle all received data.
        """
        self.socket.bind((self.ip, self.port))
        self.socket.listen(100)
        self.socket.setblocking(False)
        receiver_process = Process(target=self.listen)
        receiver_process.start()


    def get_message(self, timeout: float | None) -> Message:
        return self.received_queue.get(timeout=timeout)