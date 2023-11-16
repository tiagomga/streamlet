import pickle

class Message:
    """
    Class that sets the structure of a message.
    """

    def __init__(self, type, content, sender_id):
        self.type = type
        self.content = content
        self.sender_id = sender_id


    @staticmethod
    def to_bytes(message):
        return pickle.dumps(message)


    @staticmethod
    def from_bytes(bytes):
        return pickle.loads(bytes)


    def __str__(self):
        return f"({self.type}, {self.content}, {self.sender_id})"