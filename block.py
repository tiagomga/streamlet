import os
import rsa
import pickle
import json
from hashlib import sha256
from blockstatus import BlockStatus

class Block:
    """
    Class that represents a block containing:
    - Hash of the (block) parent hash
    - Set of transactions
    - Epoch number
    """

    def __init__(self, epoch, transactions, parent_hash, parent_epoch=None):
        """
        Constructor.

        Args:
            epoch (int): block's epoch
            transactions (list): clients' transactions
            parent_hash (str): hash of the last notarized block
        """
        self.epoch = epoch
        self.transactions = transactions
        self.hash = None
        self.parent_hash = parent_hash
        self.parent_epoch = parent_epoch
        self.signature = None
        self.votes = []
        self.status = BlockStatus.PROPOSED


    def get_epoch(self):
        """
        Get block's epoch.

        Returns:
            int: epoch of the block
        """
        return self.epoch


    def get_hash(self):
        """
        Get block's hash.

        Returns:
            str: hash
        """
        return self.hash


    def get_parent_hash(self):
        """
        Get block's parent hash.

        Returns:
            str: parent hash
        """
        return self.parent_hash


    def get_status(self):
        """
        Get block's status.

        Returns:
            BlockStatus: block's status
        """
        return self.status


    def get_parent_epoch(self):
        """
        Get parent block's epoch.

        Returns:
            int: epoch of parent block
        """
        return self.parent_epoch


    def get_votes(self):
        return self.votes


    def get_signature(self):
        return self.signature


    def set_signature(self, signature):
        self.signature = signature


    def set_parent_epoch(self, parent_epoch):
        """
        Set parent block's epoch.

        Args:
            parent_epoch (int): epoch of parent block
        """
        self.parent_epoch = parent_epoch


    def is_parent(self, block):
        """
        Check if this block is parent of the other block.

        Args:
            block (Block): other block to be compared to

        Returns:
            bool: True, if and only if this block is parent of the other block, else return False
        """
        if block.parent_hash == self.hash:
            return True
        return False


    def is_child(self, block):
        """
        Check if this block is child of the other block.

        Args:
            block (Block): other block to be compared to

        Returns:
            bool: True, if and only if this block is child of the other block, else return False
        """
        if self.parent_hash == block.hash:
            return True
        return False


    def calculate_hash(self):
        """
        Calculate block's hash.
        """
        block_bytes = self.to_bytes()
        self.hash = sha256(block_bytes).hexdigest()


    def check_validity(self, public_key, epoch, longest_notarized_block):
        """
        Check block's validity by checking its signature, epoch and if it
        extends from the longest notarized chain.

        Args:
            public_key (PublicKey): server's public key
            epoch (int): epoch number
            longest_notarized_block (Block): latest block from the longest
            notarized chain

        Returns:
            bool: True, if and only if the block meets all conditions, else return False
        """
        # Check block's signature
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
    

    def sign(self, private_key):
        """
        Sign block's data - used by epoch's leader.

        Args:
            private_key (PrivateKey): server's private key
        """
        block_bytes = self.to_bytes()
        signature = rsa.sign(block_bytes, private_key, 'SHA-256')
        self.signature = signature


    def create_vote(self, private_key):
        block_bytes = self.to_bytes()
        signature = rsa.sign(block_bytes, private_key, 'SHA-256')
        block = Block(
            self.epoch,
            None,
            self.parent_hash,
        )
        block.signature = signature
        return block


    def check_signature(self, public_key, content=None):
        """
        Check block's signature validity.

        Args:
            public_key (PublicKey): server's public key

        Returns:
            bool: True, if and only if block's signature is valid, else return False
        """
        if content == None:
            content = self.to_bytes()
        try:
            hash_algorithm = rsa.verify(content, self.signature, public_key)
            if hash_algorithm == 'SHA-256':
                return True
        except rsa.VerificationError:
            return False


    def add_vote(self, vote):
        """
        Add vote to the block.

        Args:
            vote (tuple): tuple with ID of the voter and empty Block with signature
        """
        self.votes.append(vote)


    def notarize(self):
        """
        Change status to notarized.
        """
        self.status = BlockStatus.NOTARIZED


    def finalize(self):
        """
        Change status to finalized.
        """
        self.status = BlockStatus.FINALIZED


    def write(self, filename=f"blockchain/blockchain_{os.getpid()}"):
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


    def to_bytes(self, include_signature=False):
        """
        Convert Block to bytes.

        Args:
            include_signature (bool): if set to True, block's signature
            is included

        Returns:
            bytes: bytes from Block object
        """
        if include_signature:
            data = (self.parent_hash, self.epoch, self.transactions, self.signature)
        else:
            data = (self.parent_hash, self.epoch, self.transactions)
        return pickle.dumps(data)


    @staticmethod
    def from_bytes(bytes):
        """
        Convert bytes to Block.

        Args:
            bytes (bytes): Block in serialized form

        Returns:
            Block: Block object from bytes
        """
        data = pickle.loads(bytes)
        block = Block(data[1], data[2], data[0])
        block.signature = data[3]
        return block


    def __str__(self):
        """
        Represent Block in a string.

        Returns:
            str: string representation of Block
        """
        return f"({self.epoch}, {self.transactions}, {self.parent_hash})"