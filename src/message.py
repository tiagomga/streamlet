import pickle
import logging
from typing import Self
import crypto
from ui import UI
from block import Block
from messagetype import MessageType
from certificate import Certificate

class Message:
    """
    Class that sets the structure of a message.
    """

    def __init__(self, type: MessageType, content: Block | Self, sender_id: int, certificate: Certificate = None, ui: UI = None) -> None:
        self.type = type
        self.content = content
        self.sender_id = sender_id
        self.certificate = certificate
        self.ui = ui


    def get_type(self) -> MessageType:
        """
        Get type of message.

        Returns:
            MessageType: type of message (REQUEST, PROPOSE, VOTE)
        """
        return self.type


    def get_content(self) -> Block | Self:
        return self.content


    def get_sender(self) -> int:
        """
        Get sender's ID of message.

        Returns:
            int: ID of the sender
        """
        return self.sender_id


    def get_certificate(self) -> Certificate:
        """
        Get quorum certificate for the freshest notarized block.

        Returns:
            tuple: quorum certificate
        """
        return self.certificate


    def get_ui(self) -> UI:
        """
        Get unique identifier (UI).

        Returns:
            UI: unique identifier
        """
        return self.ui


    def set_ui(self, ui: UI) -> None:
        """
        Set unique identifier (UI).

        Args:
            ui (UI): unique identifier
        """
        self.ui = ui


    def calculate_hash(self) -> str:
        """
        Calculate hash.

        Returns:
            str: hash of the message
        """
        content = [
            self.type,
            self.content.to_bytes(),
            self.sender_id,
        ]
        if isinstance(self.certificate, Certificate):
            content.append(self.certificate.to_bytes())
        else:
            content.append(self.certificate)
        content = pickle.dumps(content)
        return crypto.calculate_hash(content)


    def to_bytes(self) -> bytes:
        """
        Convert Message to bytes.

        Returns:
            bytes: bytes of Message object
        """
        if self.type == MessageType.PK_EXCHANGE:
            data = (self.type, crypto.serialize_public_key(self.content), self.sender_id, self.certificate, self.ui)
        elif self.type == MessageType.PROPOSE:
            data = (self.type, self.content.to_bytes(), self.sender_id, self.certificate.to_bytes(), self.ui.to_bytes())
        elif self.type in [MessageType.VOTE, MessageType.TIMEOUT]:
            data = (self.type, self.content.to_bytes(), self.sender_id, self.certificate, self.ui.to_bytes())
        elif self.type == MessageType.RECOVERY_REQUEST:
            data = (self.type, self.content.to_bytes(), self.sender_id, self.certificate, self.ui)
        elif self.type == MessageType.RECOVERY_REPLY:
            data = (self.type, self.content.to_bytes(include_votes=True), self.sender_id, self.certificate, self.ui)
        return pickle.dumps(data)


    @staticmethod
    def from_bytes(data_bytes: bytes) -> Self | None:
        """
        Convert bytes to Message. Additionally, check if instance attributes
        have the correct type.

        Args:
            data_bytes (bytes)

        Returns:
            Message: Message object from bytes
        """
        try:
            data = pickle.loads(data_bytes)
        except pickle.PickleError:
            logging.error("Message cannot be unpickled.\n")
            return None
        try:
            message_type, content, sender_id, certificate, ui = data
        except ValueError:
            logging.error("Attributes cannot be unpacked from tuple.\n")
            return None
        if (isinstance(message_type, MessageType) and isinstance(content, bytes)
                and isinstance(sender_id, int)):
            if message_type == MessageType.PK_EXCHANGE:
                try:
                    crypto.load_public_key(content)
                except ValueError:
                    logging.error("Public key cannot be deserialized.\n")
                    return None
                certificate = None
            elif message_type == MessageType.PROPOSE:
                content = Block.from_bytes(content)
                if not (isinstance(certificate, bytes) and isinstance(ui, bytes)):
                    logging.error("Block certificate or UI cannot be deserialized (not bytes type).\n")
                    return None
                certificate = Certificate.from_bytes(certificate)
                ui = UI.from_bytes(ui)
                if certificate is None or ui is None:
                    logging.error("Block certificate or UI cannot be deserialized.\n")
                    return None
            elif message_type in [MessageType.VOTE, MessageType.TIMEOUT]:
                content = Block.from_bytes(content)
                certificate = None
                if not isinstance(ui, bytes):
                    logging.error("UI cannot be deserialized (not bytes type).\n")
                    return None
                ui = UI.from_bytes(ui)
                if ui is None:
                    logging.error("UI cannot be deserialized.\n")
                    return None
            elif message_type in [MessageType.RECOVERY_REQUEST, MessageType.RECOVERY_REPLY]:
                content = Block.from_bytes(content)
                certificate = None
                ui = None
            else:
                content = None
        else:
            logging.error("Message attributes do not contain the correct type(s).\n")
            return None
        if content is None:
            logging.error("Message content cannot be deserialized.\n")
            return None
        return Message(message_type, content, sender_id, certificate, ui)


    def __str__(self) -> str:
        """
        String representation of Message.

        Returns:
            str: string representation of Message
        """
        return f"({self.type}, {self.content}, {self.certificate}, {self.sender_id})"