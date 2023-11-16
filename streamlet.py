class Streamlet:
    """
    Streamlet protocol.
    """

    def __init__(self):
        """
        Constructor.
        """
        self.epoch = 0


    def start_new_epoch(self):
        #TODO
        pass


    def propose(self, block):
        #TODO
        pass


    def vote(self, block):
        #TODO
        pass


    def finalize(self, block):
        #TODO
        pass