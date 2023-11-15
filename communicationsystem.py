import multiprocessing
import selectors

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
    

    def send(self, message, num_servers=4):
        """
        Handles sending messages to all replicas.

        Args:
            message (Message): message to send
            num_servers (int): number of servers
        """
        # Get address (IP and port) and socket from sender
        sender_info = self.configuration[self.server_id]
        sender_socket = sender_info[2]

        # Establish connection with the receivers and send message
        for i in range(num_servers):
            if i != self.server_id:
                receiver_info = self.configuration[i]
                receiver_address = (receiver_info[0], receiver_info[1])
                try:
                    sender_socket.send(message)
                except BrokenPipeError:
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
            self.received_queue.put(data.decode())


    def accept(self, socket):
        connection_socket, connection_address = socket.accept()
        connection_socket.setblocking(False)
        self.selector.register(connection_socket, selectors.EVENT_READ, self.receive)


    def listen(self):
        while True:
            events = self.selector.select()
            for key, mask in events:
                callback = key.data
                callback(key.fileobj)


    def start(self):
        multiprocessing.set_start_method("fork")
        receiver_process = multiprocessing.Process(target=self.listen)
        receiver_process.start()