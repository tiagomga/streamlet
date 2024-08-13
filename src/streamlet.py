import random
import time
import logging
import socket
from multiprocessing import Value, Queue
from typing import NoReturn
from pickle import PickleError
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
        else:
            self.vote(epoch_leader, start_time)
        self.notarize(start_time)
        self.finalize()


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
        certificate = None
        if self.epoch.value > 1:
            certificate = Certificate(freshest_notarized_block)
            certificate = certificate.to_bytes()

        # Send block proposal to every server participating in the protocol
        propose_message = Message(
            MessageType.PROPOSE,
            proposed_block.to_bytes(include_signature=True),
            self.server_id,
            certificate
        ).to_bytes()
        self.communication.broadcast(propose_message)


    def vote(self, leader_id: int, start_time: float) -> None:
        """
        Vote for the proposed block.
        """
        # Get proposed block for the current epoch
        proposer_id, proposed_block, certificate = self.get_message(start_time)
        
        # Get leader's public key
        leader_public_key = self.servers_public_key[leader_id]

        # Get latest block from the longest notarized chain
        freshest_notarized_block = self.blockchain.get_freshest_notarized_block()

        if certificate is not None:
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
        valid_block = proposed_block.check_validity(leader_public_key, self.epoch.value, freshest_notarized_block)
        if not valid_block:
            raise ProtocolError

        # Add leader's vote to the proposed block
        proposed_block.add_leader_vote(proposer_id)
        
        # Create vote for the proposed block using server's private key
        _vote = proposed_block.create_vote(self.private_key)
        proposed_block.add_vote((self.server_id, _vote))

        # Add proposed block to server's blockchain
        proposed_block.set_parent_epoch(freshest_notarized_block.get_epoch())
        self.blockchain.add_block(proposed_block)

        # Send vote to every server participating in the protocol
        vote_message = Message(
            MessageType.VOTE,
            _vote.to_bytes(include_signature=True),
            self.server_id
        ).to_bytes()
        self.communication.broadcast(vote_message)


    def notarize(self, start_time: float) -> None:
        """
        Notarize block after getting 2f + 1 votes.
        """
        # Get proposed block for the current epoch from server's blockchain
        proposed_block = self.blockchain.get_block(self.epoch.value)

        # For every vote, check its signature validity
        # If it is valid, add vote to the proposed block
        num_votes = len(proposed_block.get_votes())
        num_votes_left = 2*self.f+1 - num_votes
        for i in range(num_votes_left):
            sender, vote = self.get_message(start_time)
            valid_vote = Block.check_vote(vote, proposed_block, self.servers_public_key[sender])
            if valid_vote:
                num_votes += 1
                proposed_block.add_vote((sender, vote))
        
        # Check if there are sufficient valid votes; then, notarize the proposed block
        if num_votes >= 2*self.f+1:
            proposed_block.notarize()


    def finalize(self) -> None:
        """
        Finalize the notarized chain up to the second of the three blocks,
        after observing three adjacent blocks with consecutive epochs.
        """
        if self.epoch.value > 1:
            finalized_blocks = self.blockchain.finalize()
            # Execute clients' transactions
            # if finalized_blocks:
            #     execute_transactions(finalized_blocks)


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
                logging.info("Epoch ended abruptly: a timeout was triggered.\n")
            except ProtocolError:
                logging.info("Epoch ended abruptly: invalid block.\n")
            finally:
                logging.info(f"Blockchain - {self.blockchain}\n\n")
                end_time = time.time()
                epoch_duration = end_time - start_time
                if epoch_duration < self.epoch_duration:
                    time.sleep(self.epoch_duration - epoch_duration)


    def get_message(self, start_time: float) -> tuple:
        """
        Get message. Returns proposal or vote for the current epoch.
        
        More details:
        - Ignores proposals and votes for epochs higher than the current epoch.
        - Ignores repeated proposals and votes.
        - Adds valid votes to blocks from previous epochs.
        - Adds valid proposals from previous epochs to the blockchain.

        Args:
            start_time (float): time when current epoch started

        Raises:
            TimeoutError: error is raised when epoch duration is exceeded

        Returns:
            tuple: tuple with proposal or vote, along with sender's id
        """
        while True:
            remaining_time = self.epoch_duration - (time.time() - start_time)
            if remaining_time <= 0:
                raise TimeoutError
            message = self.communication.get_message(remaining_time)
            sender = message.get_sender()
            try:
                block = Block.from_bytes(message.get_content())
            except PickleError:
                logging.error("Block cannot be deserialized.\n")
                continue
            if not block.check_type_integrity():
                logging.error("Block attributes do not contain the correct type(s).\n")
                continue
            certificate = message.get_certificate()
            if certificate is not None:
                certificate = Certificate.from_bytes(certificate)
            block_epoch = block.get_epoch()
            logging.debug(f"Message type - {message.get_type()}\n\n")

            # Current epoch - return propose message if proposed block is new to the blockchain
            # Past epochs - add to the blockchain if proposed block is valid and new to the blockchain
            if message.get_type() == MessageType.PROPOSE:
                if block_epoch <= self.epoch.value:
                    # Check if the proposer's ID matches the leader's ID
                    if sender != self.epoch_leaders[block_epoch]:
                        continue
                    try:
                        self.blockchain.get_block(block_epoch)
                    except KeyError:
                        if block_epoch == self.epoch.value:
                            logging.debug(f"New proposal (epoch: {self.epoch.value} | proposer: {sender})\n\n")
                            return (sender, block, certificate)
                        else:
                            logging.debug(f"Old proposal (epoch: {block_epoch} | proposer: {sender})\n\n")
                            freshest_notarized_block = self.blockchain.get_freshest_notarized_block()
                            valid_block = block.check_validity(self.servers_public_key[sender], block_epoch, freshest_notarized_block)
                            if valid_block:
                                block.add_leader_vote(sender)
                                block.set_parent_epoch(freshest_notarized_block.get_epoch())
                                self.blockchain.add_block(block)
            
            # Return vote message if vote is new to the proposed block
            elif message.get_type() == MessageType.VOTE:
                try:
                    blockchain_block = self.blockchain.get_block(block_epoch)
                except KeyError:
                    continue
                if sender not in [vote[0] for vote in blockchain_block.get_votes()]:
                    if block_epoch == self.epoch.value:
                        logging.debug(f"New vote for current epoch (epoch: {self.epoch.value} | voter: {sender})\n\n")
                        return (sender, block)
                    else:
                        valid_block = Block.check_vote(block, blockchain_block, self.servers_public_key[sender])
                        if valid_block:
                            blockchain_block.add_vote((sender, block))
                            logging.debug(f"New vote for past epoch (epoch: {blockchain_block.get_epoch()} | voter: {sender})\n\n")
                            if blockchain_block.get_status() == BlockStatus.PROPOSED and len(blockchain_block.get_votes()) >= 2*self.f+1:
                                blockchain_block.notarize()


    def send_message(self, message_type: MessageType, block: Block) -> None:
        message = Message(
            message_type,
            block.to_bytes(include_signature=True),
            self.server_id
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
        
        message = Message(
            MessageType.RECOVERY_REQUEST,
            block_request.to_bytes(include_signature=True),
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
                if reply_message.get_type() == MessageType.RECOVERY_REPLY:
                    missing_block = Block.from_bytes(reply_message.get_content())
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