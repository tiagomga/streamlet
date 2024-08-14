import os
import pickle
import json
import logging
from types import NoneType
from typing import Self
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey, RSAPublicKey
import crypto
from blockstatus import BlockStatus

class Block:
    """
    Class that represents a block containing:
    - Hash of the (block) parent hash
    - Set of transactions
    - Epoch number
    """

    def __init__(self, epoch: int, transactions: list, parent_hash: str, parent_epoch: int | None = None) -> None:
        """
        Constructor.

        Args:
            epoch (int): block's epoch
            transactions (list): clients' transactions
            parent_hash (str): hash of the parent block
            parent_epoch (int or None): epoch of the parent block
        """
        self.epoch = epoch
        self.transactions = transactions
        self.hash = None
        self.parent_hash = parent_hash
        self.parent_epoch = parent_epoch
        self.signature = None
        self.votes = []
        self.status = BlockStatus.PROPOSED


    def get_epoch(self) -> int:
        """
        Get block's epoch.

        Returns:
            int: epoch of the block
        """
        return self.epoch


    def get_hash(self) -> str:
        """
        Get block's hash.

        Returns:
            str: hash
        """
        return self.hash


    def get_parent_hash(self) -> str:
        """
        Get block's parent hash.

        Returns:
            str: parent hash
        """
        return self.parent_hash


    def get_status(self) -> BlockStatus:
        """
        Get block's status.

        Returns:
            BlockStatus: block's status
        """
        return self.status


    def get_parent_epoch(self) -> int:
        """
        Get parent block's epoch.

        Returns:
            int: epoch of parent block
        """
        return self.parent_epoch


    def get_votes(self) -> list:
        """
        Get block's votes.

        Returns:
            list: list containing votes
        """
        return self.votes


    def get_signature(self) -> str:
        """
        Get block's signature.

        Returns:
            str: signature
        """
        return self.signature


    def set_signature(self, signature: str) -> None:
        """
        Set block's signature.

        Args:
            signature (str): signature
        """
        self.signature = signature


    def set_parent_epoch(self, parent_epoch: int) -> None:
        """
        Set parent block's epoch.

        Args:
            parent_epoch (int): epoch of parent block
        """
        self.parent_epoch = parent_epoch


    def is_parent(self, block: Self) -> bool:
        """
        Check if this block is parent of the other block.

        Args:
            block (Block): other block to be compared to

        Returns:
            bool: True, if and only if this block is parent of the other block, else return False
        """
        return block.parent_hash == self.hash


    def is_child(self, block: Self) -> bool:
        """
        Check if this block is child of the other block.

        Args:
            block (Block): other block to be compared to

        Returns:
            bool: True, if and only if this block is child of the other block, else return False
        """
        return self.parent_hash == block.hash


    def calculate_hash(self) -> None:
        """
        Calculate block's hash.
        """
        self.hash = crypto.calculate_hash(self.to_bytes())


    def check_validity(self, public_key: RSAPublicKey, epoch: int, longest_notarized_block: Self) -> bool:
        """
        Check block's validity by checking its signature, epoch and if it
        extends from the longest notarized chain.

        Args:
            public_key (RSAPublicKey): server's public key
            epoch (int): epoch number
            longest_notarized_block (Block): latest block from the longest
            notarized chain

        Returns:
            bool: True, if and only if the block meets all conditions, else return False
        """
        # Check block's signature
        self.calculate_hash()
        valid_signature = self.check_signature(public_key)
        if not valid_signature:
            return False
        
        # Check if block's epoch matches with current epoch
        if self.epoch != epoch:
            return False
        
        # Check if block extends from the longest notarized chain
        if not self.is_child(longest_notarized_block):
            return False
        
        # If all previous conditions are met, block is valid
        return True
    

    def sign(self, private_key: RSAPrivateKey) -> None:
        """
        Sign block's data - used by epoch's leader.

        Args:
            private_key (RSAPrivateKey): server's private key
        """
        self.calculate_hash()
        self.signature = crypto.sign_hash(self.hash, private_key)


    def create_vote(self, private_key: RSAPrivateKey) -> Self:
        """
        Create a vote by signing the block with `private_key`.

        Args:
            private_key (RSAPrivateKey): private key

        Returns:
            Block: vote
        """
        signature = crypto.sign(self.to_bytes(), private_key)
        block = Block(
            self.epoch,
            None,
            self.parent_hash,
        )
        block.signature = signature
        return block


    @classmethod
    def check_vote(cls, vote: Self, proposed_block: Self, public_key: RSAPublicKey) -> bool:
        """
        Check if `vote` is valid for `proposed_block` using voter's `public_key`.

        Args:
            vote (Block): vote
            proposed_block (Block): block that the vote refers to
            public_key (RSAPublicKey): public key

        Returns:
            bool: True, if and only if the vote is valid, else return False
        """
        return crypto.verify_signature(vote.signature, proposed_block.hash, public_key)


    def check_signature(self, public_key: RSAPublicKey) -> bool:
        """
        Check block's signature validity.

        Args:
            public_key (RSAPublicKey): server's public key

        Returns:
            bool: True, if and only if block's signature is valid, else return False
        """
        return crypto.verify_signature(self.signature, self.hash, public_key)


    def add_vote(self, vote: tuple) -> None:
        """
        Add vote to the block.

        Args:
            vote (tuple): tuple with ID of the voter and empty Block with signature
        """
        self.votes.append(vote)


    def add_leader_vote(self, server_id: int) -> None:
        """
        Add leader's vote using the existing signature.

        Args:
            server_id (int): id of the leader
        """
        vote = Block(
            self.epoch,
            None,
            self.parent_hash
        )
        vote.signature = self.signature
        self.add_vote((server_id, vote))


    def notarize(self) -> None:
        """
        Change status to notarized.
        """
        self.status = BlockStatus.NOTARIZED


    def finalize(self) -> None:
        """
        Change status to finalized.
        """
        self.status = BlockStatus.FINALIZED


    def write(self, filename: str = f"blockchain/blockchain_{os.getpid()}") -> None:
        """
        Write block to a file.

        Args:
            filename (str, optional): name of the file - defaults to "blockchain"
        """
        data = {
            "epoch": self.epoch,
            "parent_hash": self.parent_hash,
            "transactions": self.transactions
        }
        with open(filename, "a") as blockchain:
            blockchain.write(json.dumps(data) + ",")


    def to_bytes(self, include_signature: bool = False, include_votes: bool = False) -> bytes:
        """
        Convert Block to bytes.

        Args:
            include_signature (bool): if set to True, block's signature
            is included

        Returns:
            bytes: bytes from Block object
        """
        data = [self.parent_hash, self.epoch, self.transactions]
        if include_signature:
            data.append(self.signature)
        if include_votes:
            votes = []
            for sender, vote in self.votes:
                votes.append((sender, vote.to_bytes(include_signature=True)))
            data.append(votes)
            data.append(self.parent_epoch)
        return pickle.dumps(tuple(data))


    @staticmethod
    def from_bytes(data_bytes: bytes) -> Self | None:
        """
        Convert bytes to Block. Additionally, check if instance attributes
        have the correct type.

        Args:
            data_bytes (bytes): Block in serialized form

        Returns:
            Block: Block object from bytes
        """
        try:
            data = pickle.loads(data_bytes)
        except pickle.PickleError:
            logging.error("Block cannot be unpickled.\n")
            return None
        try:
            if len(data) == 6:
                parent_hash, epoch, transactions, signature, votes, parent_epoch = data
            else:
                parent_hash, epoch, transactions, signature = data
                votes = None
                parent_epoch = None
        except ValueError:
            logging.error("Attributes cannot be unpacked from tuple.\n")
            return None
        if (isinstance(parent_hash, str) and isinstance(epoch, int)
                and isinstance(transactions, (list, NoneType))
                and isinstance(signature, str)):
            block = Block(epoch, transactions, parent_hash)
            block.signature = signature
            if votes and parent_epoch:
                if (isinstance(votes, list) and isinstance(parent_epoch, int)):
                    deserialized_votes = []
                    for vote in votes:
                        if isinstance(vote, tuple) and len(vote) == 2:
                            if isinstance(vote[0], int) and isinstance(vote[1], bytes):
                                deserialized_vote = Block.from_bytes(vote[1])
                                if deserialized_vote is None:
                                    logging.error("Block vote cannot be deserialized.\n")
                                    return None
                                deserialized_votes.append((vote[0], deserialized_vote))
                            else:
                                logging.error("Block vote does not contain the correct type(s).\n")
                                return None
                        else:
                            logging.error("Block votes are not in the correct format.\n")
                            return None
                    block.votes = deserialized_votes
                    block.parent_epoch = parent_epoch
                else:
                    logging.error("Block attributes do not contain the correct type(s).\n")
                    return None
            return block
        logging.error("Block attributes do not contain the correct type(s).\n")
        return None


    def __str__(self) -> str:
        """
        Represent Block in a string.

        Returns:
            str: string representation of Block
        """
        return f"({self.epoch}, {self.transactions}, {self.parent_hash})"