import pickle
import logging
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
            self.votes = [(sender, vote.get_signature()) for sender, vote in block.get_votes()]


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
        return pickle.dumps((self.epoch, self.block_hash, self.votes))


    @staticmethod
    def from_bytes(data_bytes: bytes) -> Self:
        """
        Convert bytes to Certificate.

        Args:
            data_bytes (bytes): Certificate in serialized form

        Returns:
            Certificate: Certificate object from bytes
        """
        try:
            data = pickle.loads(data_bytes)
        except pickle.PickleError:
            logging.error("Certificate cannot be unpickled.\n")
            return None
        try:
            epoch, block_hash, votes = data
        except ValueError:
            logging.error("Attributes cannot be unpacked from tuple.\n")
            return None
        if isinstance(epoch, int) and isinstance(block_hash, str) and isinstance(votes, list):
            certificate = Certificate()
            certificate.epoch = epoch
            certificate.block_hash = block_hash
            for vote in votes:
                if isinstance(vote, tuple) and len(vote) == 2:
                    if not (isinstance(vote[0], int) and isinstance(vote[1], str)):
                        logging.error("Block vote does not contain the correct type(s).\n")
                        return None
                else:
                    logging.error("Block votes are not in the correct format.\n")
                    return None
            certificate.votes = votes
            return certificate
        logging.error("Certificate attributes do not contain the correct type(s).\n")
        return None