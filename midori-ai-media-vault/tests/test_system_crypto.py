"""Tests for system-stats-based encryption."""

from midori_ai_media_vault import SystemCrypto
from midori_ai_media_vault import derive_system_key
from midori_ai_media_vault import get_system_stats


class TestGetSystemStats:
    """Tests for get_system_stats function."""

    def test_returns_string(self) -> None:
        stats = get_system_stats()
        assert isinstance(stats, str)

    def test_contains_multiple_parts(self) -> None:
        stats = get_system_stats()
        parts = stats.split("|")
        assert len(parts) >= 5

    def test_is_deterministic(self) -> None:
        stats1 = get_system_stats()
        stats2 = get_system_stats()
        assert stats1 == stats2


class TestDeriveSystemKey:
    """Tests for derive_system_key function."""

    def test_returns_bytes(self) -> None:
        key = derive_system_key()
        assert isinstance(key, bytes)

    def test_key_length_valid_for_fernet(self) -> None:
        key = derive_system_key()
        assert len(key) == 44

    def test_is_deterministic(self) -> None:
        key1 = derive_system_key()
        key2 = derive_system_key()
        assert key1 == key2

    def test_different_iterations_produce_different_keys(self) -> None:
        key1 = derive_system_key(iterations=12)
        key2 = derive_system_key(iterations=13)
        assert key1 != key2

    def test_custom_iterations(self) -> None:
        key = derive_system_key(iterations=5)
        assert isinstance(key, bytes)
        assert len(key) == 44


class TestSystemCrypto:
    """Tests for SystemCrypto class."""

    def test_encrypt_returns_bytes(self) -> None:
        crypto = SystemCrypto()
        encrypted = crypto.encrypt(b"test data")
        assert isinstance(encrypted, bytes)

    def test_encrypt_changes_data(self) -> None:
        crypto = SystemCrypto()
        data = b"original content"
        encrypted = crypto.encrypt(data)
        assert encrypted != data

    def test_decrypt_recovers_data(self) -> None:
        crypto = SystemCrypto()
        data = b"secret message"
        encrypted = crypto.encrypt(data)
        decrypted = crypto.decrypt(encrypted)
        assert decrypted == data

    def test_roundtrip_various_sizes(self) -> None:
        crypto = SystemCrypto()
        sizes = [0, 1, 100, 1000, 10000]
        for size in sizes:
            data = bytes(range(256)) * (size // 256 + 1)
            data = data[:size]
            encrypted = crypto.encrypt(data)
            decrypted = crypto.decrypt(encrypted)
            assert decrypted == data

    def test_roundtrip_empty_data(self) -> None:
        crypto = SystemCrypto()
        data = b""
        encrypted = crypto.encrypt(data)
        decrypted = crypto.decrypt(encrypted)
        assert decrypted == data

    def test_roundtrip_binary_data(self) -> None:
        crypto = SystemCrypto()
        data = bytes(range(256))
        encrypted = crypto.encrypt(data)
        decrypted = crypto.decrypt(encrypted)
        assert decrypted == data

    def test_same_system_can_decrypt(self) -> None:
        crypto1 = SystemCrypto()
        crypto2 = SystemCrypto()
        data = b"cross-instance test"
        encrypted = crypto1.encrypt(data)
        decrypted = crypto2.decrypt(encrypted)
        assert decrypted == data

    def test_custom_iterations(self) -> None:
        crypto = SystemCrypto(iterations=5)
        data = b"test with custom iterations"
        encrypted = crypto.encrypt(data)
        crypto2 = SystemCrypto(iterations=5)
        decrypted = crypto2.decrypt(encrypted)
        assert decrypted == data
