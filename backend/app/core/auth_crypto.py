"""
Cryptographic, Hashing, and RFC 6238 TOTP Multi-Factor Authentication Helpers.

Zero external dependencies: uses Python's standard library (hashlib, hmac, secrets, time, struct).
"""
import base64
import hashlib
import hmac
import secrets
import struct
import time
from typing import List, Tuple


def hash_password(password: str) -> str:
    """Hash password using PBKDF2-HMAC-SHA256 with 100,000 rounds and random salt."""
    salt = secrets.token_hex(16)
    key = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 100000)
    return f"pbkdf2_sha256$100000${salt}${key.hex()}"


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password against stored PBKDF2 hash."""
    if not hashed_password or "$" not in hashed_password:
        return False
    try:
        parts = hashed_password.split("$")
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = parts[2]
        expected_hex = parts[3]
        calculated = hashlib.pbkdf2_hmac("sha256", plain_password.encode("utf-8"), salt.encode("utf-8"), iterations)
        return hmac.compare_digest(calculated.hex(), expected_hex)
    except Exception:
        return False


# --- RFC 6238 Time-based One-time Password (TOTP) Helpers ---

def generate_totp_secret() -> str:
    """Generate random Base32 encoded 160-bit TOTP secret."""
    raw = secrets.token_bytes(20)
    return base64.b32encode(raw).decode("utf-8").replace("=", "")


def generate_totp_code(secret_b32: str, time_step: int = 30, for_time: float = None) -> str:
    """Compute 6-digit TOTP code for given base32 secret and timestamp."""
    if for_time is None:
        for_time = time.time()
    
    # Pad base32 secret if needed
    padded_secret = secret_b32.upper()
    padding_needed = (8 - len(padded_secret) % 8) % 8
    padded_secret += "=" * padding_needed
    key = base64.b32decode(padded_secret)

    counter = int(for_time // time_step)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = struct.unpack(">I", digest[offset:offset + 4])[0] & 0x7FFFFFFF
    return f"{code_int % 1000000:06d}"


def verify_totp_code(secret_b32: str, code: str, window: int = 1) -> bool:
    """Validate 6-digit TOTP code allowing ±1 step (30 seconds) clock drift."""
    if not code or not code.isdigit() or len(code) != 6:
        return False
    current_time = time.time()
    for step in range(-window, window + 1):
        test_time = current_time + (step * 30)
        expected = generate_totp_code(secret_b32, for_time=test_time)
        if hmac.compare_digest(expected, code):
            return True
    return False


def generate_totp_uri(secret_b32: str, account_name: str, issuer: str = "Aura Voice AI") -> str:
    """Generate standard otpauth:// URI for authenticator apps."""
    return f"otpauth://totp/{issuer}:{account_name}?secret={secret_b32}&issuer={issuer}&algorithm=SHA1&digits=6&period=30"


def generate_recovery_codes(count: int = 8) -> Tuple[List[str], List[str]]:
    """Generate plaintext recovery codes and their secure SHA-256 hashes."""
    plain_codes = []
    hashed_codes = []
    for _ in range(count):
        code = f"{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}-{secrets.token_hex(2).upper()}"
        plain_codes.append(code)
        hashed_codes.append(hashlib.sha256(code.encode("utf-8")).hexdigest())
    return plain_codes, hashed_codes


def hash_token(token: str) -> str:
    """SHA-256 hash a session or reset token."""
    return hashlib.sha256(token.encode("utf-8")).hexdigest()
