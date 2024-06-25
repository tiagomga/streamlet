import random
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
        self.freshest_notarized_chain = []
        random.seed(0)


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


    def update_freshest_notarized_chain(self):
        notarized_chains = self.get_notarized_chains()
        if len(notarized_chains) == 1:
            self.freshest_notarized_chain = notarized_chains[0]
        else:
            notarized_chains_length = [len(chain) for chain in notarized_chains]
            longest_chain_length = max(notarized_chains_length)
            if notarized_chains_length.count(longest_chain_length) == 1:
                longest_chain_index = notarized_chains_length.index(longest_chain_length)
                self.freshest_notarized_chain = notarized_chains[longest_chain_index]
            else:
                notarized_chains = list(filter(lambda x: len(x) == longest_chain_length, notarized_chains))
                freshest_chain = notarized_chains[0]
                freshest_block_epoch = freshest_chain[0].get_epoch()
                for chain in notarized_chains:
                    block_epoch = chain[0].get_epoch()
                    if block_epoch > freshest_block_epoch:
                        freshest_chain = chain
                        freshest_block_epoch = block_epoch
                self.freshest_notarized_chain = freshest_chain


    def get_notarized_chains(self):
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
                block = self.chain[latest_epoch]
                if block.get_status() == BlockStatus.NOTARIZED and latest_epoch not in iterated_epochs:
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
                    parent_block = self.chain[parent_epoch]
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


    def get_freshest_notarized_block(self):
        """
        Get latest block from blockchain's longest notarized chain.

        Returns:
            Block: latest notarized block
        """
        self.update_freshest_notarized_chain()
        return self.freshest_notarized_chain[0]


    def finalize(self):
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