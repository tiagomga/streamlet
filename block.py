class Block:
    """
    Class that represents a block containing:
    - Hash of the (block) parent hash
    - Set of transactions
    - Block length
    """

    def __init__(self):
        self.parent_hash = ""
        self.transactions = []


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


    def is_child(self, block):
        # Replace hash() with proper function
        block_hash = hash(block)
        if self.parent_hash == block_hash:
            return True
        return False