import pickle
from types import NoneType
from typing import Self
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
    def from_bytes(bytes: bytes) -> Self:
        """
        Convert bytes to Message.

        Args:
            bytes (bytes)

        Returns:
            Message: Message object from bytes
        """
        data = pickle.loads(bytes)
        return Message(data[0], data[1], data[2], data[3])


    def check_type_integrity(self) -> bool:
        """
        Check if instance attributes have the correct type.

        Returns:
            bool: True if every verified attribute has the correct type, else return False
        """
        return type(self.type) is MessageType and \
            (type(self.content) is Block or type(self.content) is Message or type(self.content) is bytes) and \
            type(self.sender_id) is int and \
            (type(self.certificate) is Certificate or type(self.certificate) is NoneType or type(self.certificate) is bytes)


    def __str__(self) -> str:
        """
        String representation of Message.

        Returns:
            str: string representation of Message
        """
        return f"({self.type}, {self.content}, {self.certificate}, {self.sender_id})"