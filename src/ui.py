import pickle
import logging
from typing import Self

class UI:
    """
    Class that represents a Unique Identifier (UI).
    """

    def __init__(self, sequence_number: int, signature: str) -> None:
        self.sequence_number = sequence_number
        self.signature = signature


    def get_sequence_number(self) -> int:
        return self.sequence_number


    def get_signature(self) -> str:
        return self.signature


    def is_next(self, sequence_number: int) -> bool:
        return self.sequence_number == sequence_number+1


    def to_bytes(self) -> bytes:
        return pickle.dumps((self.sequence_number, self.signature))


    @staticmethod
    def from_bytes(data_bytes: bytes) -> Self | None:
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