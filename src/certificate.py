import pickle
import crypto

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


    def check_validity(self, block, public_keys, min_votes):
        valid_votes = 0
        iterated_senders = []
        for sender, signature in self.votes:
            if sender not in iterated_senders:
                iterated_senders.append(sender)
                if crypto.verify_signature(signature, block.get_hash(), public_keys[sender]):
                    valid_votes += 1
        return valid_votes >= min_votes


    def to_bytes(self):
        data = (self.epoch, self.block_hash, self.votes)
        return pickle.dumps(data)


    @staticmethod
    def from_bytes(bytes):
        data = pickle.loads(bytes)
        certificate = Certificate()
        certificate.epoch = data[0]
        certificate.block_hash = data[1]
        certificate.votes = data[2]
        return certificate