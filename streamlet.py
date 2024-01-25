import random
import time
import logging
from multiprocessing import Value
from block import Block
from message import Message
from messagetype import MessageType
from blockchain import Blockchain

class Streamlet:
    """
    Streamlet protocol.
    """

    def __init__(self, server_id, communication, private_key, servers_public_key, f=1):
        """
        Constructor.
        """
        self.server_id = server_id
        self.communication = communication
        self.private_key = private_key
        self.servers_public_key = servers_public_key
        self.epoch = Value("i", 0)
        self.f = f
        self.num_replicas = 3*f + 1
        self.blockchain = Blockchain()
        self.random_object = random.Random()
        self.random_object.seed(0)


    def start_new_epoch(self):
        """
        Start a new epoch.
        """
        start_time = time.time()
        self.epoch.value += 1
        epoch_leader = self.get_epoch_leader()
        if epoch_leader == self.server_id:
            self.propose()
        else:
            self.vote(epoch_leader, start_time)
        self.notarize(start_time)
        self.finalize()


    def propose(self):
        """
        Propose a new block to the blockchain.
        """
        # Get clients' requests
        # requests = get_requests()

        # Get latest block from the longest notarized chain
        latest_notarized_block = self.blockchain.get_longest_notarized_block()

        # Create block proposal
        proposed_block = Block(
            self.epoch.value,
            [f"request {self.epoch.value}"],
            latest_notarized_block.get_hash(),
            latest_notarized_block.get_epoch()
        )

        # Sign the block
        proposed_block.sign(self.private_key)

        # Add block to server's blockchain
        self.blockchain.add_block(proposed_block)

        # Send block proposal to every server participating in the protocol
        propose_message = Message(
            MessageType.PROPOSE,
            proposed_block.to_bytes(include_signature=True),
            self.server_id
        ).to_bytes()
        self.communication.send(propose_message)


    def vote(self, leader_id, start_time):
        """
        Vote for the proposed block.
        """
        # Get proposed block for the current epoch
        proposer_id, proposed_block = self.get_message(start_time)

        # Check if the proposer's ID matches with the leader's ID
        if proposer_id != leader_id:
            raise Exception
        
        # Get leader's public key
        leader_public_key = self.servers_public_key[leader_id]

        # Get latest block from the longest notarized chain
        longest_notarized_block = self.blockchain.get_longest_notarized_block()

        # Check if the proposed block is valid
        valid_block = proposed_block.check_validity(leader_public_key, self.epoch.value, longest_notarized_block)
        if not valid_block:
            raise Exception
        
        # Create vote for the proposed block using server's private key
        _vote = proposed_block.create_vote(self.private_key)
        proposed_block.add_vote((self.server_id, _vote))

        # Add proposed block to server's blockchain
        proposed_block.set_parent_epoch(longest_notarized_block.get_epoch())
        self.blockchain.add_block(proposed_block)

        # Send vote to every server participating in the protocol
        vote_message = Message(
            MessageType.VOTE,
            _vote.to_bytes(include_signature=True),
            self.server_id
        ).to_bytes()
        self.communication.send(vote_message)


    def notarize(self, start_time):
        """
        Notarize block after getting 2f + 1 votes.
        """
        # Get proposed block for the current epoch from server's blockchain
        proposed_block = self.blockchain.get_block(self.epoch.value)
        proposed_block_bytes = proposed_block.to_bytes()

        # For every vote, check its signature validity
        # If it is valid, add vote to the proposed block
        num_votes = 0
        for i in range(2):
            sender, vote = self.get_message(start_time)
            public_key = self.servers_public_key[sender]
            valid_vote = vote.check_signature(public_key, content=proposed_block_bytes)
            if valid_vote:
                num_votes += 1
                proposed_block.add_vote((sender, vote))
        
        # Check if there are sufficient valid votes; then, notarize the proposed block
        if num_votes == 2*self.f:
            proposed_block.notarize()


    def finalize(self):
        """
        Finalize the notarized chain up to the second of the three blocks,
        after observing three adjacent blocks with consecutive epochs.
        """
        if self.epoch.value > 2:
            finalized_blocks = self.blockchain.finalize()
            # Execute clients' transactions
            # if finalized_blocks:
            #     execute_transactions(finalized_blocks)


    def get_epoch_leader(self):
        """
        Get leader's id of the current epoch.

        Returns:
            int: leader's id
        """
        return self.random_object.randrange(0, self.num_replicas)


    def start(self):
        """
        Start Streamlet.
        """
        self.blockchain.add_genesis_block()
        while True:
            try:
                start_time = time.time()
                self.start_new_epoch()
                end_time = time.time()
                epoch_duration = end_time - start_time
                logging.info(f"Blockchain - {self.blockchain}\n\n")
                if epoch_duration < 5:
                    time.sleep(5 - epoch_duration)
            except TimeoutError:
                pass


    def get_message(self, start_time):
        while True:
            remaining_time = 5 - (time.time() - start_time)
            message = self.communication.get_message(remaining_time)
            sender = message.get_sender()
            block = Block.from_bytes(message.get_content())
            block_epoch = block.get_epoch()
            logging.debug(f"Message type - {message.get_type()}\n\n")

            # Return propose message if proposed block is new to the blockchain
            if message.get_type() == MessageType.PROPOSE:
                if block_epoch == self.epoch.value:
                    try:
                        self.blockchain.get_block(block_epoch)
                    except KeyError:
                        logging.debug(f"New proposal (epoch: {self.epoch.value} | proposer: {sender})\n\n")
                        return (sender, block)
            
            # Return vote message if vote is new to the proposed block
            elif message.get_type() == MessageType.VOTE:
                blockchain_block = self.blockchain.get_block(block_epoch)
                blockchain_block_votes = blockchain_block.get_votes()
                repeated_vote = False
                for vote in blockchain_block_votes:
                    if sender == vote[0]:
                        repeated_vote = True
                        break
                if not repeated_vote:
                    if block_epoch == self.epoch.value:
                        logging.debug(f"New vote for current epoch (epoch: {self.epoch.value} | voter: {sender})\n\n")
                        return (sender, block)
                    else:
                        public_key = self.servers_public_key[sender]
                        valid_block = block.check_signature(public_key, content=blockchain_block.to_bytes())
                        if valid_block:
                            blockchain_block.add_vote((sender, block))
                            logging.debug(f"New vote for past epoch (epoch: {blockchain_block.get_epoch()} | voter: {sender})\n\n")