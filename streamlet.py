import random
import time
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
        proposer_id, proposed_block = self.communication.get_proposed_block(self.epoch.value, start_time)

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
        
        # Add proposed block to server's blockchain
        self.blockchain.add_block(proposed_block)

        # Create vote for the proposed block using server's private key
        _vote = proposed_block.create_vote(self.private_key)

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

        # Get votes from other servers
        votes = self.communication.get_votes(self.epoch.value, self.f, start_time)

        # For every vote, check its signature validity
        # If it is valid, add vote to the proposed block
        num_votes = 0
        for sender, vote in votes:
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
        #TODO
        pass


    def get_epoch_leader(self):
        """
        Get leader's id of the current epoch.

        Returns:
            int: leader's id
        """
        return self.random_object.randrange(0, self.num_replicas)