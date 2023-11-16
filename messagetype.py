from enum import Enum

class MessageType(Enum):
    """
    Class than contains the different types of message.
    """
    REQUEST = 0
    PROPOSE = 1
    VOTE = 2