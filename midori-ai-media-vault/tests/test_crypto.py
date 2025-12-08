"""Tests for encryption and decryption."""

import pytest

from midori_ai_media_vault import MediaCrypto


class TestMediaCrypto:
    """Tests for MediaCrypto class."""

    def test_generate_key_returns_bytes(self) -> None:
        key = MediaCrypto.generate_key()
        assert isinstance(key, bytes)
        assert len(key) > 0

    def test_generate_key_unique(self) -> None:
        key1 = MediaCrypto.generate_key()
        key2 = MediaCrypto.generate_key()
        assert key1 != key2

    def test_encrypt_returns_tuple(self) -> None:
        data = b"test data"
        result = MediaCrypto.encrypt(data)
        assert isinstance(result, tuple)
        assert len(result) == 3
        encrypted, key, hash_str = result
        assert isinstance(encrypted, bytes)
        assert isinstance(key, bytes)
        assert isinstance(hash_str, str)

    def test_encrypt_changes_data(self) -> None:
        data = b"original content"
        encrypted, _, _ = MediaCrypto.encrypt(data)
        assert encrypted != data

    def test_encrypt_produces_unique_keys(self) -> None:
        data = b"same data"
        _, key1, _ = MediaCrypto.encrypt(data)
        _, key2, _ = MediaCrypto.encrypt(data)
        assert key1 != key2

    def test_encrypt_hash_is_sha256(self) -> None:
        data = b"test data"
        _, _, hash_str = MediaCrypto.encrypt(data)
        assert len(hash_str) == 64

    def test_decrypt_recovers_data(self) -> None:
        data = b"secret message"
        encrypted, key, hash_str = MediaCrypto.encrypt(data)
        decrypted = MediaCrypto.decrypt(encrypted, key, hash_str)
        assert decrypted == data

    def test_decrypt_with_wrong_key_fails(self) -> None:
        data = b"secret"
        encrypted, _, hash_str = MediaCrypto.encrypt(data)
        wrong_key = MediaCrypto.generate_key()
        with pytest.raises(Exception):
            MediaCrypto.decrypt(encrypted, wrong_key, hash_str)

    def test_decrypt_with_wrong_hash_fails(self) -> None:
        data = b"content"
        encrypted, key, _ = MediaCrypto.encrypt(data)
        wrong_hash = "0" * 64
        with pytest.raises(ValueError, match="integrity"):
            MediaCrypto.decrypt(encrypted, key, wrong_hash)

    def test_roundtrip_various_sizes(self) -> None:
        sizes = [0, 1, 100, 1000, 10000]
        for size in sizes:
            data = bytes(range(256)) * (size // 256 + 1)
            data = data[:size]
            encrypted, key, hash_str = MediaCrypto.encrypt(data)
            decrypted = MediaCrypto.decrypt(encrypted, key, hash_str)
            assert decrypted == data

    def test_roundtrip_empty_data(self) -> None:
        data = b""
        encrypted, key, hash_str = MediaCrypto.encrypt(data)
        decrypted = MediaCrypto.decrypt(encrypted, key, hash_str)
        assert decrypted == data

    def test_roundtrip_binary_data(self) -> None:
        data = bytes(range(256))
        encrypted, key, hash_str = MediaCrypto.encrypt(data)
        decrypted = MediaCrypto.decrypt(encrypted, key, hash_str)
        assert decrypted == data
