import pickle
from types import NoneType
from typing import Self
import crypto
from block import Block
from messagetype import MessageType
from certificate import Certificate

class Message:
    """
    Class that sets the structure of a message.
    """

    def __init__(self, type: MessageType, content: Block | Self, sender_id: int, certificate: Certificate = None) -> None:
        self.type = type
        self.content = content
        self.sender_id = sender_id
        self.certificate = certificate


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


    def to_bytes(self) -> bytes:
        """
        Convert Message to bytes.

        Returns:
            bytes: bytes of Message object
        """
        data = (self.type, self.content, self.sender_id, self.certificate)
        return pickle.dumps(data)


    @staticmethod
    def from_bytes(bytes: bytes) -> Self | None:
        """
        Convert bytes to Message. Additionally, check if instance attributes
        have the correct type.

        Args:
            bytes (bytes)

        Returns:
            Message: Message object from bytes
        """
        data = pickle.loads(bytes)
        try:
            message_type, content, sender_id, certificate = data
        except ValueError:
            return None
        if isinstance(message_type, MessageType) and isinstance(sender_id, int):
            if message_type == MessageType.PK_EXCHANGE:
                content = crypto.load_public_key(content)
                certificate = None
            elif message_type == MessageType.PROPOSE:
                content = Block.from_bytes(content)
                certificate = Certificate.from_bytes(certificate)
                if certificate is None:
                    return None
            elif message_type in [MessageType.VOTE, MessageType.RECOVERY_REQUEST, MessageType.RECOVERY_REPLY]:
                content = Block.from_bytes(content)
                certificate = None
            else:
                content = None
        elif content is None:
            return None
        else:
            return None
        return Message(message_type, content, sender_id, certificate)


    def __str__(self) -> str:
        """
        String representation of Message.

        Returns:
            str: string representation of Message
        """
        return f"({self.type}, {self.content}, {self.certificate}, {self.sender_id})"