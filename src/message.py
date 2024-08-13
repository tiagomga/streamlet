import pickle
import logging
from typing import Self
import crypto
from block import Block
from messagetype import MessageType

class Message:
    """
    Class that sets the structure of a message.
    """

    def __init__(self, type: MessageType, content: Block | Self, sender_id: int) -> None:
        self.type = type
        self.content = content
        self.sender_id = sender_id


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


    def to_bytes(self) -> bytes:
        """
        Convert Message to bytes.

        Returns:
            bytes: bytes of Message object
        """
        data = (self.type, self.content, self.sender_id)
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
            message_type, content, sender_id = data
        except ValueError:
            logging.error("Attributes cannot be unpacked from tuple.\n")
            return None
        if isinstance(message_type, MessageType) and isinstance(sender_id, int):
            if message_type == MessageType.PK_EXCHANGE:
                content = crypto.load_public_key(content)
            elif message_type == MessageType.PROPOSE or message_type == MessageType.VOTE:
                content = Block.from_bytes(content)
            elif message_type == MessageType.ECHO:
                content = Message.from_bytes(content)
            else:
                content = None
        else:
            logging.error("Message attributes do not contain the correct type(s).\n")
            return None
        if content is None:
            logging.error("Message content cannot be deserialized.\n")
            return None
        return Message(message_type, content, sender_id)


    def __str__(self) -> str:
        """
        String representation of Message.

        Returns:
            str: string representation of Message
        """
        return f"({self.type}, {self.content}, {self.sender_id})"