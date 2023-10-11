from server import Server

class Streamlet:

    def __init__(self, number_servers=4):
        self.number_servers = number_servers

    def run(self):
        for _ in range(self.number_servers):
            Server()