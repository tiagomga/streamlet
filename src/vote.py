import pickle
import logging
from typing import Self
from ui import UI

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


    def get_voter(self) -> int:
        """
        Get ID of the voter.

        Returns:
            int: ID of the voter
        """
        return self.voter


    def get_epoch(self) -> int:
        """
        Get epoch.

        Returns:
            int: epoch
        """
        return self.epoch


    def to_bytes(self) -> bytes:
        """
        Convert Vote to bytes.

        Returns:
            bytes: bytes of Vote object
        """
        data = (self.voter, self.epoch, self.message_hash, self.ui.to_bytes())
        return pickle.dumps(data)

    
    @staticmethod
    def from_bytes(data_bytes: bytes) -> Self:
        """
        Convert bytes to Vote. Additionally, check if instance attributes
        have the correct type.

        Args:
            data_bytes (bytes)

        Returns:
            Vote: Vote object from bytes
        """
        try:
            data = pickle.loads(data_bytes)
        except pickle.PickleError:
            logging.error("Vote cannot be unpickled.\n")
            return None
        try:
            voter, epoch, message_hash, ui = data
        except ValueError:
            logging.error("Attributes cannot be unpacked from tuple.\n")
            return None
        if (isinstance(voter, int) and isinstance(epoch, int)
                and isinstance(message_hash, str) and isinstance(ui, bytes)):
            ui = UI.from_bytes(ui)
            if ui is None:
                logging.error("UI cannot be deserialized.\n")
                return None
            return Vote(voter, epoch, message_hash, ui)
        logging.error("Vote attributes do not contain the correct type(s).\n")
        return None