# Cryptographic functions based on the package's documentation (version 42.0.8) (https://cryptography.io/en/42.0.8/)
from cryptography.hazmat.primitives.asymmetric import rsa, padding, utils
from cryptography.hazmat.primitives import hashes, serialization

def generate_keys(key_size: int = 2048) -> tuple[rsa.RSAPublicKey, rsa.RSAPrivateKey]:
    """
    Generate pair of asymmetric keys.

    Args:
        key_size (int, optional): size of the key

    Returns:
        tuple[rsa.RSAPublicKey, rsa.RSAPrivateKey]: public and private keys
    """
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size
    )
    public_key = private_key.public_key()
    return (public_key, private_key)


def compute_hash(content: bytes) -> str:
    """
    Calculate hash of `content`.

    Args:
        content (bytes): content to be hashed

    Returns:
        str: hash
    """
    hasher = hashes.Hash(hashes.SHA256())
    hasher.update(content)
    digest = hasher.finalize()
    return digest.hex()


def sign(content: bytes, private_key: rsa.RSAPrivateKey) -> str:
    """
    Sign `content`.

    Args:
        content (bytes): content to be signed
        private_key (rsa.RSAPrivateKey): private key

    Returns:
        str: signature
    """
    signature = private_key.sign(
        content,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature.hex()


def sign_hash(digest: str, private_key: rsa.RSAPrivateKey) -> str:
    """
    Sign pre-hashed content.

    Args:
        digest (str): hash of the content
        private_key (rsa.RSAPrivateKey): private key

    Returns:
        str: signature
    """
    signature = private_key.sign(
        bytes.fromhex(digest),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        utils.Prehashed(hashes.SHA256())
    )
    return signature.hex()


def verify_signature(signature: str, digest: str, public_key: rsa.RSAPublicKey) -> bool:
    """
    Verify if `signature` is valid, using `digest` and `public_key`.

    Args:
        signature (str): signature of the content
        digest (str): digest of the content
        public_key (rsa.RSAPublicKey): public key

    Returns:
        bool: True, if the signature is valid, else return False 
    """
    try:
        public_key.verify(
            bytes.fromhex(signature),
            bytes.fromhex(digest),
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            utils.Prehashed(hashes.SHA256())
        )
        return True
    except:
        return False


def serialize_public_key(public_key: rsa.RSAPublicKey) -> bytes:
    """
    Serialize `public_key`.

    Args:
        public_key (rsa.RSAPublicKey): public key

    Returns:
        bytes: serialized public key
    """
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem