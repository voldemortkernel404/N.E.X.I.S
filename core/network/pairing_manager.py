"""
N.E.X.I.S. Network
Pairing Manager

Connects:
- Device identity
- Pairing verification
- Trusted devices

A device becomes trusted only after successful
cryptographic verification.
"""

from core.network.pairing import (
    create_pairing_challenge,
    verify_pairing_code,
    sign_challenge,
    verify_signature,
)

from core.network.trusted_devices import (
    add_trusted_device,
    is_trusted_device,
    get_trusted_device,
    remove_trusted_device,
)


# ============================================================
# CREATE PAIRING SESSION
# ============================================================

def start_pairing(device_id):
    """
    Create a temporary pairing session for a device.
    """

    return create_pairing_challenge(device_id)


# ============================================================
# VERIFY PAIRING
# ============================================================

def verify_pairing(
    challenge,
    supplied_code,
    device_id,
    device_name,
    device_type,
    public_key,
    signature,
):
    """
    Verify a device and add it to the trusted-device store.
    """

    # --------------------------------------------------------
    # Verify pairing code
    # --------------------------------------------------------

    if not verify_pairing_code(
        challenge,
        supplied_code,
    ):
        return {
            "success": False,
            "reason": "Invalid or expired pairing code.",
        }

    # --------------------------------------------------------
    # Make sure the challenge belongs to this device
    # --------------------------------------------------------

    if challenge.get("device_id") != device_id:
        return {
            "success": False,
            "reason": "Device ID does not match pairing challenge.",
        }

    # --------------------------------------------------------
    # Verify cryptographic signature
    # --------------------------------------------------------

    if not verify_signature(
        public_key,
        challenge,
        signature,
    ):
        return {
            "success": False,
            "reason": "Cryptographic signature verification failed.",
        }

    # --------------------------------------------------------
    # Store trusted device
    # --------------------------------------------------------

    add_trusted_device(
        device_id=device_id,
        device_name=device_name,
        device_type=device_type,
        public_key=public_key,
    )

    return {
        "success": True,
        "device_id": device_id,
        "device_name": device_name,
        "device_type": device_type,
    }


# ============================================================
# TRUST CHECK
# ============================================================

def check_device(device_id):
    """
    Check whether a device is trusted.
    """

    if not is_trusted_device(device_id):
        return {
            "trusted": False,
            "device": None,
        }

    return {
        "trusted": True,
        "device": get_trusted_device(device_id),
    }


# ============================================================
# UNPAIR DEVICE
# ============================================================

def unpair_device(device_id):
    """
    Remove a device from the trusted list.
    """

    removed = remove_trusted_device(
        device_id
    )

    return {
        "success": removed
    }


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("NEXIS PAIRING MANAGER TEST")
    print("=" * 60)

    # --------------------------------------------------------
    # Create a simulated phone identity
    # --------------------------------------------------------

    from cryptography.hazmat.primitives.asymmetric.ed25519 import (
        Ed25519PrivateKey,
    )

    from cryptography.hazmat.primitives import serialization

    phone_private = Ed25519PrivateKey.generate()
    phone_public = phone_private.public_key()

    phone_private_hex = phone_private.private_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PrivateFormat.Raw,
        encryption_algorithm=serialization.NoEncryption(),
    ).hex()

    phone_public_hex = phone_public.public_bytes(
        encoding=serialization.Encoding.Raw,
        format=serialization.PublicFormat.Raw,
    ).hex()

    phone_id = "NEXIS-PHONE-TEST"

    # --------------------------------------------------------
    # Create pairing challenge
    # --------------------------------------------------------

    challenge = start_pairing(
        phone_id
    )

    print("\nPAIRING CODE:")
    print(challenge["code"])

    # --------------------------------------------------------
    # Phone signs the challenge
    # --------------------------------------------------------

    signature = sign_challenge(
        phone_private_hex,
        challenge,
    )

    # --------------------------------------------------------
    # Verify and trust device
    # --------------------------------------------------------

    result = verify_pairing(
        challenge=challenge,
        supplied_code=challenge["code"],
        device_id=phone_id,
        device_name="NEXIS-PHONE",
        device_type="phone",
        public_key=phone_public_hex,
        signature=signature,
    )

    print("\nPAIRING RESULT:")
    print(result)

    # --------------------------------------------------------
    # Check trust
    # --------------------------------------------------------

    trust = check_device(
        phone_id
    )

    print("\nTRUST CHECK:")
    print(trust)

    # --------------------------------------------------------
    # Remove device
    # --------------------------------------------------------

    removed = unpair_device(
        phone_id
    )

    print("\nUNPAIR RESULT:")
    print(removed)

    print("\nPAIRING MANAGER TEST COMPLETE")