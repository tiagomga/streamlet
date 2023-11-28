import random
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
        self.epoch = 1
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
        self.notarize()
        self.epoch += 1


    def propose(self):
        """
        Propose a new block to the blockchain.
        """
        # requests = get_requests()
        latest_notarized_block = self.blockchain.get_longest_notarized_block()
        proposed_block = Block(
            self.server_id,
            self.epoch,
            [f"request {self.epoch}"],
            latest_notarized_block.get_hash(),
            latest_notarized_block.get_epoch()
        )
        proposed_block.sign(self.private_key)
        self.blockchain.add_block(proposed_block)
        propose_message = Message(MessageType.PROPOSE, proposed_block, self.server_id).to_bytes()
        self.communication.send(propose_message)


    def vote(self):
        """
        Vote for the proposed block.
        """
        leader_id = self.get_epoch_leader()
        proposer_id, proposed_block = self.communication.get_proposed_block()
        if proposer_id != leader_id:
            raise Exception
        leader_public_key = self.servers_public_key[leader_id]
        longest_notarized_block = self.blockchain.get_longest_notarized_block()
        valid_block = proposed_block.check_validity(leader_public_key, self.epoch, longest_notarized_block)
        if not valid_block:
            raise Exception
        self.blockchain.add_block(proposed_block)
        _vote = proposed_block.create_vote(self.private_key)
        vote_message = Message(MessageType.VOTE, _vote, self.server_id).to_bytes()
        self.communication.send(vote_message)


    def notarize(self):
        pass


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