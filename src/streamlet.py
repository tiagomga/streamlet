import random
import time
import logging
import sys
import socket
from queue import Empty
from multiprocessing import Process
from multiprocessing import Value
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

    def __init__(self, server_id: int, communication: CommunicationSystem, private_key: RSAPrivateKey, servers_public_key: dict, f: int = 1) -> None:
        """
        Constructor.
        """
        self.server_id = server_id
        self.recovery_port = 15000
        self.communication = communication
        self.private_key = private_key
        self.servers_public_key = servers_public_key
        self.epoch = Value("i", 0)
        self.epoch_duration = 5
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
        vote = Block(
            proposed_block.get_epoch(),
            None,
            proposed_block.get_parent_hash()
        )
        vote.set_signature(proposed_block.get_signature())
        proposed_block.add_vote((self.server_id, vote))

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

        # Check if the proposer's ID matches with the leader's ID
        if proposer_id != leader_id:
            raise Exception
        
        # Get leader's public key
        leader_public_key = self.servers_public_key[leader_id]

        # Get latest block from the longest notarized chain
        freshest_notarized_block = self.blockchain.get_freshest_notarized_block()

        if certificate is not None:
            if certificate.check_validity(freshest_notarized_block, self.servers_public_key, 2*self.f+1):
                if not certificate.extends_freshest_chain(freshest_notarized_block):
                    # Start recovery
                    self.start_recovery_request(certificate.get_epoch())
            else:
                return

        # Check if the proposed block is valid
        valid_block = proposed_block.check_validity(leader_public_key, self.epoch.value, freshest_notarized_block)
        if not valid_block:
            raise Exception
        
        # Add leader's vote to the proposed block
        leader_vote = Block(
            proposed_block.get_epoch(),
            None,
            proposed_block.get_parent_hash()
        )
        leader_vote.set_signature(proposed_block.get_signature())
        proposed_block.add_vote((proposer_id, leader_vote))
        
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
        return self.random_object.randrange(0, self.num_replicas)


    def start(self) -> NoReturn:
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
                if epoch_duration < self.epoch_duration:
                    time.sleep(self.epoch_duration - epoch_duration)
            except (Empty, TimeoutError):
                logging.debug("Epoch ended abruptly.")


    def get_message(self, start_time: float) -> tuple:
        while True:
            remaining_time = self.epoch_duration - (time.time() - start_time)
            if remaining_time <= 0:
                raise TimeoutError
            message = self.communication.get_message(remaining_time)
            sender = message.get_sender()
            block = Block.from_bytes(message.get_content())
            certificate = message.get_certificate()
            if certificate is not None:
                certificate = Certificate.from_bytes(certificate)
            block_epoch = block.get_epoch()
            logging.debug(f"Message type - {message.get_type()}\n\n")

            # Return propose message if proposed block is new to the blockchain
            if message.get_type() == MessageType.PROPOSE:
                if block_epoch == self.epoch.value:
                    try:
                        self.blockchain.get_block(block_epoch)
                    except KeyError:
                        logging.debug(f"New proposal (epoch: {self.epoch.value} | proposer: {sender})\n\n")
                        return (sender, block, certificate)
            
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
                        valid_block = Block.check_vote(block, blockchain_block, self.servers_public_key[sender])
                        if valid_block:
                            blockchain_block.add_vote((sender, block))
                            logging.debug(f"New vote for past epoch (epoch: {blockchain_block.get_epoch()} | voter: {sender})\n\n")
                            if blockchain_block.get_status() == BlockStatus.PROPOSED and len(blockchain_block.get_votes()) >= 2*self.f+1:
                                blockchain_block.notarize()
            
            # Prepare and send recovery reply in parallel
            elif message.get_type() == MessageType.RECOVERY_REQUEST:
                process = Process(target=self.start_recovery_reply, args=(message, self.blockchain))
                process.start()


    def start_recovery_reply(self, message, blockchain):
        sender = message.get_sender()
        epoch = Block.from_bytes(message.get_content()).get_epoch()
        block = blockchain.get_block(epoch)

        message = Message(
            MessageType.RECOVERY_REPLY,
            block.to_bytes(include_signature=True, include_votes=True),
            self.server_id
        ).to_bytes()

        reply_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        reply_socket.connect('127.0.0.1', self.recovery_port+sender)
        reply_socket.send(message)
        reply_socket.close()
        sys.exit(0)


    def start_recovery_request(self, epoch):
        block_request = Block(epoch, [], "")

        message = Message(
            MessageType.RECOVERY_REQUEST,
            block_request.to_bytes(),
            self.server_id
        ).to_bytes()

        servers_id = list(self.servers_public_key.keys())
        servers_id.remove(self.server_id)
        random_server = random.choice(servers_id)
        servers_id.remove(random_server)
        self.communication.send(message, random_server)
        
        recovery_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        recovery_socket.bind(("127.0.0.1", self.recovery_port+self.server_id))
        recovery_socket.listen()

        while True:
            reply_socket, address = recovery_socket.accept()
            data = reply_socket.recv(2048)
            if data:
                reply_message = Message.from_bytes(data)
                if reply_message.get_type() == MessageType.RECOVERY_REPLY:
                    missing_block = Block.from_bytes(reply_message.get_content())
                    valid_votes = 0
                    for sender, vote in missing_block.get_votes():
                        if vote.check_signature(self.servers_public_key[sender], content=missing_block.to_bytes()):
                            valid_votes += 1
                    if valid_votes >= 2*self.f+1:
                        missing_block.notarize()
                        self.blockchain.add_block(missing_block)
                        try:
                            reply_socket.close()
                            self.blockchain.get_block(missing_block.get_parent_epoch())
                            break
                        except KeyError:
                            self.start_recovery_request(missing_block.get_parent_epoch())
                random_server = random.choice(servers_id)
                servers_id.remove(random_server)
                self.communication.send(message, random_server)
            reply_socket.close()

        recovery_socket.close()
