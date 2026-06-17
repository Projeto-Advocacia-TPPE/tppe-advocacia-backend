from cryptography.fernet import Fernet

from app.modules.google_calendar.crypto import TokenCipher


def _cipher() -> TokenCipher:
    return TokenCipher(Fernet.generate_key().decode())


def test_encrypt_decrypt_roundtrip():
    cipher = _cipher()
    token = "1//0refresh-token-value"
    assert cipher.decrypt(cipher.encrypt(token)) == token


def test_ciphertext_is_not_plaintext():
    cipher = _cipher()
    encrypted = cipher.encrypt("secret-token")
    assert encrypted != "secret-token"


def test_keys_are_not_interchangeable():
    encrypted = _cipher().encrypt("token")
    other = _cipher()
    try:
        other.decrypt(encrypted)
        raised = False
    except Exception:
        raised = True
    assert raised
