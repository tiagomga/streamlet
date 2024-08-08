import random
from blockstatus import BlockStatus
from block import Block

class Blockchain:
    """
    Class that contains the blockchain structure and its operations.
    """

    def __init__(self) -> None:
        """
        Constructor.
        """
        self.chain = {}
        self.freshest_notarized_chain = []
        random.seed(0)


    def add_block(self, block: Block) -> None:
        """
        Add block to the blockchain.

        Args:
            block (Block): block to be added to the blockchain
        """
        self.chain[block.get_epoch()] = block


    def add_genesis_block(self) -> None:
        """
        Add genesis block to the blockchain.
        """
        genesis_block = Block(0, None, None)
        genesis_block.notarize()
        genesis_block.calculate_hash()
        self.add_block(genesis_block)


    def get_block(self, epoch: int) -> Block:
        """
        Get epoch's block from blockchain.

        Args:
            epoch (int): epoch's number

        Returns:
            Block: blockchain block
        """
        return self.chain[epoch]


    def update_freshest_notarized_chain(self) -> None:
        """
        Update `self.freshest_notarized_chain` with the freshest notarized chain.
        """
        latest_epoch = max(self.chain)
        self.freshest_notarized_chain = []

        # Find notarized block with highest epoch number
        while latest_epoch >= 0:
            try:
                block = self.chain[latest_epoch]
            except KeyError:
                latest_epoch -= 1
                continue
            if block.get_status() == BlockStatus.NOTARIZED:
                break
            latest_epoch -= 1
        
        # Build chain (from the end) starting with the notarized block with highest epoch number
        build_chain = True
        while build_chain:
            parent_epoch = block.get_parent_epoch()
            if parent_epoch is not None:
                parent_block = self.chain[parent_epoch]
                if block.get_status() == BlockStatus.NOTARIZED:
                    self.freshest_notarized_chain.append(block)
                    block = parent_block
                else:
                    build_chain = False
            else:
                self.freshest_notarized_chain.append(block)
                build_chain = False


    def get_freshest_notarized_block(self) -> Block:
        """
        Get latest block from blockchain's longest notarized chain.

        Returns:
            Block: latest notarized block
        """
        self.update_freshest_notarized_chain()
        return self.freshest_notarized_chain[0]


    def finalize(self) -> list:
        """
        Finalize the notarized chain up to the second of the three blocks,
        after observing three adjacent blocks with consecutive epochs.
        """
        self.update_freshest_notarized_chain()
        finalized_blocks = []
        consecutive_epochs = 1
        
        # Skip if notarized chain is too short for finalization
        if len(self.freshest_notarized_chain) <= 1:
            return finalized_blocks
        
        # When blocks with consecutive epochs are all notarized
        else:
            block = self.freshest_notarized_chain[0]
            parent_block = self.freshest_notarized_chain[1]
            if block.get_epoch() == parent_block.get_epoch() + 1:
                consecutive_epochs += 1

        # If there are 2 blocks with consecutive epochs,
        # finalize prefix chain up to the 1st of the 2 blocks
        if consecutive_epochs == 2:
            for block in self.freshest_notarized_chain[1:]:
                block.finalize()
                finalized_blocks.append(block)
            finalized_blocks.reverse()

            # Write finalized blocks to file
            for block in finalized_blocks:
                block.write()

        return finalized_blocks


    def __str__(self) -> str:
        """
        Represent Blockchain in a string.

        Returns:
            str: string representation of Blockchain
        """
        string = ""
        for key, value in self.chain.items():
            string += f"{key} : {value} || "
        return string