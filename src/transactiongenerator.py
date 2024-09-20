class TransactionGenerator:
    """
    Class that generates transactions.
    """

    def __init__(self) -> None:
        """
        Constructor.
        """
        self.queue = Queue(maxsize=10)
        self.transaction_size = int(os.environ.get("TRANSACTION_SIZE")) if os.environ.get("TRANSACTION_SIZE") else 256
        self.transaction_number = int(os.environ.get("TRANSACTION_NUMBER")) if os.environ.get("TRANSACTION_NUMBER") else 100
        self.process = Process(target=self.generate_transactions, args=(self.queue, self.transaction_size, self.transaction_number))
        self.process.start()
