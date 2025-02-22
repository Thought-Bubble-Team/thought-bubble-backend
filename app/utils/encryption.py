from cryptography.fernet import Fernet
from decouple import config

# Load encryption key from environment variables
ENCRYPTION_KEY = config("ENCRYPTION_KEY")
cipher = Fernet(ENCRYPTION_KEY.encode())  # Ensure key is bytes

def encrypt_text(plain_text: str) -> str:
    """Encrypts a journal entry before storing it in the database."""
    encrypted_text = cipher.encrypt(plain_text.encode()).decode()
    return encrypted_text

def decrypt_text(encrypted_text: str) -> str:
    """Decrypts a journal entry when retrieved by the user."""
    decrypted_text = cipher.decrypt(encrypted_text.encode()).decode()
    return decrypted_text
