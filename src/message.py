import pickle
from block import Block
from messagetype import MessageType

class Message:
    """
    Class that sets the structure of a message.
    """

    def __init__(self, type: MessageType, content: Block | 'Message', sender_id: int) -> None:
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


    def get_content(self) -> Block | 'Message':
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
        return pickle.dumps(self)


    @staticmethod
    def from_bytes(bytes: bytes) -> 'Message':
        """
        Convert bytes to Message.

        Args:
            bytes (bytes)

        Returns:
            Message: Message object from bytes
        """
        return pickle.loads(bytes)


    def __str__(self) -> str:
        """
        String representation of Message.

        Returns:
            str: string representation of Message
        """
        return f"({self.type}, {self.content}, {self.sender_id})"