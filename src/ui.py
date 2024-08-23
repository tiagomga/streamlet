import pickle
import logging
from typing import Self

class UI:
    """
    Class that represents a Unique Identifier (UI).
    """

    def __init__(self, sequence_number: int, signature: str) -> None:
        """
        Constructor.

        Args:
            sequence_number (int): sequence number/counter value
            signature (str): signature
        """
        self.sequence_number = sequence_number
        self.signature = signature


    def get_sequence_number(self) -> int:
        """
        Get sequence number.

        Returns:
            int: sequence number/counter value
        """
        return self.sequence_number


    def get_signature(self) -> str:
        """
        Get signature.

        Returns:
            str: signature
        """
        return self.signature


    def is_next(self, sequence_number: int) -> bool:
        """
        Check if `sequence_number` is sequential to UI's sequence
        number.

        Args:
            sequence_number (int): sequence number/counter value

        Returns:
            bool: True if and only if the sequence number is sequential,
                else return False
        """
        return self.sequence_number == sequence_number+1


    def to_bytes(self) -> bytes:
        """
        Convert UI to bytes.

        Returns:
            bytes: bytes from UI object
        """
        return pickle.dumps((self.sequence_number, self.signature))


    @staticmethod
    def from_bytes(data_bytes: bytes) -> Self | None:
        """
        Convert bytes to UI. Additionally, check if instance attributes
        have the correct type.

        Args:
            data_bytes (bytes): UI in serialized form

        Returns:
            UI: UI object from bytes
        """
        try:
            data = pickle.loads(data_bytes)
        except pickle.PickleError:
            logging.error("UI cannot be unpickled.\n")
            return None
        try:
            sequence_number, signature = data
        except ValueError:
            logging.error("Attributes cannot be unpacked from tuple.\n")
            return None
        if isinstance(sequence_number, int) and isinstance(signature, str):
            return UI(sequence_number, signature)
        logging.error("UI attributes do not contain the correct type(s).\n")