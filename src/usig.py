class USIG:
    """
    Unique Sequential Identifier Generator (USIG) is a component that
    generates unique identifiers (UI) that are unique, sequential and
    monotonic.
    """

    def __init__(self) -> None:
        """
        Constructor.
        """
        self.counter = 0
        self.public_key, self.private_key = crypto.generate_keys()


    def create_ui(self, message: Message) -> UI:
        """
        Create unique identifier (UI) for `message`.

        Args:
            message (Message): message

        Returns:
            UI: unique identifier that binds a counter value to a message
        """
        self.counter += 1
        signature_content = pickle.dumps((message.to_bytes(), self.counter))
        signature = crypto.sign(signature_content, self.private_key)
        return UI(self.counter, signature)


    def verify_ui(self, ui: UI, public_key: RSAPublicKey, message: Message) -> bool:
        """
        Verify `message`'s unique identifier `ui` (UI) using `public_key`.

        Args:
            ui (UI): unique identifier
            public_key (RSAPublicKey): public key
            message (Message): message

        Returns:
            bool: True, if and only if the unique identifier is valid, else return False
        """
        content = pickle.dumps((message.to_bytes(), ui.get_sequence_number()))
        content_hash = crypto.calculate_hash(content)
        return crypto.verify_signature(ui.get_signature(), content_hash, public_key)


    def get_public_key(self) -> RSAPublicKey:
        """
        Get public key.

        Returns:
            RSAPublicKey: public key
        """
        return self.public_key