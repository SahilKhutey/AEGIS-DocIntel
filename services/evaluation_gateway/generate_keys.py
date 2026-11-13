"""
Key Generation Utility for AEGIS-DocIntel Evaluation Gateway
Generates Ed25519 Root Private Key and Public Key for Evaluation License Signing.
"""

from pathlib import Path
from cryptography.hazmat.primitives.asymmetric import ed25519
from cryptography.hazmat.primitives import serialization

KEYS_DIR = Path(__file__).resolve().parent / "keys"

def generate_keypair(output_dir: Path = KEYS_DIR) -> tuple[Path, Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    private_key_path = output_dir / "private-key.pem"
    public_key_path = output_dir / "public-key.pem"

    private_key = ed25519.Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    # Serialize private key (server-side only, proprietary)
    priv_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    private_key_path.write_bytes(priv_bytes)

    # Serialize public key (bundled with demo distribution)
    pub_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    public_key_path.write_bytes(pub_bytes)

    return private_key_path, public_key_path

if __name__ == "__main__":
    priv, pub = generate_keypair()
    print(f"Generated Ed25519 Keypair:")
    print(f"  Private Key: {priv}")
    print(f"  Public Key:  {pub}")
