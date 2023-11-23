class Transaction:
    """
    Class that represents a transaction between two parties.
    """

    def __init__(self, sender_id, receiver_id, amount):
        """
        Constructor.

        Args:
            sender_id (int): ID of the sender
            receiver_id (int): ID of the receiver
            amount (int): amount of the transaction
        """
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.amount = amount