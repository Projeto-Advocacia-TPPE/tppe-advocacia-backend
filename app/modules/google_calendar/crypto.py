from cryptography.fernet import Fernet


class TokenCipher:
    """Criptografia simétrica (Fernet) para o refresh_token do Google.

    A chave vem de `GOOGLE_TOKEN_ENCRYPTION_KEY` (env). Gere uma com:
        python -c "from cryptography.fernet import Fernet; \
print(Fernet.generate_key().decode())"
    """

    def __init__(self, key: str) -> None:
        self._fernet = Fernet(key.encode())

    def encrypt(self, plaintext: str) -> str:
        return self._fernet.encrypt(plaintext.encode()).decode()

    def decrypt(self, ciphertext: str) -> str:
        return self._fernet.decrypt(ciphertext.encode()).decode()
