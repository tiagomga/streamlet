from block import Block
from message import Message
from messagetype import MessageType
    
class Streamlet:
    """
    Streamlet protocol.
    """

    def __init__(self, server_id, num_replicas=4):
        """
        Constructor.
        """
        self.server_id = server_id
        self.epoch = 0
        self.num_replicas = num_replicas


    def start_new_epoch(self, block):
        epoch_leader = self.get_epoch_leader()
        if epoch_leader == self.server_id:
            self.propose()
        else:
            self.vote(block)
        self.epoch += 1


    def propose(self):
        requests = get_requests()
        latest_notarized_block = Blockchain.get_latest_notarized_block()
        proposed_block = Block(self.server_id, self.epoch, requests, latest_notarized_block.get_hash())
        proposed_block.sign()
        propose_message = Message(MessageType.PROPOSE, proposed_block, self.server_id)
        self.communication.send(propose_message)


    def vote(self, block):
        leader_id = self.get_epoch_leader()
        proposed_block = get_proposed_block()
        if proposed_block.get_proposer_id() != leader_id:
            raise Exception
        leader_public_key = get_public_key(leader_id)
        longest_notarized_block = Blockchain.get_longest_notarized_block()
        valid_block = proposed_block.check_validity(leader_public_key, self.epoch, longest_notarized_block.get_parent_hash())
        if not valid_block:
            raise Exception
        proposed_block.sign()
        vote_message = Message(MessageType.VOTE, proposed_block, self.server_id)
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
        return self.epoch % self.num_replicas