"""
N.E.X.I.S. Network
Device Pairing

Creates and verifies a pairing challenge between NEXIS devices.
Private keys never leave the device.
"""

import secrets
import time

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)


# ============================================================
# CONFIGURATION
# ============================================================

PAIRING_CODE_LENGTH = 6
PAIRING_CODE_EXPIRY = 300  # 5 minutes


# ============================================================
# LOAD PRIVATE KEY
# ============================================================

def load_private_key(private_key_hex):
    """
    Reconstruct an Ed25519 private key from stored hexadecimal data.
    """

    return Ed25519PrivateKey.from_private_bytes(
        bytes.fromhex(private_key_hex)
    )


# ============================================================
# LOAD PUBLIC KEY
# ============================================================

def load_public_key(public_key_hex):
    """
    Reconstruct an Ed25519 public key.
    """

    return Ed25519PublicKey.from_public_bytes(
        bytes.fromhex(public_key_hex)
    )


# ============================================================
# PAIRING CODE
# ============================================================

def generate_pairing_code():
    """
    Generate a random six-digit pairing code.
    """

    return f"{secrets.randbelow(1_000_000):06d}"


# ============================================================
# CHALLENGE
# ============================================================

def create_pairing_challenge(device_id):
    """
    Create a temporary pairing challenge.
    """

    code = generate_pairing_code()

    return {
        "device_id": device_id,
        "code": code,
        "created_at": time.time(),
        "expires_at": time.time() + PAIRING_CODE_EXPIRY,
    }


# ============================================================
# CHALLENGE VALIDATION
# ============================================================

def verify_pairing_code(
    challenge,
    supplied_code,
):
    """
    Verify that a pairing code is correct and has not expired.
    """

    if not challenge:
        return False

    if time.time() > challenge["expires_at"]:
        return False

    return secrets.compare_digest(
        challenge["code"],
        str(supplied_code),
    )


# ============================================================
# SIGN CHALLENGE
# ============================================================

def sign_challenge(
    private_key_hex,
    challenge,
):
    """
    Sign a pairing challenge using the device's private key.
    """

    private_key = load_private_key(
        private_key_hex
    )

    challenge_data = (
        f"{challenge['device_id']}:"
        f"{challenge['code']}:"
        f"{challenge['created_at']}"
    ).encode("utf-8")

    signature = private_key.sign(
        challenge_data
    )

    return signature.hex()


# ============================================================
# VERIFY SIGNATURE
# ============================================================

def verify_signature(
    public_key_hex,
    challenge,
    signature_hex,
):
    """
    Verify a pairing signature using the device's public key.
    """

    public_key = load_public_key(
        public_key_hex
    )

    challenge_data = (
        f"{challenge['device_id']}:"
        f"{challenge['code']}:"
        f"{challenge['created_at']}"
    ).encode("utf-8")

    try:
        public_key.verify(
            bytes.fromhex(signature_hex),
            challenge_data,
        )

        return True

    except Exception:
        return False


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("NEXIS PAIRING TEST")
    print("=" * 60)

    # Create two test identities.
    device_a_private = Ed25519PrivateKey.generate()
    device_a_public = device_a_private.public_key()

    device_b_private = Ed25519PrivateKey.generate()
    device_b_public = device_b_private.public_key()

    device_a_private_hex = (
        device_a_private.private_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PrivateFormat.Raw,
            encryption_algorithm=serialization.NoEncryption(),
        ).hex()
    )

    device_a_public_hex = (
        device_a_public.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        ).hex()
    )

    device_b_public_hex = (
        device_b_public.public_bytes(
            encoding=serialization.Encoding.Raw,
            format=serialization.PublicFormat.Raw,
        ).hex()
    )

    # Device A creates a pairing challenge.
    challenge = create_pairing_challenge(
        "NEXIS-PC"
    )

    print("\nPAIRING CODE:")
    print(challenge["code"])

    # Device A signs the challenge.
    signature = sign_challenge(
        device_a_private_hex,
        challenge,
    )

    print("\nSIGNATURE GENERATED: YES")

    # Verify using Device A's public key.
    valid = verify_signature(
        device_a_public_hex,
        challenge,
        signature,
    )

    print("VALID SIGNATURE:", valid)

    # Make sure another public key cannot verify it.
    invalid = verify_signature(
        device_b_public_hex,
        challenge,
        signature,
    )

    print("WRONG KEY ACCEPTED:", invalid)

    print("\nPAIRING TEST COMPLETE")