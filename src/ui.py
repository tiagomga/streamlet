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
