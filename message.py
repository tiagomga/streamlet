class Message:
    """
    Class that sets the structure of a message.
    """

    def __init__(self, type, content, sender_id):
        self.type = type
        self.content = content
        self.sender_id = sender_id