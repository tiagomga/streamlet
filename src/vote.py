class Vote:
    """
    Class that represents a vote.
    """

    def __init__(self, voter: int, epoch: int, message_hash: str, ui: UI) -> None:
        self.voter = voter
        self.epoch = epoch
        self.message_hash = message_hash
        self.ui = ui
