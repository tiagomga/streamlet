import pickle
from cryptography.hazmat.primitives.asymmetric.rsa import RSAPublicKey
import crypto
from ui import UI
from message import Message
from certificate import Certificate

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
        content = [
            message.get_type(),
            message.get_content().to_bytes(),
            message.get_sender(),
            message.get_certificate(),
            self.counter
        ]
        if isinstance(message.get_certificate(), Certificate):
            content[3] = message.get_certificate().to_bytes()
        signature_content = pickle.dumps(content)
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
        content = [
            message.get_type(),
            message.get_content().to_bytes(),
            message.get_sender(),
            message.get_certificate(),
            ui.get_sequence_number()
        ]
        if isinstance(message.get_certificate(), Certificate):
            content[3] = message.get_certificate().to_bytes()
        content = pickle.dumps(content)
        content_hash = crypto.calculate_hash(content)
        return crypto.verify_signature(ui.get_signature(), content_hash, public_key)


    def get_public_key(self) -> RSAPublicKey:
        """
        Get public key.

        Returns:
            RSAPublicKey: public key
        """
        return self.public_key