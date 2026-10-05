"""
N.E.X.I.S. Network
Device Identity

Each NEXIS installation gets:
- A unique device ID
- A device name
- A device type
- An Ed25519 public/private key pair

The private key NEVER leaves the device.
"""

import json
import uuid
from pathlib import Path

from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
)
from cryptography.hazmat.primitives import serialization


# ============================================================
# CONFIGURATION
# ============================================================

NETWORK_DIR = Path(__file__).resolve().parent

IDENTITY_FILE = NETWORK_DIR / "device_identity.json"


# ============================================================
# DEVICE IDENTITY
# ============================================================

def create_identity(
    device_name="NEXIS-PC",
    device_type="pc",
):
    """
    Create a new NEXIS device identity.
    """

    private_key = Ed25519PrivateKey.generate()

    public_key = private_key.public_key()

    private_key_bytes = private_key.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    )

    public_key_bytes = public_key.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    )

    identity = {
        "device_id": str(uuid.uuid4()),
        "device_name": device_name,
        "device_type": device_type,
        "public_key": public_key_bytes.hex(),
        "private_key": private_key_bytes.hex(),
    }

    IDENTITY_FILE.write_text(
        json.dumps(identity, indent=4),
        encoding="utf-8",
    )

    return identity


# ============================================================
# LOAD IDENTITY
# ============================================================

def load_identity():
    """
    Load the existing NEXIS device identity.

    If none exists, create one.
    """

    if not IDENTITY_FILE.exists():
        return create_identity()

    return json.loads(
        IDENTITY_FILE.read_text(
            encoding="utf-8"
        )
    )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    identity = load_identity()

    print("=" * 60)
    print("NEXIS DEVICE IDENTITY")
    print("=" * 60)

    print("Device ID:   ", identity["device_id"])
    print("Device Name: ", identity["device_name"])
    print("Device Type: ", identity["device_type"])
    print("Public Key:  ", identity["public_key"])

    print()
    print("Private key generated successfully.")
    print("Private key is stored locally.")