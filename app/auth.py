"""Credenciales y comprobaciones para el único negocio del MVP."""

import base64
import binascii
import hashlib
import hmac
import os
import secrets
import sys


ITERATIONS = 600_000


def make_password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, ITERATIONS)
    return "$".join((
        "pbkdf2_sha256",
        str(ITERATIONS),
        base64.urlsafe_b64encode(salt).decode(),
        base64.urlsafe_b64encode(digest).decode(),
    ))


def verify_password(password: str, stored: str) -> bool:
    try:
        algorithm, iterations, salt, expected = stored.split("$")
        if algorithm != "pbkdf2_sha256" or not 100_000 <= int(iterations) <= 2_000_000:
            return False
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), base64.urlsafe_b64decode(salt), int(iterations)
        )
        return hmac.compare_digest(actual, base64.urlsafe_b64decode(expected))
    except (ValueError, TypeError, binascii.Error):
        return False


def admin_is_configured() -> bool:
    return all(os.getenv(name) for name in ("ADMIN_USERNAME", "ADMIN_PASSWORD_HASH", "SESSION_SECRET"))


def valid_credentials(username: str, password: str) -> bool:
    configured_name = os.getenv("ADMIN_USERNAME", "")
    configured_hash = os.getenv("ADMIN_PASSWORD_HASH", "")
    return hmac.compare_digest(username, configured_name) and verify_password(password, configured_hash)


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("hash-password", "session-secret"):
        raise SystemExit("Uso: python -m app.auth [hash-password|session-secret]")
    if sys.argv[1] == "session-secret":
        print(secrets.token_urlsafe(48))
    else:
        import getpass

        print(make_password_hash(getpass.getpass("Contraseña del negocio: ")))
