"""Per-file encryption with random keys stored in the MediaObject."""

import hashlib

from cryptography.fernet import Fernet


class MediaCrypto:
    """Handles per-file encryption with random keys stored in the MediaObject."""

    @staticmethod
    def generate_key() -> bytes:
        """Generate a new random Fernet key for a media file."""
        return Fernet.generate_key()

    @staticmethod
    def encrypt(data: bytes) -> tuple[bytes, bytes, str]:
        """Encrypt data with a new random key.

        Returns:
            Tuple of (encrypted_bytes, encryption_key, content_integrity_hash)
        """
        key = MediaCrypto.generate_key()
        fernet = Fernet(key)
        encrypted = fernet.encrypt(data)
        integrity_hash = hashlib.sha256(data).hexdigest()
        return encrypted, key, integrity_hash

    @staticmethod
    def decrypt(encrypted_data: bytes, key: bytes, expected_hash: str) -> bytes:
        """Decrypt data using the stored key and verify integrity.

        Args:
            encrypted_data: The encrypted bytes from MediaObject
            key: The encryption_key from MediaObject
            expected_hash: The content_integrity_hash from MediaObject

        Returns:
            Decrypted bytes after integrity verification

        Raises:
            ValueError: If integrity hash doesn't match
        """
        fernet = Fernet(key)
        decrypted = fernet.decrypt(encrypted_data)
        actual_hash = hashlib.sha256(decrypted).hexdigest()
        if actual_hash != expected_hash:
            raise ValueError("Content integrity check failed - data may be corrupted")
        return decrypted
