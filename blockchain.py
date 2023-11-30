from blockstatus import BlockStatus
from block import Block

class Blockchain:
    """
    Class that contains the blockchain structure and its operations.
    """

    def __init__(self):
        """
        Constructor.
        """
        self.chain = {
            0: Block(None, 0, None, None, None)
        }


    def add_block(self, block):
        """
        Add block to the blockchain.

        Args:
            epoch (int): block's epoch
            block (Block): block to be added to the blockchain
        """
        block.calculate_hash()
        self.chain[block.get_epoch()] = block


    def get_block(self, epoch):
        """
        Get epoch's block from blockchain.

        Args:
            epoch (int): epoch's number

        Returns:
            Block: blockchain block
        """
        return self.chain[epoch]


    def get_longest_notarized_block(self):
        """
        Get latest block from blockchain's longest notarized chain.

        Returns:
            Block: latest notarized block
        """
        epochs = list(self.chain.keys())
        epochs.sort()
        i = len(epochs) - 1
        notarized_chain = []
        while i >= 0:
            epoch = epochs[i]
            block = self.chain[epoch]
            if block.get_status() == BlockStatus.NOTARIZED:
                parent_epoch = block.get_parent_epoch()
                parent_block = self.chain[parent_epoch]
                if block.get_parent_hash() == parent_block.get_hash():
                    notarized_chain.append(self.chain[epoch])
            i -= 1
        
        # Return genesis block, when no block is notarized
        if len(self.chain) <= 2 and len(notarized_chain) == 0:
            return self.chain[0]
        
        return notarized_chain[0]


    def find_fork(self):
        """
        Find forks in the blockchain.

        Returns:
            (str, int): tuple with the hash of the block where the fork
            was created with the corresponding number of forks
        """
        # Count parent hashes in the blockchain (find parent hash "collision")
        hash_count = {}
        for block in self.chain.values():
            if block.status != BlockStatus.NOTARIZED:
                continue
            parent_hash = block.get_parent_hash()
            if parent_hash in hash_count:
                hash_count[parent_hash] += 1
            else:
                hash_count[parent_hash] = 1
        
        # If there are parent hashes that have a count higher than 1,
        # there is at least one fork
        fork_location = []
        for hash in hash_count.keys():
            if hash_count[hash] > 1:
                fork_location.append((hash, hash_count[hash]))
        
        return fork_location


    def __str__(self):
        """
        Represent Blockchain in a string.

        Returns:
            str: string representation of Blockchain
        """
        string = ""
        for key, value in self.chain.items():
            string += f"{key} : {value} || "
        return string