import rsa
import pickle

class Certificate:
    """
    Certificate for the freshest notarized block, containing a
    quorum of votes.
    """

    def __init__(self, block=None):
        if block is None:
            self.epoch = 0
            self.block_hash = ""
            self.votes = []
        else:
            self.epoch = block.get_epoch()
            self.block_hash = block.get_hash()
            self.votes = []
            for sender, vote in block.get_votes():
                self.votes.append((sender, vote.get_signature()))


    def extends_freshest_chain(self, block):
        return self.epoch == block.get_epoch() and self.block_hash == block.get_hash()
