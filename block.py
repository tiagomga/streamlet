class Block:
    """
    Class that represents a block containing:
    - Hash of the (block) parent hash
    - Set of transactions
    - Block length
    """

    length = 0

    def __init__(self):
        self.parent_hash = ""
        self.transactions = []
        self.length = Block.length + 1

    def get_length(self):
        return self.length
    
    def get_parent_hash(self):
        return self.parent_hash
    
    def is_parent(self, block):
        # Replace hash() with proper function
        self_hash = hash(self)
        if block.parent_hash == self_hash:
            return True
        return False