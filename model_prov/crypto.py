"""Cryptographic signing and verification using Ed25519."""

from __future__ import annotations

import base64
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey
from cryptography.hazmat.primitives import serialization


def generate_keypair(key_dir: Path) -> tuple[Path, Path]:
    """Generate Ed25519 keypair, return (private_path, public_path)."""
    key_dir.mkdir(parents=True, exist_ok=True)
    private_key = Ed25519PrivateKey.generate()
    public_key = private_key.public_key()

    priv_path = key_dir / "signing_key.pem"
    pub_path = key_dir / "signing_key.pub.pem"

    priv_path.write_bytes(
        private_key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
    )
    pub_path.write_bytes(
        public_key.public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    priv_path.chmod(0o600)
    return priv_path, pub_path


def load_private_key(path: Path) -> Ed25519PrivateKey:
    return serialization.load_pem_private_key(path.read_bytes(), password=None)  # type: ignore


def load_public_key(path: Path) -> Ed25519PublicKey:
    return serialization.load_pem_public_key(path.read_bytes())  # type: ignore


def sign(data: bytes, private_key: Ed25519PrivateKey) -> str:
    """Sign data, return base64-encoded signature."""
    sig = private_key.sign(data)
    return base64.b64encode(sig).decode()


def verify(data: bytes, signature_b64: str, public_key: Ed25519PublicKey) -> bool:
    """Verify signature. Returns True if valid, False otherwise."""
    try:
        sig = base64.b64decode(signature_b64)
        public_key.verify(sig, data)
        return True
    except Exception:
        return False
