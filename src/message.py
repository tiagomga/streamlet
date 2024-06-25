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
        """
        Get type of message.

        Returns:
            MessageType: type of message (REQUEST, PROPOSE, VOTE)
        """
        return self.type


    def get_content(self):
        return self.content


    def get_sender(self):
        """
        Get sender's ID of message.

        Returns:
            int: ID of the sender
        """
        return self.sender_id


    def to_bytes(self):
        """
        Convert Message to bytes.

        Returns:
            bytes: bytes of Message object
        """
        return pickle.dumps(self)


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