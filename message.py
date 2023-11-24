import pickle

class Message:
    """
    Class that sets the structure of a message.
    """

    def __init__(self, type, content, sender_id):
        self.type = type
        self.content = content
        self.sender_id = sender_id


    def get_type(self):
        return self.type


    @staticmethod
    def to_bytes(message):
        """
        Convert Message to bytes.

        Args:
            message (Message)

        Returns:
            bytes: bytes of Message object
        """
        return pickle.dumps(message)


    @staticmethod
    def from_bytes(bytes):
        """
        Convert bytes to Message.

        Args:
            bytes (bytes)

        Returns:
            Message: Message object from bytes
        """
        return pickle.loads(bytes)


    def __str__(self):
        """
        String representation of Message.

        Returns:
            str: string representation of Message
        """
        return f"({self.type}, {self.content}, {self.sender_id})"