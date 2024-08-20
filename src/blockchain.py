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
        self.longest_notarized_chains = []
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


    def get_block(self, epoch: int) -> Block | None:
        """
        Get epoch's block from blockchain.

        Args:
            epoch (int): epoch's number

        Returns:
            (Block | None): blockchain block
        """
        if epoch in self.chain:
            return self.chain[epoch]


    def update_longest_notarized_chains(self) -> None:
        """
        Update `self.longest_notarized_chains` to contain a list of the 
        longest notarized chain(s).
        """
        notarized_chains = self.get_notarized_chains()
        if len(notarized_chains) == 1:
            self.longest_notarized_chains = notarized_chains
        else:
            notarized_chains_length = [len(chain) for chain in notarized_chains]
            longest_chain_length = max(notarized_chains_length)
            if notarized_chains_length.count(longest_chain_length) == 1:
                longest_chain_index = notarized_chains_length.index(longest_chain_length)
                self.longest_notarized_chains = [notarized_chains[longest_chain_index]]
            else:
                self.longest_notarized_chains = list(filter(lambda x: len(x) == longest_chain_length, notarized_chains))


    def get_notarized_chains(self) -> list:
        """
        Get every notarized chain.

        Returns:
            list: list of notarized chains
        """
        latest_epoch = max(self.chain)
        notarized_chains = []
        iterated_epochs = []

        # First iteration: start chain (from the end) with notarized block
        # with highest epoch number
        # -------------------------------------------------------------------
        # Further iterations: start chain (from the end) with notarized block
        # that was not present in other notarized chains (fork chain)
        while True:
            while latest_epoch >= 0:
                block = self.get_block(latest_epoch)
                if (block and block.get_status() == BlockStatus.NOTARIZED
                        and latest_epoch not in iterated_epochs):
                    break
                latest_epoch -= 1
            
            # Exit loop after iterating through every epoch number
            if latest_epoch < 0:
                break
            
            chain = []
            end_chain = False
            while not end_chain:
                parent_epoch = block.get_parent_epoch()
                if parent_epoch != None:
                    parent_block = self.get_block(parent_epoch)
                    if block.is_child(parent_block) and block.get_status() == BlockStatus.NOTARIZED:
                        chain.append(block)
                        iterated_epochs.append(block.get_epoch())
                        block = parent_block
                    else:
                        end_chain = True
                else:
                    chain.append(block)
                    iterated_epochs.append(block.get_epoch())
                    end_chain = True
            notarized_chains.append(chain)

        return notarized_chains


    def get_longest_notarized_blocks(self) -> list:
        """
        Get latest block(s) from blockchain's longest notarized chain(s).

        Returns:
            list: list of the latest notarized block(s)
        """
        self.update_longest_notarized_chains()
        longest_notarized_blocks = []
        for chain in self.longest_notarized_chains:
            longest_notarized_blocks.append(chain[0])
        return longest_notarized_blocks


    def finalize(self) -> list:
        """
        Finalize the notarized chain up to the second of the three blocks,
        after observing three adjacent blocks with consecutive epochs.
        """
        self.update_longest_notarized_chains()
        finalized_blocks = []
        consecutive_epochs = 1
        
        # Skip if the only notarized chain is too short for finalization
        longest_notarized_chain = self.longest_notarized_chains[0]
        if len(self.longest_notarized_chains) != 1 or len(longest_notarized_chain) <= 2:
            return finalized_blocks
        
        # When blocks with consecutive epochs are all notarized
        else:
            for i in range(2):
                block = longest_notarized_chain[i]
                child_block = longest_notarized_chain[i+1]
                if block.get_epoch() == child_block.get_epoch() + 1:
                    consecutive_epochs += 1

        # If there are 3 blocks with consecutive epochs,
        # finalize prefix chain up to the 2nd of the 3 blocks
        if consecutive_epochs == 3:
            for block in longest_notarized_chain[1:]:
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