"""
Cryptographic utilities for secure data handling.
"""

import base64
import hashlib
import os
from typing import Union, Optional
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


def generate_key(password: str, salt: Optional[bytes] = None) -> bytes:
    """Generate encryption key from password."""
    if salt is None:
        salt = os.urandom(16)
    
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
    return key


def encrypt_data(data: Union[str, bytes], password: str) -> str:
    """Encrypt data with password."""
    if isinstance(data, str):
        data = data.encode('utf-8')
    
    salt = os.urandom(16)
    key = generate_key(password, salt)
    f = Fernet(key)
    
    encrypted_data = f.encrypt(data)
    
    # Combine salt and encrypted data
    combined = salt + encrypted_data
    return base64.urlsafe_b64encode(combined).decode()


def decrypt_data(encrypted_data: str, password: str) -> str:
    """Decrypt data with password."""
    try:
        combined = base64.urlsafe_b64decode(encrypted_data.encode())
        salt = combined[:16]
        encrypted_data = combined[16:]
        
        key = generate_key(password, salt)
        f = Fernet(key)
        
        decrypted_data = f.decrypt(encrypted_data)
        return decrypted_data.decode('utf-8')
    
    except Exception as e:
        raise ValueError(f"Decryption failed: {e}")


def hash_password(password: str) -> str:
    """Hash password for storage."""
    salt = os.urandom(32)
    pwdhash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return base64.urlsafe_b64encode(salt + pwdhash).decode('ascii')


def verify_password(stored_password: str, provided_password: str) -> bool:
    """Verify password against stored hash."""
    try:
        pwdhash = base64.urlsafe_b64decode(stored_password.encode('ascii'))
        salt = pwdhash[:32]
        stored_hash = pwdhash[32:]
        pwdhash = hashlib.pbkdf2_hmac('sha256', provided_password.encode('utf-8'), salt, 100000)
        return pwdhash == stored_hash
    except Exception:
        return False
