class USIG:
    """
    Unique Sequential Identifier Generator (USIG) is a component that
    generates unique identifiers (UI) that are unique, sequential and
    monotonic.
    """

    def __init__(self) -> None:
        self.counter = 0
        self.public_key, self.private_key = crypto.generate_keys()


    def create_ui(self, message: Message) -> UI:
        self.counter += 1
        signature_content = pickle.dumps((message.to_bytes(), self.counter))
        signature = crypto.sign(signature_content, self.private_key)
        return UI(self.counter, signature)


    def verify_ui(self, ui: UI, public_key: RSAPublicKey, message: Message) -> bool:
        content = pickle.dumps((message.to_bytes(), ui.get_sequence_number()))
        content_hash = crypto.calculate_hash(content)
        return crypto.verify_signature(ui.get_signature(), content_hash, public_key)
