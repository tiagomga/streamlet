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
        return self.proposer_id


    def get_parent_hash(self):
        return self.parent_hash


    def is_parent(self, block):
        # Replace hash() with proper function
        self_hash = hash(self)
        if block.parent_hash == self_hash:
            return True
        return False


    def is_child(self, block):
        # Replace hash() with proper function
        block_hash = hash(block)
        if self.parent_hash == block_hash:
            return True
        return False


    def check_validity(self, public_key, epoch, longest_notarized_block):
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