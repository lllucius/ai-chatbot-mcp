"Utility functions for security operations."

import base64
import hashlib
import secrets
import string

SCRYPT_N = 2**14
SCRYPT_R = 8
SCRYPT_P = 1
SCRYPT_DKLEN = 64


def get_password_hash(password: str) -> str:
    "Get password hash data."
    salt = secrets.token_bytes(16)
    key = hashlib.scrypt(
        password=password.encode("utf-8"),
        salt=salt,
        n=SCRYPT_N,
        r=SCRYPT_R,
        p=SCRYPT_P,
        dklen=SCRYPT_DKLEN,
    )
    data = base64.b64encode((salt + key)).decode("utf-8")
    return data


def verify_password(plain_password: str, hashed_password: str) -> bool:
    "Verify Password operation."
    try:
        decoded = base64.b64decode(hashed_password.encode("utf-8"))
        salt = decoded[:16]
        key = decoded[16:]
        new_key = hashlib.scrypt(
            password=plain_password.encode("utf-8"),
            salt=salt,
            n=SCRYPT_N,
            r=SCRYPT_R,
            p=SCRYPT_P,
            dklen=len(key),
        )
        return secrets.compare_digest(new_key, key)
    except Exception:
        return False


def generate_random_password(length: int = 12) -> str:
    "Generate Random Password operation."
    alphabet = (string.ascii_letters + string.digits) + "!@#$%^&*"
    password = "".join((secrets.choice(alphabet) for _ in range(length)))
    return password


def generate_secret_key(length: int = 32) -> str:
    "Generate Secret Key operation."
    return secrets.token_hex(length)


def generate_token(length: int = 32) -> str:
    "Generate Token operation."
    return secrets.token_urlsafe(length)
