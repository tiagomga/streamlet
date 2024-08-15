import random
import time
import logging
from multiprocessing import Value
from typing import NoReturn
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from block import Block
from blockstatus import BlockStatus
from message import Message
from messagetype import MessageType
from blockchain import Blockchain
from communicationsystem import CommunicationSystem

class Streamlet:
    """
    Streamlet protocol.
    """

    def __init__(self, server_id: int, communication: CommunicationSystem, private_key: RSAPrivateKey, servers_public_key: dict, f: int = 1) -> None:
        """
        Constructor.
        """
        self.server_id = server_id
        self.communication = communication
        self.private_key = private_key
        self.servers_public_key = servers_public_key
        self.epoch = Value("i", 0)
        self.epoch_duration = 5
        self.epoch_leaders = [None]
        self.f = f
        self.num_replicas = 3*f + 1
        self.blockchain = Blockchain()
        self.random_object = random.Random()
        self.random_object.seed(0)
        self.early_messages = []


    def start_new_epoch(self) -> None:
        """
        Start a new epoch.
        """
        start_time = time.time()
        self.epoch.value += 1
        epoch_leader = self.get_epoch_leader()
        if epoch_leader == self.server_id:
            self.propose()
        self.process_messages(start_time)


    def propose(self) -> None:
        """
        Propose a new block to the blockchain.
        """
        # Get clients' requests
        # requests = get_requests()

        # Get latest block(s) from the longest notarized chain(s)
        longest_notarized_blocks = self.blockchain.get_longest_notarized_blocks()

        # Choose one of the longest chains to extend from (if there are more than 1)
        longest_notarized_block = random.choice(longest_notarized_blocks)

        # Create block proposal
        proposed_block = Block(
            self.epoch.value,
            [f"request {self.epoch.value}"],
            longest_notarized_block.get_hash(),
            longest_notarized_block.get_epoch()
        )

        # Sign the block
        proposed_block.sign(self.private_key)

        # Add leader's vote to the proposed block
        proposed_block.add_leader_vote(self.server_id)

        # Add block to server's blockchain
        self.blockchain.add_block(proposed_block)

        # Send block proposal to every server participating in the protocol
        self.send_message(MessageType.PROPOSE, proposed_block)


    def process_proposal(self, proposed_block: Block, leader_id: int) -> None:
        """
        Process proposal.

        Args:
            proposed_block (Block): block proposal
            leader_id (int): leader of the epoch when block was proposed

        Raises:
            ProtocolError: raises error when block is not valid or does not
                extend the longest notarized chain
        """
        # Get leader's public key
        leader_public_key = self.servers_public_key[leader_id]

        # Get latest block(s) from the longest notarized chain(s)
        longest_notarized_blocks = self.blockchain.get_longest_notarized_blocks()

        # Check if proposed block extends from one of the longest notarized chains
        longest_notarized_block = proposed_block.extends_from(longest_notarized_blocks)

        if longest_notarized_block is None:
            raise ProtocolError

        # Check if the proposed block is valid
        valid_block = proposed_block.check_signature(leader_public_key)
        if not valid_block:
            raise ProtocolError
        
        # Add leader's vote to the proposed block
        proposed_block.add_leader_vote(leader_id)

        # Add proposed block to server's blockchain
        proposed_block.set_parent_epoch(longest_notarized_block.get_epoch())
        self.blockchain.add_block(proposed_block)
        logging.debug(f"New block proposal for epoch {proposed_block.get_epoch()} (proposer: {leader_id}).\n")


    def vote(self, proposed_block: Block) -> None:
        """
        Vote for the proposed block.
        """
        # Create vote for the proposed block using server's private key
        vote_block = proposed_block.create_vote(self.private_key)
        proposed_block.add_vote((self.server_id, vote_block))

        # Send vote to every server participating in the protocol
        self.send_message(MessageType.VOTE, vote_block)


    def process_vote(self, vote: Block, block: Block, voter: int) -> None:
        """
        Process vote.

        Args:
            vote (Block): vote
            block (Block): block
            voter (int): ID of the server that voted
        """
        # Add valid (and not repeated) votes to the block
        if Block.check_vote(vote, block, self.servers_public_key[voter]):
            block.add_vote((voter, vote))
            logging.debug(f"New vote for block from epoch {block.get_epoch()} (voter: {voter}).\n")
        
        # Notarize the block if there are sufficient valid votes (2f+1)
        if len(block.get_votes()) >= 2*self.f+1 and block.get_status() == BlockStatus.PROPOSED:
            block.notarize()
            logging.info(f"Block from epoch {block.get_epoch()} was notarized.\n")
            self.finalize()


    def finalize(self) -> None:
        """
        Finalize the notarized chain up to the second of the three blocks,
        after observing three adjacent blocks with consecutive epochs.
        """
        if self.epoch.value > 2:
            finalized_blocks = self.blockchain.finalize()
            if finalized_blocks:
                logging.info(f"Blocks from epochs {', '.join([str(block.get_epoch()) for block in finalized_blocks])} were finalized.\n")
                # Execute clients' transactions
                # execute_transactions(finalized_blocks)


    def get_epoch_leader(self) -> int:
        """
        Get leader's id of the current epoch.

        Returns:
            int: leader's id
        """
        leader = self.random_object.randrange(0, self.num_replicas)
        self.epoch_leaders.append(leader)
        return leader


    def start(self) -> NoReturn:
        """
        Start Streamlet.
        """
        self.blockchain.add_genesis_block()
        while True:
            try:
                self.start_new_epoch()
            except TimeoutError:
                logging.info("Timeout triggered: epoch reached its end.\n")
            finally:
                logging.info(f"Blockchain - {self.blockchain}\n")


    def process_messages(self, start_time: float) -> None:
        """
        Process received messages.
        
        More details:
        - Stores proposals and votes for epochs higher than the current
            epoch for posterior processing.
        - Ignores repeated proposals and votes.
        - Adds valid votes to blocks from previous epochs.
        - Adds valid proposals from previous epochs to the blockchain.

        Args:
            start_time (float): time when current epoch started

        Raises:
            TimeoutError: error is raised when epoch duration is exceeded
        """
        while True:
            remaining_time = self.epoch_duration - (time.time() - start_time)
            if remaining_time <= 0:
                raise TimeoutError
            message = self.get_early_message()
            if message is None:
                message = self.communication.get_message(remaining_time)
            sender = message.get_sender()
            block = message.get_content()
            block_epoch = block.get_epoch()
            
            # Store messages that arrive early for posterior processing (when time is adequate)
            if block_epoch > self.epoch.value:
                self.early_messages.append(message)
                continue
            logging.debug(f"Message type - {message.get_type()}\n")

            # Add new valid proposed blocks to the blockchain
            # Vote for the block, if block was received in the current epoch
            if message.get_type() == MessageType.PROPOSE:
                if block_epoch <= self.epoch.value:
                    # Check if the proposer's ID matches the leader's ID
                    if sender == self.epoch_leaders[block_epoch]:
                        if self.blockchain.get_block(block_epoch) is None:
                            # Echo received proposal
                            self.send_message(MessageType.ECHO, message)
                            try:
                                self.process_proposal(block, sender)
                            except ProtocolError:
                                continue
                            if block_epoch == self.epoch.value:
                                self.vote(block)
            
            # Add votes to blocks (from current and past epochs)
            elif message.get_type() == MessageType.VOTE:
                # Get block for the vote's epoch from server's blockchain
                proposed_block = self.blockchain.get_block(block_epoch)
                if proposed_block and sender not in [vote[0] for vote in proposed_block.get_votes()]:
                    # Echo received vote
                    self.send_message(MessageType.ECHO, message)
                    self.process_vote(block, proposed_block, sender)


    def get_early_message(self) -> Message | None:
        """
        Get early message. Only returns message if it can be handled
        in the current epoch.

        Returns:
            (Message | None): message for current epoch
        """
        messages_epoch = [message.get_content().get_epoch() for message in self.early_messages]
        if self.epoch.value in messages_epoch:
            index = messages_epoch.index(self.epoch.value)
            return self.early_messages.pop(index)
        return None


    def send_message(self, message_type: MessageType, content: Block | Message) -> None:
        """
        Send message to every server.

        Args:
            message_type (MessageType): type of the message
            content (Block or Message): content to send
        """
        message = Message(
            message_type,
            content,
            self.server_id
        ).to_bytes()
        self.communication.broadcast(message)


class ProtocolError(Exception):
    pass