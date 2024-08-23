class UI:
    """
    Class that represents a Unique Identifier (UI).
    """

    def __init__(self, sequence_number: int, signature: str) -> None:
        self.sequence_number = sequence_number
        self.signature = signature


    def get_sequence_number(self) -> int:
        return self.sequence_number
