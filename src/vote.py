import pickle

class Vote:
    """
    Class that represents a vote.
    """

    def __init__(self, voter: int, epoch: int, message_hash: str, ui: UI) -> None:
        """
        Constructor.

        Args:
            voter (int): id of the voter
            epoch (int): epoch from the message
            message_hash (str): hash of the message
            ui (UI): unique identifier
        """
        self.voter = voter
        self.epoch = epoch
        self.message_hash = message_hash
        self.ui = ui


    def to_bytes(self) -> bytes:
        """
        Convert Vote to bytes.

        Returns:
            bytes: bytes of Vote object
        """
        data = (self.voter, self.epoch, self.message_hash, self.ui.to_bytes())
        return pickle.dumps(data)
