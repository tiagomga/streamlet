import random
from block import Block
from message import Message
from messagetype import MessageType
from blockchain import Blockchain
    
class Streamlet:
    """
    Streamlet protocol.
    """

    def __init__(self, server_id, communication, f=1):
        """
        Constructor.
        """
        self.server_id = server_id
        self.communication = communication
        self.epoch = 0
        self.f = f
        self.num_replicas = 3*f + 1
        self.blockchain = Blockchain()
        random.seed(0)


    def start_new_epoch(self):
        """
        Start a new epoch.
        """
        epoch_leader = self.get_epoch_leader()
        if epoch_leader == self.server_id:
            self.propose()
        else:
            self.vote()
        self.epoch += 1


    def propose(self):
        """
        Propose a new block to the blockchain.
        """
        requests = get_requests()
        latest_notarized_block = self.blockchain.get_longest_notarized_block()
        proposed_block = Block(self.server_id, self.epoch, requests, latest_notarized_block.get_hash())
        proposed_block.sign()
        propose_message = Message(MessageType.PROPOSE, proposed_block, self.server_id)
        self.communication.send(propose_message)


    def vote(self):
        """
        Vote for the proposed block.
        """
        leader_id = self.get_epoch_leader()
        proposed_block = self.communication.get_proposed_block()
        if proposed_block.get_proposer_id() != leader_id:
            raise Exception
        leader_public_key = get_public_key(leader_id)
        longest_notarized_block = self.blockchain.get_longest_notarized_block()
        valid_block = proposed_block.check_validity(leader_public_key, self.epoch, longest_notarized_block)
        if not valid_block:
            raise Exception
        _vote = proposed_block.create_vote()
        vote_message = Message(MessageType.VOTE, _vote, self.server_id)
        self.communication.send(vote_message)
    

    def finalize(self, block):
        #TODO
        pass


    def get_epoch_leader(self):
        """
        Get leader's id of the current epoch.

        Returns:
            int: leader's id
        """
        return random.randrange(0, self.num_replicas)