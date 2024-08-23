class USIG:
    """
    Unique Sequential Identifier Generator (USIG) is a component that
    generates unique identifiers (UI) that are unique, sequential and
    monotonic.
    """

    def __init__(self) -> None:
        self.counter = 0
        self.public_key, self.private_key = crypto.generate_keys()
