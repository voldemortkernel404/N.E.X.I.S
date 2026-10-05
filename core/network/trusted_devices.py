"""
N.E.X.I.S. Network
Trusted Device Manager

Stores trusted NEXIS devices and their public keys.
Private keys are NEVER stored here.
"""

import json
from pathlib import Path


# ============================================================
# CONFIGURATION
# ============================================================

NETWORK_DIR = Path(__file__).resolve().parent
TRUSTED_DEVICES_FILE = NETWORK_DIR / "trusted_devices.json"


# ============================================================
# DATABASE
# ============================================================

def _load_devices():
    """Load the trusted-device database."""

    if not TRUSTED_DEVICES_FILE.exists():
        return {}

    try:
        return json.loads(
            TRUSTED_DEVICES_FILE.read_text(
                encoding="utf-8"
            )
        )
    except (json.JSONDecodeError, OSError):
        return {}


def _save_devices(devices):
    """Save the trusted-device database."""

    TRUSTED_DEVICES_FILE.write_text(
        json.dumps(
            devices,
            indent=4
        ),
        encoding="utf-8"
    )


# ============================================================
# ADD DEVICE
# ============================================================

def add_trusted_device(
    device_id,
    device_name,
    device_type,
    public_key,
):
    """
    Add or update a trusted NEXIS device.
    """

    devices = _load_devices()

    devices[device_id] = {
        "device_name": device_name,
        "device_type": device_type,
        "public_key": public_key,
    }

    _save_devices(devices)

    return True


# ============================================================
# CHECK DEVICE
# ============================================================

def is_trusted_device(device_id):
    """
    Check whether a device is trusted.
    """

    devices = _load_devices()

    return device_id in devices


# ============================================================
# GET DEVICE
# ============================================================

def get_trusted_device(device_id):
    """
    Get information about a trusted device.
    """

    devices = _load_devices()

    return devices.get(device_id)


# ============================================================
# LIST DEVICES
# ============================================================

def list_trusted_devices():
    """
    Return all trusted devices.
    """

    return _load_devices()


# ============================================================
# REMOVE DEVICE
# ============================================================

def remove_trusted_device(device_id):
    """
    Remove a trusted device.
    """

    devices = _load_devices()

    if device_id not in devices:
        return False

    del devices[device_id]

    _save_devices(devices)

    return True


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("NEXIS TRUSTED DEVICE TEST")
    print("=" * 60)

    test_device_id = "test-phone-001"

    add_trusted_device(
        device_id=test_device_id,
        device_name="NEXIS-PHONE",
        device_type="phone",
        public_key="TEST_PUBLIC_KEY",
    )

    print("\nDEVICE ADDED:")
    print(
        get_trusted_device(test_device_id)
    )

    print(
        "\nIS TRUSTED:",
        is_trusted_device(test_device_id)
    )

    print("\nALL TRUSTED DEVICES:")
    print(
        json.dumps(
            list_trusted_devices(),
            indent=4
        )
    )

    remove_trusted_device(
        test_device_id
    )

    print(
        "\nAFTER REMOVAL:",
        is_trusted_device(test_device_id)
    )

    print("\nTRUSTED DEVICE TEST COMPLETE")