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
        self.chain = {}
        self.longest_notarized_chain = []
        self.finalized_chain = []


    def add_block(self, block):
        """
        Add block to the blockchain.

        Args:
            epoch (int): block's epoch
            block (Block): block to be added to the blockchain
        """
        block.calculate_hash()
        self.chain[block.get_epoch()] = block


    def add_genesis_block(self):
        """
        Add genesis block to the blockchain.
        """
        genesis_block = Block(0, None, None)
        genesis_block.notarize()
        self.add_block(genesis_block)


    def get_block(self, epoch):
        """
        Get epoch's block from blockchain.

        Args:
            epoch (int): epoch's number

        Returns:
            Block: blockchain block
        """
        return self.chain[epoch]


    def update_longest_notarized_chain(self):
        self.longest_notarized_chain = []
        latest_epoch = max(self.chain)

        while latest_epoch >= 0:
            block = self.chain[latest_epoch]
            if block.get_status() == BlockStatus.NOTARIZED:
                break
            latest_epoch -= 1

        while True:
            parent_epoch = block.get_parent_epoch()
            if parent_epoch != None:
                parent_block = self.chain[parent_epoch]
                if block.is_child(parent_block) and block.get_status() == BlockStatus.NOTARIZED:
                    self.longest_notarized_chain.append(block)
                    block = parent_block
                else:
                    break
            else:
                self.longest_notarized_chain.append(block)
                break


    def get_longest_notarized_block(self):
        """
        Get latest block from blockchain's longest notarized chain.

        Returns:
            Block: latest notarized block
        """
        self.update_longest_notarized_chain()
        return self.longest_notarized_chain[0]


    def finalize(self):
        """
        Finalize the notarized chain up to the second of the three blocks,
        after observing three adjacent blocks with consecutive epochs.
        """
        self.update_longest_notarized_chain()
        finalized_blocks = []
        consecutive_epochs = 1
        
        # Skip if notarized chain is too short for finalization
        if len(self.longest_notarized_chain) <= 1:
            return finalized_blocks
        
        # When blocks with consecutive epochs include a finalized block
        elif len(self.longest_notarized_chain) == 2 and self.finalized_chain:
            block = self.longest_notarized_chain[0]
            child_block = self.longest_notarized_chain[1]
            grandchild_block = self.finalized_chain[-1]
            if block.get_epoch() == child_block.get_epoch() + 1:
                consecutive_epochs += 1
                if child_block.get_epoch() == grandchild_block.get_epoch() + 1:
                    consecutive_epochs += 1
        
        # When blocks with consecutive epochs are all notarized
        elif len(self.longest_notarized_chain) > 2:
            for i in range(2):
                block = self.longest_notarized_chain[i]
                child_block = self.longest_notarized_chain[i+1]
                if block.get_epoch() == child_block.get_epoch() + 1:
                    consecutive_epochs += 1

        # If there are 3 blocks with consecutive epochs,
        # finalize prefix chain up to the 2nd of the 3 blocks
        if consecutive_epochs == 3:
            for block in self.longest_notarized_chain[1:]:
                block.finalize()
                finalized_blocks.append(block)
        
        finalized_blocks.reverse()
        self.finalized_chain.extend(finalized_blocks)
        return finalized_blocks


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