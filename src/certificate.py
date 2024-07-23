import pickle
from typing import Self
import crypto
from block import Block

class Certificate:
    """
    Certificate for the freshest notarized block, containing a
    quorum of votes.
    """

    def __init__(self, block: Block | None = None) -> None:
        """
        Constructor.

        Args:
            block (Block, optional): block to create certificate from. Defaults to None.
        """
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


    def get_epoch(self) -> int:
        """
        Get certificate's epoch.

        Returns:
            int: epoch number
        """
        return self.epoch


    def extends_freshest_chain(self, block: Block) -> bool:
        """
        Check if the certificate is for the freshest `block` (that is being extended).

        Args:
            block (Block): freshest block

        Returns:
            bool: True, if and only if the certificate is for the freshest block, else return False
        """
        return self.epoch == block.get_epoch() and self.block_hash == block.get_hash()


    def check_validity(self, public_keys: dict, min_votes: int) -> bool:
        """
        Check if the certificate's votes are valid.

        Args:
            public_keys (dict): dictionary containing servers' public keys
            min_votes (int): minimum number of valid votes required to consider the certificate as valid

        Returns:
            bool: True, if and only if the certificate contains valid `min_votes` votes, else return False
        """
        valid_votes = 0
        iterated_senders = []
        for sender, signature in self.votes:
            if sender not in iterated_senders:
                iterated_senders.append(sender)
                if crypto.verify_signature(signature, self.block_hash, public_keys[sender]):
                    valid_votes += 1
        return valid_votes >= min_votes


    def to_bytes(self) -> bytes:
        """
        Convert Certificate to bytes.

        Returns:
            bytes: bytes from Certificate object.
        """
        data = (self.epoch, self.block_hash, self.votes)
        return pickle.dumps(data)


    @staticmethod
    def from_bytes(bytes: bytes) -> Self:
        """
        Convert bytes to Certificate.

        Args:
            bytes (bytes): Certificate in serialized form

        Returns:
            Certificate: Certificate object from bytes
        """
        data = pickle.loads(bytes)
        certificate = Certificate()
        certificate.epoch = data[0]
        certificate.block_hash = data[1]
        certificate.votes = data[2]
        return certificate