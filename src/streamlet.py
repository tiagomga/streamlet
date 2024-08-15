import random
import time
import logging
import socket
from multiprocessing import Value, Queue
from typing import NoReturn
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPrivateKey
from block import Block
from blockstatus import BlockStatus
from message import Message
from messagetype import MessageType
from blockchain import Blockchain
from communicationsystem import CommunicationSystem
from certificate import Certificate

class Streamlet:
    """
    Streamlet protocol.
    """

    def __init__(self, server_id: int, communication: CommunicationSystem, private_key: RSAPrivateKey, servers_public_key: dict, recovery_queue: Queue, recovery_port: int, f: int = 1) -> None:
        """
        Constructor.
        """
        self.server_id = server_id
        self.communication = communication
        self.private_key = private_key
        self.servers_public_key = servers_public_key
        self.recovery_queue = recovery_queue
        self.recovery_port = recovery_port
        self.epoch = Value("i", 0)
        self.epoch_duration = 5
        self.epoch_leaders = [None]
        self.f = f
        self.num_replicas = 3*f + 1
        self.blockchain = Blockchain()
        self.random_object = random.Random()
        self.random_object.seed(0)


    def start_new_epoch(self) -> None:
        """
        Start a new epoch.
        """
        start_time = time.time()
        self.update_recovery_queue()
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

        # Get latest block from the longest notarized chain
        freshest_notarized_block = self.blockchain.get_freshest_notarized_block()

        # Create block proposal
        proposed_block = Block(
            self.epoch.value,
            [f"request {self.epoch.value}"],
            freshest_notarized_block.get_hash(),
            freshest_notarized_block.get_epoch()
        )

        # Sign the block
        proposed_block.sign(self.private_key)

        # Add leader's vote to the proposed block
        proposed_block.add_leader_vote(self.server_id)

        # Add block to server's blockchain
        self.blockchain.add_block(proposed_block)

        # Create certificate for the freshest notarized block
        certificate = Certificate(freshest_notarized_block)

        # Send block proposal to every server participating in the protocol
        self.send_message(MessageType.PROPOSE, proposed_block, certificate)


    def process_proposal(self, proposed_block: Block, certificate: Certificate, leader_id: int) -> None:
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

        # Get latest block from the longest notarized chain
        freshest_notarized_block = self.blockchain.get_freshest_notarized_block()

        if self.epoch.value > 1:
            if certificate.check_validity(self.servers_public_key, 2*self.f+1):
                if not certificate.extends_freshest_chain(freshest_notarized_block):
                    if certificate.get_epoch() > freshest_notarized_block.get_epoch():
                        self.start_recovery_request(certificate.get_epoch())
                        freshest_notarized_block = self.blockchain.get_freshest_notarized_block()
                    else:
                        return
            else:
                return

        # Check if the proposed block is valid
        valid_block = proposed_block.check_validity(leader_public_key)
        if not valid_block:
            raise ProtocolError
        
        # Add leader's vote to the proposed block
        proposed_block.add_leader_vote(leader_id)

        # Add proposed block to server's blockchain
        proposed_block.set_parent_epoch(freshest_notarized_block.get_epoch())
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
        if self.epoch.value > 1:
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
                start_time = time.time()
                self.start_new_epoch()
            except TimeoutError:
                logging.info("Timeout triggered: epoch reached its end.\n")
            finally:
                logging.info(f"Blockchain - {self.blockchain}\n")
                end_time = time.time()
                epoch_duration = end_time - start_time
                if epoch_duration < self.epoch_duration:
                    time.sleep(self.epoch_duration - epoch_duration)


    def process_messages(self, start_time: float) -> None:
        """
        Process received messages.
        
        More details:
        - Ignores proposals and votes for epochs higher than the current epoch.
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
            message = self.communication.get_message(remaining_time)
            sender = message.get_sender()
            block = message.get_content()
            certificate = message.get_certificate()
            block_epoch = block.get_epoch()
            logging.debug(f"Message type - {message.get_type()}\n")

            # Add new valid proposed blocks to the blockchain
            # Vote for the block, if block was received in the current epoch
            if message.get_type() == MessageType.PROPOSE:
                if block_epoch <= self.epoch.value:
                    # Check if the proposer's ID matches the leader's ID
                    if sender == self.epoch_leaders[block_epoch]:
                        try:
                            self.blockchain.get_block(block_epoch)
                        except KeyError:
                            try:
                                self.process_proposal(block, certificate, sender)
                            except ProtocolError:
                                continue
                            if block_epoch == self.epoch.value:
                                self.vote(block)
            
            # Add votes to blocks (from current and past epochs)
            elif message.get_type() == MessageType.VOTE:
                # Get block for the vote's epoch from server's blockchain
                try:
                    proposed_block = self.blockchain.get_block(block_epoch)
                except KeyError:
                    continue
                if sender not in [vote[0] for vote in proposed_block.get_votes()]:
                    self.process_vote(block, proposed_block, sender)


    def send_message(self, message_type: MessageType, block: Block, certificate: Certificate | None = None) -> None:
        """
        Send message to every server.

        Args:
            message_type (MessageType): type of the message
            block (Block): block to send
            certificate (Certificate or None): certificate for freshest notarized block
        """
        message = Message(
            message_type,
            block,
            self.server_id,
            certificate
        ).to_bytes()
        self.communication.broadcast(message)


    def update_recovery_queue(self) -> None:
        """
        Update `recovery_queue` with the latest version of `blockchain`.
        """
        if self.recovery_queue.empty():
            self.recovery_queue.put(self.blockchain)
        else:
            self.recovery_queue.get()
            self.recovery_queue.put(self.blockchain)


    def start_recovery_request(self, epoch: int, recovery_socket: socket.socket | None = None) -> None:
        """
        Start recovery request.
        Communicate with other servers to recover block from `epoch`.

        Args:
            epoch (int): epoch number
            recovery_socket (socket.socket | None, optional): socket to perform recovery. Defaults to None.
        """
        logging.info(f"Initiating recovery mechanism to request block from epoch {epoch}.\n")
        block_request = Block(epoch, [], "")
        block_request.set_signature("None")
        
        message = Message(
            MessageType.RECOVERY_REQUEST,
            block_request,
            self.server_id
        ).to_bytes()

        if recovery_socket is None:
            recovery_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            recovery_socket.bind(("127.0.0.1", self.recovery_port+self.server_id))
            recovery_socket.settimeout(1)
            recovery_socket.listen()

        servers_id = list(self.servers_public_key.keys())
        servers_id.remove(self.server_id)
        random_server = random.choice(servers_id)
        servers_id.remove(random_server)
        self.communication.send(message, random_server)

        while True:
            try:
                reply_socket, address = recovery_socket.accept()
                data = reply_socket.recv(8192)
            except TimeoutError:
                data = None
            if data:
                reply_message = Message.from_bytes(data)
                if reply_message:
                    if reply_message.get_type() == MessageType.RECOVERY_REPLY:
                        missing_block = reply_message.get_content()
                        if missing_block.get_epoch() == epoch:
                            missing_block.calculate_hash()
                            valid_votes = 0
                            for sender, vote in missing_block.get_votes():
                                if Block.check_vote(vote, missing_block, self.servers_public_key[sender]):
                                    valid_votes += 1
                            if valid_votes >= 2*self.f+1:
                                missing_block.notarize()
                                self.blockchain.add_block(missing_block)
                                reply_socket.close()
                                try:
                                    parent_epoch = missing_block.get_parent_epoch()
                                    if parent_epoch < epoch:
                                        parent_block = self.blockchain.get_block(parent_epoch)
                                        if parent_block.is_parent(missing_block):
                                            break
                                except KeyError:
                                    self.start_recovery_request(parent_epoch, recovery_socket=recovery_socket)
                                    break
                reply_socket.close()
            random_server = random.choice(servers_id)
            servers_id.remove(random_server)
            self.communication.send(message, random_server)

        recovery_socket.close()
        logging.info(f"Block from epoch {epoch} was recovered successfully.\n")


class ProtocolError(Exception):
    pass