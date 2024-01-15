from enum import Enum

class MessageType(Enum):
    """
    Class than contains the different types of messages exchanged in the protocol.
    """
    REQUEST = 0
    PROPOSE = 1
    VOTE = 2
    ECHO = 3