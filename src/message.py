import pickle
from typing import Self
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
    def from_bytes(bytes: bytes) -> Self:
        """
        Convert bytes to Message.

        Args:
            bytes (bytes)

        Returns:
            Message: Message object from bytes
        """
        data = pickle.loads(bytes)
        return Message(data[0], data[1], data[2])


    def check_type_integrity(self) -> bool:
        """
        Check if instance attributes have the correct type.

        Returns:
            bool: True if every verified attribute has the correct type, else return False
        """
        return isinstance(self.type, MessageType) and \
            isinstance(self.content, (Block, Message, bytes)) and \
            isinstance(self.sender_id, int)


    def __str__(self) -> str:
        """
        String representation of Message.

        Returns:
            str: string representation of Message
        """
        return f"({self.type}, {self.content}, {self.sender_id})"