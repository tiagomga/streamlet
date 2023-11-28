import selectors
from multiprocessing import Process, Queue
from threading import Thread
from message import Message
from messagetype import MessageType

class CommunicationSystem:
    """
    Manages communication between replicas.
    """

    def __init__(self, server_id, configuration):
        """
        Constructor.

        Args:
            server_id (int): id of the server/replica
            configuration (dict): configuration settings that contains servers' IP, port and socket
        """
        self.configuration = configuration
        self.server_id = server_id
        self.selector = selectors.DefaultSelector()
        self.ip = configuration[server_id][0]
        self.port = configuration[server_id][1]
        self.socket = configuration[server_id][2]
        self.received_queue = Queue()
    

    def send(self, message, num_servers=4):
        """
        Handles sending messages to all replicas.

        Args:
            message (Message): message to send
            num_servers (int): number of servers
        """
        # Establish connection with the receivers and send message
        for i in range(num_servers):
            if i != self.server_id:
                receiver_info = self.configuration[i]
                receiver_address = (receiver_info[0], receiver_info[1])
                sender_socket = receiver_info[2]
                try:
                    sender_socket.send(message)
                except OSError:
                    sender_socket.connect(receiver_address)
                    sender_socket.send(message)
                except ConnectionRefusedError:
                    # Handle refused connections
                    pass
    
    
    def receive(self, socket):
        """
        Handles receiving messages from all replicas.

        Args:
            socket (Socket): socket for receiving data
        """
        data = socket.recv(1024)
        if data:
            self.received_queue.put(Message.from_bytes(data))
            # Print received data
            print(Message.from_bytes(data))


    def accept(self, socket):
        """
        Accept new connections.

        Args:
            socket (Socket): current server socket
        """
        connection_socket, connection_address = socket.accept()
        connection_socket.setblocking(False)
        self.selector.register(connection_socket, selectors.EVENT_READ, self.receive)


    def listen(self):
        """
        Listen for new or existing connections.
        """
        while True:
            events = self.selector.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj)


    def start(self):
        """
        Prepare socket for listening to connections and launch process to handle all received data.
        """
        self.socket.bind((self.ip, self.port))
        self.socket.listen(100)
        self.socket.setblocking(False)
        self.selector.register(self.socket, selectors.EVENT_READ, self.accept)
        receiver_process = Thread(target=self.listen)
        receiver_process.start()


    def get_public_keys(self):
        """
        Get public keys from all servers.

        Returns:
            dict: dictionary with ID of the server as key and PublicKey as value
        """
        public_keys = {}
        while len(public_keys) != 3:
            message = self.received_queue.get()
            sender = message.get_sender()
            content = message.get_content()
            public_keys[sender] = content
        return public_keys


    def get_proposed_block(self, current_epoch):
        """
        Get proposed block for the current epoch.

        Args:
            current_epoch (int): current epoch

        Returns:
            tuple: tuple with ID of the sender/leader and proposed block
        """
        while True:
            message = self.received_queue.get()
            block_epoch = message.get_content().get_epoch()

            # Accept only propose messages
            if message.get_type() != MessageType.PROPOSE:
                self.received_queue.put(message)
                continue

            # Accept only proposed blocks from current epoch
            if block_epoch == current_epoch:
                return (message.get_sender(), message.get_content())
            else:
                self.received_queue.put(message)


    def get_votes(self, current_epoch, f):
        """
        Get 2f votes from the current epoch.

        Args:
            current_epoch (int): current epoch
            f (int): number of faults

        Returns:
            tuple: tuple with ID of the sender and vote
        """
        votes = []
        while len(votes) < 2*f:
            message = self.received_queue.get()
            block_epoch = message.get_content().get_epoch()

            # Accept only vote messages
            if message.get_type() != MessageType.VOTE:
                self.received_queue.put(message)
                continue

            # Accept only votes from current epoch
            if block_epoch == current_epoch:
                votes.append((message.get_sender(), message.get_content()))
            else:
                self.received_queue.put(message)
        return votes