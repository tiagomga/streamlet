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
            0: Block(None, 0, None, None)
        }


    def add_block(self, epoch, block):
        """
        Add block to the blockchain.

        Args:
            epoch (int): block's epoch
            block (Block): block to be added to the blockchain
        """
        self.chain[epoch] = block


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


    def generate_alternate_chains(self, fork_location, epochs):
        """
        Generate chains for the corresponding forks (fork_location).

        Args:
            fork_location (tuple): tuple with the hash of the block where the fork
            was created with the corresponding number of forks
            epochs (int): epoch number
        """
        # Store epochs of blocks that were already included in a chain
        iterated_epochs = []

        # Store lists of alternate chains in chains variable
        chains = []
        fork, fork_count = fork_location

        for i in range(fork_count):
            alternate_chain = []
            for epoch in epochs:
                block = self.chain[epoch]

                # Ignore blocks that were already included in other alternate chain
                if epoch in iterated_epochs:
                    continue

                # Add first block to the chain and ensure only one fork child is added
                elif len(alternate_chain) == 0 and block.get_parent_hash() == fork:
                    alternate_chain.append(block)
                    iterated_epochs.append(epoch)

                # Add child block of the last block added to the alternate chain
                elif len(alternate_chain) > 0 and block.get_parent_hash() == alternate_chain[-1].get_hash():
                    alternate_chain.append(block)
                    iterated_epochs.append(epoch)
                else:
                    continue
            chains.append(alternate_chain)