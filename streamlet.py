class Streamlet:
    """
    Streamlet protocol.
    """

    def __init__(self, server_id, num_replicas=4):
        """
        Constructor.
        """
        self.server_id = server_id
        self.epoch = 0
        self.num_replicas = num_replicas


    def start_new_epoch(self, block):
        epoch_leader = self.get_epoch_leader()
        if epoch_leader == self.server_id:
            self.propose(block)
        else:
            self.vote(block)


    def propose(self, block):
        #TODO
        pass


    def vote(self, block):
        #TODO
        pass


    def finalize(self, block):
        #TODO
        pass


    def get_epoch_leader(self):
        return self.epoch % self.num_replicas