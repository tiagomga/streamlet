import sys
import random
import time
import json
import logging
import socket
import struct
from multiprocessing import Process, Value
from typing import NoReturn
from vote import Vote
from usig import USIG
from block import Block
from blockstatus import BlockStatus
from message import Message
from messagetype import MessageType
from blockchain import Blockchain
from communicationsystem import CommunicationSystem
from certificate import Certificate
from transactiongenerator import TransactionGenerator

class Streamlet:
    """
    Streamlet protocol.
    """

    def __init__(self, server_id: int, communication: CommunicationSystem, usig: USIG, usig_public_keys: dict,
                 epoch_duration: float, f: int, benchmark_threshold: int, benchmark_total: int) -> None:
        """
        Constructor.
        """
        self.server_id = server_id
        self.communication = communication
        self.usig = usig
        self.usig_public_keys = usig_public_keys
        self.usig_counters = {0: 0, 1: 0, 2: 0}
        self.recovery_port = 15000
        self.epoch = Value("i", 0)
        self.epoch_duration = epoch_duration
        self.delta = self.epoch_duration/2
        self.epoch_leaders = [None]
        self.f = f
        self.num_replicas = 2*f + 1
        self.blockchain = Blockchain()
        self.random_object = random.Random()
        self.random_object.seed(0)
        self.early_messages = []
        self.transaction_generator = TransactionGenerator()
        self.finalized_transactions = 0
        self.total_finalized_transactions = 0
        self.benchmark_threshold = benchmark_threshold
        self.benchmark_total = benchmark_total
        self.benchmark_time = []


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
        # Get clients' transactions
        transactions = self.transaction_generator.get_transactions()

        # Get latest block from the longest notarized chain
        freshest_notarized_block = self.blockchain.get_freshest_notarized_block()

        # Create block proposal
        proposed_block = Block(
            self.epoch.value,
            transactions,
            freshest_notarized_block.get_hash(),
            freshest_notarized_block.get_epoch()
        )

        # Create certificate for the freshest notarized block
        certificate = Certificate(freshest_notarized_block)

        # Create and sign message with USIG
        message = Message(
            MessageType.PROPOSE,
            proposed_block,
            self.server_id,
            certificate
        )
        ui = self.usig.create_ui(message)
        message.set_ui(ui)

        # Add leader's vote to the proposed block
        leader_vote = Vote(self.server_id, self.epoch.value, message.calculate_hash(), ui)
        proposed_block.add_vote(leader_vote)

        # Add block to server's blockchain
        self.blockchain.add_block(proposed_block)

        # Send block proposal to every server participating in the protocol
        self.communication.broadcast(message.to_bytes())


    def process_proposal(self, message: Message) -> None:
        """
        Process proposal.

        Args:
            message (Message): proposal message

        Raises:
            ProtocolError: raises error when block is not valid or does not
                extend the longest notarized chain
        """
        # Get latest block from the longest notarized chain
        freshest_notarized_block = self.blockchain.get_freshest_notarized_block()

        certificate = message.get_certificate()
        proposed_block = message.get_content()

        if self.epoch.value > 1:
            if certificate.check_validity(self.usig_public_keys, self.f+1):
                if not certificate.extends_freshest_chain(freshest_notarized_block):
                    if certificate.get_epoch() > freshest_notarized_block.get_epoch():
                        self.start_recovery_request(certificate.get_epoch())
                        freshest_notarized_block = self.blockchain.get_freshest_notarized_block()
                    else:
                        return
            else:
                return
        
        # Check if proposed block extends from the freshest notarized chain
        if not proposed_block.is_child(freshest_notarized_block):
            raise ProtocolError
        
        # Add leader's vote to the proposed block
        leader_vote = Vote(message.get_sender(), message.get_content().get_epoch(), message.calculate_hash(), message.get_ui())
        proposed_block.add_vote(leader_vote)

        # Add proposed block to server's blockchain
        proposed_block.set_parent_epoch(freshest_notarized_block.get_epoch())
        self.blockchain.add_block(proposed_block)
        logging.debug(f"New block proposal for epoch {proposed_block.get_epoch()} (proposer: {message.get_sender()}).\n")


    def vote(self, proposed_block: Block) -> None:
        """
        Vote for the proposed block.
        """
        # Create vote for the proposed block using USIG
        vote_block = proposed_block.create_vote()
        message = Message(
            MessageType.VOTE,
            vote_block,
            self.server_id
        )
        ui = self.usig.create_ui(message)
        message.set_ui(ui)

        # Add own vote to the proposed block
        own_vote = Vote(self.server_id, self.epoch.value, message.calculate_hash(), ui)
        proposed_block.add_vote(own_vote)

        # Send vote to every server participating in the protocol
        self.communication.broadcast(message.to_bytes())


    def process_vote(self, message: Message, block: Block) -> None:
        """
        Process vote.

        Args:
            message (Message): message
            block (Block): block
        """
        # Add valid (and not repeated) votes to the block
        server_vote = Vote(message.get_sender(), message.get_content().get_epoch(), message.calculate_hash(), message.get_ui())
        block.add_vote(server_vote)
        logging.debug(f"New vote for block from epoch {block.get_epoch()} (voter: {message.get_sender()}).\n")
        
        # Notarize the block if there are sufficient valid votes (2f+1)
        if len(block.get_votes()) >= self.f+1 and block.get_status() == BlockStatus.PROPOSED:
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
                for block in finalized_blocks:
                    if block.get_epoch() >= 1:
                        self.finalized_transactions += len(block.get_transactions())
                if self.finalized_transactions >= self.benchmark_threshold:
                    elapsed_time = time.perf_counter() - self.benchmark_time[0]
                    self.benchmark_time.append(elapsed_time)
                    self.total_finalized_transactions += self.finalized_transactions
                    self.finalized_transactions = 0
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
        self.benchmark_time.append(time.perf_counter())
        while self.total_finalized_transactions < self.benchmark_total:
            try:
                self.start_new_epoch()
            except TimeoutError:
                logging.info("Timeout triggered: epoch reached its end.\n")
            finally:
                logging.info(f"Blockchain - {self.blockchain}\n")
        self.export_benchmark_results()


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
        timeout = False
        sent_timeout = False
        waiting_time = self.delta
        while True:
            remaining_time = waiting_time - (time.time() - start_time)
            if remaining_time <= 0:
                timeout = True
                remaining_time = None
            if timeout and not sent_timeout:
                timeout_block = Block(self.epoch.value+1, [], "")
                timeout_message = Message(
                    MessageType.TIMEOUT,
                    timeout_block,
                    self.server_id
                )
                ui = self.usig.create_ui(timeout_message)
                timeout_message.set_ui(ui)
                self.communication.broadcast(timeout_message.to_bytes())
                sent_timeout = True
                self.timeout_messages.append(timeout_message)
            message = self.get_early_message()
            if message is None:
                try:
                    message = self.communication.get_message(remaining_time)
                except TimeoutError:
                    continue
            sender = message.get_sender()
            if message.get_type() in [MessageType.PROPOSE, MessageType.VOTE, MessageType.TIMEOUT]:
                ui = message.get_ui()
                if ui.is_next(self.usig_counters[sender]):
                    self.usig_counters[sender] += 1
                else:
                    self.early_messages.append(message)
                    continue
                if not USIG.verify_ui(ui, self.usig_public_keys[sender], message):
                    continue
            block = message.get_content()
            block_epoch = block.get_epoch()
            
            # Store messages that arrive early for posterior processing (when time is adequate) (except for timeout messages)
            if block_epoch > self.epoch.value and message.get_type() != MessageType.TIMEOUT:
                self.usig_counters[sender] -= 1
                self.early_messages.append(message)
                continue
            logging.debug(f"Message type - {message.get_type()}\n")

            # Add new valid proposed blocks to the blockchain
            # Vote for the block, if block was received in the current epoch
            if message.get_type() == MessageType.PROPOSE:
                # Ensure that proposer's ID matches the leader's ID and proposal is new
                if (block_epoch <= self.epoch.value and sender == self.epoch_leaders[block_epoch]
                        and self.blockchain.get_block(block_epoch) is None):
                    try:
                        self.process_proposal(message)
                    except ProtocolError:
                        continue
                    if block_epoch == self.epoch.value and not timeout:
                        waiting_time = self.epoch_duration
                        self.vote(block)
            
            # Add votes to blocks (from current and past epochs)
            elif message.get_type() == MessageType.VOTE:
                # Get block for the vote's epoch from server's blockchain
                proposed_block = self.blockchain.get_block(block_epoch)
                if proposed_block and sender not in [vote.get_voter() for vote in proposed_block.get_votes()]:
                    self.process_vote(message, proposed_block)
                    current_epoch_block = self.blockchain.get_block(self.epoch.value)
                    if current_epoch_block and current_epoch_block.get_status() == BlockStatus.NOTARIZED:
                        break
                elif proposed_block is None:
                    self.early_messages.append(message)
            
            # Reply with missing block in parallel
            elif message.get_type() == MessageType.RECOVERY_REQUEST:
                recovery_process = Process(target=self.start_recovery_reply, args=(block_epoch, sender, self.blockchain))
                recovery_process.start()
            
            # Collect timeout messages and progress when consensus is reached
            elif message.get_type() == MessageType.TIMEOUT:
                if (sender not in [timeout_message.get_sender() for timeout_message in self.timeout_messages
                                   if timeout_message.get_content().get_epoch() == block_epoch]
                        and block_epoch > self.epoch.value):
                    self.timeout_messages.append(message)
                    if len(self.timeout_messages) >= self.f+1:
                        timeout_epochs = [timeout_message.get_content().get_epoch() for timeout_message in self.timeout_messages]
                        for epoch in set(timeout_epochs):
                            if timeout_epochs.count(epoch) >= self.f+1:
                                for _ in range(epoch-self.epoch.value-1):
                                    self.get_epoch_leader()
                                self.epoch.value = epoch-1
                                self.timeout_messages = list(filter(lambda message: message.get_content().get_epoch() > epoch, self.timeout_messages))
                                raise TimeoutError


    def get_early_message(self) -> Message | None:
        """
        Get early message. Only returns message if it can be handled
        in the current epoch.

        Returns:
            (Message | None): message for current epoch
        """
        messages_epoch = [message.get_content().get_epoch() for message in self.early_messages]
        for index, epoch in enumerate(messages_epoch):
            message = self.early_messages[index]
            if epoch <= self.epoch.value:
                if message.get_type() == MessageType.VOTE and self.blockchain.get_block(epoch) is None:
                    continue
                elif not message.get_ui().is_next(self.usig_counters[message.get_sender()]):
                    continue
                return self.early_messages.pop(index)
            elif (message.get_type() == MessageType.TIMEOUT
                    and message.get_ui().is_next(self.usig_counters[message.get_sender()])):
                return self.early_messages.pop(index)


    def start_recovery_request(self, epoch: int, recovery_socket: socket.socket | None = None, close_socket: bool = True) -> None:
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
            block_request,
            self.server_id
        ).to_bytes()

        if recovery_socket is None:
            recovery_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            recovery_socket.bind(("127.0.0.1", self.recovery_port+self.server_id))
            recovery_socket.settimeout(1)
            recovery_socket.listen()

        servers_id = list(self.usig_public_keys.keys())
        servers_id.remove(self.server_id)
        random_server = random.choice(servers_id)
        servers_id.remove(random_server)
        self.communication.send(message, random_server)

        while True:
            try:
                reply_socket, address = recovery_socket.accept()
                reply_socket.settimeout(1)
                data = self.communication.read_all_from_socket(reply_socket)
            except TimeoutError:
                logging.debug(f"Recovery request to server {random_server} timed out.\n")
                data = None
            if data:
                reply_message = Message.from_bytes(data)
                if reply_message and reply_message.get_type() == MessageType.RECOVERY_REPLY:
                    missing_block = reply_message.get_content()
                    if missing_block.get_epoch() == epoch:
                        missing_block.calculate_hash()
                        valid_votes = 0
                        for vote in missing_block.get_votes():
                            if USIG.verify_ui_from_vote(vote, self.usig_public_keys[vote.get_voter()]):
                                valid_votes += 1
                        if valid_votes >= self.f+1:
                            missing_block.notarize()
                            parent_epoch = missing_block.get_parent_epoch()
                            if parent_epoch < epoch:
                                parent_block = self.blockchain.get_block(parent_epoch)
                                if parent_block is None:
                                    self.start_recovery_request(parent_epoch, recovery_socket=recovery_socket, close_socket=False)
                                    parent_block = self.blockchain.get_block(parent_epoch)
                                if parent_block.is_parent(missing_block):
                                    self.blockchain.add_block(missing_block)
                                    reply_socket.close()
                                    break
                reply_socket.close()
            random_server = random.choice(servers_id)
            servers_id.remove(random_server)
            self.communication.send(message, random_server)

        if close_socket:
            recovery_socket.close()
        logging.info(f"Block from epoch {epoch} was recovered successfully.\n")


    def start_recovery_reply(self, epoch: int, sender: int, blockchain: Blockchain) -> NoReturn:
        """
        Start recovery reply.

        Args:
            epoch (int): epoch for the request block
            sender (int): server ID
            blockchain (Blockchain): blockchain

        Returns:
            NoReturn: terminate process after sending the reply
        """
        requested_block = blockchain.get_block(epoch)

        if requested_block is None:
            sys.exit(1)

        reply_message = Message(
            MessageType.RECOVERY_REPLY,
            requested_block,
            self.server_id
        ).to_bytes()
        reply_message = struct.pack(">I", len(reply_message)) + reply_message

        reply_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        reply_socket.connect(('127.0.0.1', self.recovery_port+sender))
        reply_socket.sendall(reply_message)
        reply_socket.close()
        logging.info(f"Sent recovery reply to server {sender} for block in epoch {epoch}.\n")
        sys.exit(0)


    def export_benchmark_results(self):
        """
        Export benchmark results to file.
        """
        transaction_size = self.transaction_generator.get_transaction_size()
        transaction_number = self.transaction_generator.get_transaction_number()
        results = {
            "EPOCH_DURATION": self.epoch_duration,
            "FAULT_NUMBER": self.f,
            "TRANSACTION_SIZE": transaction_size,
            "TRANSACTION_NUMBER": transaction_number,
            "BENCHMARK_THRESHOLD": self.benchmark_threshold,
            "BENCHMARK_TOTAL": self.benchmark_total,
            "BENCHMARK_TIME": self.benchmark_time
        }
        with open(f"benchmark_{transaction_size}_{transaction_number}.json", "w") as output:
            json.dump(results, output, indent=2)


class ProtocolError(Exception):
    pass