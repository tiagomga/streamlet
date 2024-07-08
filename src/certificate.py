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


    def check_validity(self, block, public_keys, min_votes):
        valid_votes = 0
        iterated_senders = []
        for sender, signature in self.votes:
            if sender not in iterated_senders:
                iterated_senders.append(sender)
                try:
                    hash_algorithm = rsa.verify(block.to_bytes(), signature, public_keys[sender])
                    if hash_algorithm == 'SHA-256':
                        valid_votes += 1
                except rsa.VerificationError:
                    continue
        return valid_votes >= min_votes
