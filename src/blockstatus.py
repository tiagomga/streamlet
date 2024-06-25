from enum import Enum

class BlockStatus(Enum):
    """
    Class than contains the different block's status.
    """
    PROPOSED = 0
    NOTARIZED = 1
    FINALIZED = 2