"""System-stats-based encryption for storage layer (onion encryption)."""

import base64
import hashlib
import platform

import psutil

from cryptography.fernet import Fernet


def get_system_stats() -> str:
    """Get stable system stats for key derivation.

    Collects system information that is unlikely to change over 90 minutes:
    - Total memory (not free/used)
    - Physical CPU count (more stable than logical)
    - CPU name/brand (with fallback)
    - Platform info

    Returns:
        Concatenated string of system stats
    """
    stats_parts = []
    stats_parts.append(str(psutil.virtual_memory().total))
    physical_cpus = psutil.cpu_count(logical=False)
    stats_parts.append(str(physical_cpus if physical_cpus else psutil.cpu_count(logical=True)))
    processor = platform.processor()
    stats_parts.append(processor if processor else platform.machine())
    stats_parts.append(platform.machine())
    stats_parts.append(platform.system())
    return "|".join(stats_parts)


def derive_system_key(iterations: int = 12) -> bytes:
    """Derive a Fernet key from system stats using multiple hash iterations.

    Args:
        iterations: Number of SHA-256 iterations for key derivation (default 12)

    Returns:
        A valid Fernet key derived from system stats
    """
    system_data = get_system_stats().encode()
    digest = system_data
    for _ in range(iterations):
        digest = hashlib.sha256(digest).digest()
    return base64.urlsafe_b64encode(digest)


class SystemCrypto:
    """Handles system-stats-based encryption for storage layer."""

    def __init__(self, iterations: int = 12) -> None:
        """Initialize with key derived from system stats.

        Args:
            iterations: Number of hash iterations for key derivation
        """
        self.key = derive_system_key(iterations)
        self.fernet = Fernet(self.key)

    def encrypt(self, data: bytes) -> bytes:
        """Encrypt data using system-derived key.

        Args:
            data: Raw bytes to encrypt

        Returns:
            Encrypted bytes
        """
        return self.fernet.encrypt(data)

    def decrypt(self, encrypted_data: bytes) -> bytes:
        """Decrypt data using system-derived key.

        Args:
            encrypted_data: Encrypted bytes

        Returns:
            Decrypted bytes
        """
        return self.fernet.decrypt(encrypted_data)
