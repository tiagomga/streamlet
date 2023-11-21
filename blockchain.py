from blockstatus import BlockStatus

class Blockchain:
    """
    Class that contains the blockchain structure and its operations.
    """

    def __init__(self):
        """
        Constructor.
        """
        self.chain = {}


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
        epochs = list(self.chain.keys()).sort()
        forks = self.find_fork()
        if len(forks) == 1:
            alternate_chains = self.generate_alternate_chains(forks[0], epochs)
        elif len(forks) > 1:
            alternate_chains = []
            for fork in forks:
                alternate_chains.extend(self.generate_alternate_chains(fork, epochs))
                # Handle forks within forks
        else:
            i = len(epochs) - 1
            while i >= 0:
                pos = epochs[i]
                if self.chain[pos].status == BlockStatus.NOTARIZED:
                    return self.chain[pos]
                i -= 1