"""
N.E.X.I.S. Network
Secure Cryptographic WebSocket Transport

Uses:
- WSS/TLS encryption
- Trusted-device verification
- Ed25519 challenge-response authentication
"""

import asyncio
import json
import secrets
import ssl
from pathlib import Path

import websockets
from websockets.asyncio.server import serve
from websockets.asyncio.client import connect

from core.network.trusted_devices import (
    get_trusted_device,
    is_trusted_device,
)
from core.network.pairing import sign_challenge, verify_signature


NETWORK_DIR = Path(__file__).resolve().parent
CERT_DIR = NETWORK_DIR / "certs"

CERT_FILE = CERT_DIR / "server.crt"
KEY_FILE = CERT_DIR / "server.key"

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


def create_server_ssl_context():
    context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    context.minimum_version = ssl.TLSVersion.TLSv1_2

    context.load_cert_chain(
        certfile=CERT_FILE,
        keyfile=KEY_FILE,
    )

    return context


def create_client_ssl_context():
    context = ssl.create_default_context(
        purpose=ssl.Purpose.SERVER_AUTH,
        cafile=CERT_FILE,
    )

    context.minimum_version = ssl.TLSVersion.TLSv1_2

    return context


async def start_server(
    host=DEFAULT_HOST,
    port=DEFAULT_PORT,
):

    ssl_context = create_server_ssl_context()

    async def handler(websocket):

        print("NEXIS NETWORK: Secure connection received.")

        try:

            # --------------------------------------------------
            # STEP 1 — Receive device identity
            # --------------------------------------------------

            raw_identity = await websocket.recv()

            try:
                identity = json.loads(raw_identity)

            except json.JSONDecodeError:

                await websocket.send(json.dumps({
                    "status": "rejected",
                    "message": "Invalid identity message",
                }))

                await websocket.close()
                return

            device_id = identity.get("device_id")

            if not device_id:

                await websocket.send(json.dumps({
                    "status": "rejected",
                    "message": "Device identity missing",
                }))

                await websocket.close()
                return

            print(
                f"NEXIS NETWORK: Device identified: {device_id}"
            )

            # --------------------------------------------------
            # STEP 2 — Trusted-device verification
            # --------------------------------------------------

            if not is_trusted_device(device_id):

                print(
                    "NEXIS NETWORK: "
                    f"REJECTED untrusted device: {device_id}"
                )

                await websocket.send(json.dumps({
                    "status": "rejected",
                    "message": "Device is not trusted",
                }))

                await websocket.close()
                return

            trusted_device = get_trusted_device(device_id)

            public_key = trusted_device["public_key"]

            # --------------------------------------------------
            # STEP 3 — Generate random challenge
            # --------------------------------------------------

            challenge = secrets.token_hex(32)

            print(
                "NEXIS NETWORK: "
                "Cryptographic challenge generated."
            )

            await websocket.send(json.dumps({
                "status": "challenge",
                "challenge": challenge,
            }))

            # --------------------------------------------------
            # STEP 4 — Receive signature
            # --------------------------------------------------

            raw_signature = await websocket.recv()

            try:
                signature_data = json.loads(raw_signature)

            except json.JSONDecodeError:

                await websocket.send(json.dumps({
                    "status": "rejected",
                    "message": "Invalid signature message",
                }))

                await websocket.close()
                return

            signature = signature_data.get("signature")

            if not signature:

                await websocket.send(json.dumps({
                    "status": "rejected",
                    "message": "Signature missing",
                }))

                await websocket.close()
                return

            # --------------------------------------------------
            # STEP 5 — Verify Ed25519 signature
            # --------------------------------------------------

            valid = verify_signature(
                public_key,
                {
                    "device_id": device_id,
                    "code": challenge,
                    "created_at": challenge,
                },
                signature,
            )

            if not valid:

                print(
                    "NEXIS NETWORK: "
                    "❌ Cryptographic verification failed."
                )

                await websocket.send(json.dumps({
                    "status": "rejected",
                    "message": "Cryptographic verification failed",
                }))

                await websocket.close()
                return

            # --------------------------------------------------
            # STEP 6 — AUTHENTICATED
            # --------------------------------------------------

            print(
                "NEXIS NETWORK: "
                f"🔐 Securely authenticated: {device_id}"
            )

            await websocket.send(json.dumps({
                "status": "authenticated",
                "device_id": device_id,
                "transport": "wss",
            }))

            # --------------------------------------------------
            # STEP 7 — Receive authenticated messages
            # --------------------------------------------------

            async for message in websocket:

                print(
                    "\nNEXIS NETWORK: "
                    "Authenticated message received:"
                )

                print(message)

                try:

                    data = json.loads(message)

                    response = {
                        "status": "received",
                        "message_id": data.get("message_id"),
                    }

                    await websocket.send(
                        json.dumps(response)
                    )

                except json.JSONDecodeError:

                    await websocket.send(json.dumps({
                        "status": "error",
                        "message": "Invalid JSON",
                    }))

        except websockets.exceptions.ConnectionClosed:

            print(
                "NEXIS NETWORK: "
                "Secure device disconnected."
            )

    print(
        f"NEXIS NETWORK: "
        f"Listening securely on wss://{host}:{port}"
    )

    async with serve(
        handler,
        host,
        port,
        ssl=ssl_context,
    ):

        await asyncio.Future()


async def authenticate_and_send(
    device_id,
    private_key_hex,
    host=DEFAULT_HOST,
    port=DEFAULT_PORT,
):

    uri = f"wss://{host}:{port}"

    ssl_context = create_client_ssl_context()

    print(
        f"NEXIS NETWORK: "
        f"Connecting securely to {uri}"
    )

    async with connect(
        uri,
        ssl=ssl_context,
    ) as websocket:

        # --------------------------------------------------
        # STEP 1 — Send identity
        # --------------------------------------------------

        await websocket.send(json.dumps({
            "device_id": device_id,
        }))

        print(
            "NEXIS NETWORK: "
            "Identity sent over TLS."
        )

        # --------------------------------------------------
        # STEP 2 — Receive challenge
        # --------------------------------------------------

        raw_response = await websocket.recv()

        response = json.loads(raw_response)

        print(
            "NEXIS NETWORK: "
            "Server response:"
        )

        print(response)

        if response.get("status") != "challenge":
            return response

        challenge = response["challenge"]

        # --------------------------------------------------
        # STEP 3 — Sign challenge
        # --------------------------------------------------

        challenge_data = {
            "device_id": device_id,
            "code": challenge,
            "created_at": challenge,
        }

        signature = sign_challenge(
            private_key_hex,
            challenge_data,
        )

        print(
            "NEXIS NETWORK: "
            "Challenge signed."
        )

        # --------------------------------------------------
        # STEP 4 — Send signature
        # --------------------------------------------------

        await websocket.send(json.dumps({
            "signature": signature,
        }))

        # --------------------------------------------------
        # STEP 5 — Authentication result
        # --------------------------------------------------

        raw_result = await websocket.recv()

        result = json.loads(raw_result)

        print(
            "NEXIS NETWORK: "
            "Authentication result:"
        )

        print(result)

        return result


if __name__ == "__main__":

    print("=" * 60)
    print("NEXIS WSS + CRYPTOGRAPHIC AUTH TEST")
    print("=" * 60)

    async def test():

        from core.network.identity import create_identity
        from core.network.trusted_devices import (
            add_trusted_device,
            remove_trusted_device,
        )

        # --------------------------------------------------
        # Create temporary simulated phone
        # --------------------------------------------------

        phone = create_identity(
            device_name="NEXIS-PHONE-TEST",
            device_type="phone",
        )

        phone_id = phone["device_id"]
        phone_private_key = phone["private_key"]
        phone_public_key = phone["public_key"]

        print("\nSIMULATED PHONE:")
        print("Device ID:", phone_id)

        # --------------------------------------------------
        # Trust simulated phone
        # --------------------------------------------------

        add_trusted_device(
            device_id=phone_id,
            device_name="NEXIS-PHONE-TEST",
            device_type="phone",
            public_key=phone_public_key,
        )

        print(
            "Phone added to trusted devices."
        )

        # --------------------------------------------------
        # Start secure server
        # --------------------------------------------------

        server_task = asyncio.create_task(
            start_server()
        )

        await asyncio.sleep(1)

        try:

            result = await authenticate_and_send(
                device_id=phone_id,
                private_key_hex=phone_private_key,
            )

            print("\nFINAL RESULT:")
            print(result)

        finally:

            # Clean up test device
            remove_trusted_device(phone_id)

            server_task.cancel()

            try:
                await server_task

            except asyncio.CancelledError:
                pass

    asyncio.run(test())