import random
from typing import NoReturn
from multiprocessing import Process, Queue

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


    def generate_transactions(self, queue: Queue, transaction_size: int, transaction_number: int) -> NoReturn:
        """
        Generate transactions.

        Args:
            queue (Queue): queue for transactions
            transaction_size (int): transaction's size
            transaction_number (int): number of transactions
        """
        last_transaction = 0
        while True:
            transactions = [(last_transaction+i, random.randint(0, 100), "\x00"*transaction_size) for i in range(transaction_number)]
            last_transaction += transaction_number
            queue.put(transactions)