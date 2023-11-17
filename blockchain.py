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


    def get_latest_notarized_block(self):
        """
        Get latest notarized block from the blockchain.

        Returns:
            Block: latest notarized block
        """
        epochs = list(self.chain.keys()).sort()
        i = len(epochs) - 1
        while i >= 0:
            if self.chain[i].status == BlockStatus.NOTARIZED:
                return self.chain[i]
            i -= 1