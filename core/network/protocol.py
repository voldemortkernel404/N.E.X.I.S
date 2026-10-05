"""
N.E.X.I.S. Network
Communication Protocol

Defines the standard message format used by NEXIS devices.
"""

import json
import uuid
from datetime import datetime, timezone


# ============================================================
# PROTOCOL CONFIGURATION
# ============================================================

PROTOCOL_VERSION = "1.0"


# ============================================================
# MESSAGE CREATION
# ============================================================

def create_message(
    message_type,
    sender,
    payload=None,
    action=None,
):
    """
    Create a standard NEXIS network message.
    """

    message = {
        "version": PROTOCOL_VERSION,
        "message_id": str(uuid.uuid4()),
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "sender": sender,
        "type": message_type,
        "action": action,
        "payload": payload or {},
    }

    return message


# ============================================================
# MESSAGE SERIALIZATION
# ============================================================

def encode_message(message):
    """
    Convert a NEXIS message into JSON.
    """

    return json.dumps(
        message,
        separators=(",", ":"),
    )


# ============================================================
# MESSAGE DECODING
# ============================================================

def decode_message(data):
    """
    Convert JSON data back into a NEXIS message.
    """

    if isinstance(data, bytes):
        data = data.decode("utf-8")

    message = json.loads(data)

    validate_message(message)

    return message


# ============================================================
# MESSAGE VALIDATION
# ============================================================

def validate_message(message):
    """
    Validate the basic NEXIS protocol structure.
    """

    required_fields = {
        "version",
        "message_id",
        "timestamp",
        "sender",
        "type",
        "action",
        "payload",
    }

    missing = required_fields - message.keys()

    if missing:
        raise ValueError(
            f"Invalid NEXIS message. Missing fields: {missing}"
        )

    if message["version"] != PROTOCOL_VERSION:
        raise ValueError(
            f"Unsupported NEXIS protocol version: "
            f"{message['version']}"
        )

    return True


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    message = create_message(
        message_type="command",
        sender="NEXIS-PC",
        action="launch_application",
        payload={
            "application": "Spotify"
        },
    )

    print("=" * 60)
    print("NEXIS NETWORK PROTOCOL TEST")
    print("=" * 60)

    print("\nCREATED MESSAGE:")
    print(json.dumps(message, indent=4))

    encoded = encode_message(message)

    print("\nENCODED:")
    print(encoded)

    decoded = decode_message(encoded)

    print("\nDECODED:")
    print(json.dumps(decoded, indent=4))

    print("\nVALIDATION: OK")