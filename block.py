import rsa
import pickle

class Block:
    """
    Class that represents a block containing:
    - Hash of the (block) parent hash
    - Set of transactions
    - Epoch number
    """

    def __init__(self, proposer_id, epoch, transactions, parent_hash):
        """
        Constructor.

        Args:
            proposer_id (int): id of the proposer
            epoch (int): block's epoch
            transactions (list): clients' transactions
            parent_hash (str): hash of the last notarized block
        """
        self.proposer_id = proposer_id
        self.epoch = epoch
        self.transactions = transactions
        self.hash = None
        self.parent_hash = parent_hash
        self.signature = None


    def get_proposer_id(self):
        """
        Get block proposer's ID.

        Returns:
            int: ID of the proposer
        """
        return self.proposer_id


    def get_hash(self):
        return self.hash


    def get_parent_hash(self):
        """
        Get block's parent hash.

        Returns:
            str: parent hash
        """
        return self.parent_hash


    def is_parent(self, block):
        """
        Check if this block is parent of the other block.

        Args:
            block (Block): other block to be compared to

        Returns:
            bool: True, if and only if this block is parent of the other block, else return False
        """
        # Replace hash() with proper function
        self_hash = hash(self)
        if block.parent_hash == self_hash:
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
        # Replace hash() with proper function
        block_hash = hash(block)
        if self.parent_hash == block_hash:
            return True
        return False


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


    def check_signature(self, public_key):
        """
        Check block's signature validity.

        Args:
            public_key (PublicKey): server's public key

        Returns:
            bool: True, if and only if block's signature is valid, else return False
        """
        block_bytes = self.to_bytes()
        try:
            hash_algorithm = rsa.verify(block_bytes, self.signature, public_key)
            if hash_algorithm == 'SHA-256':
                return True
        except rsa.VerificationError:
            return False


    def to_bytes(self):
        """
        Convert Block to bytes.

        Returns:
            bytes: bytes from Block object
        """
        data = (self.parent_hash, self.epoch, self.transactions)
        return pickle.dumps(data)