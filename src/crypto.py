# Cryptographic functions based on the package's documentation (version 42.0.8) (https://cryptography.io/en/42.0.8/)
from cryptography.hazmat.primitives.asymmetric import rsa, padding, utils
from cryptography.hazmat.primitives import hashes, serialization

def generate_keys(key_size: int = 2048) -> tuple[rsa.RSAPublicKey, rsa.RSAPrivateKey]:
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=key_size
    )
    public_key = private_key.public_key()
    return (public_key, private_key)


def compute_hash(content: bytes) -> str:
    hasher = hashes.Hash(hashes.SHA256())
    hasher.update(content)
    digest = hasher.finalize()
    return digest.hex()


def sign(content: bytes, private_key: rsa.RSAPrivateKey) -> str:
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
    pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    return pem