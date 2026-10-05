"""
N.E.X.I.S. Network
Cryptographic Transport Authentication

Trusted devices must prove ownership of their private Ed25519 key
before the connection is authenticated.
"""

import asyncio
import json
import secrets

import websockets
from websockets.asyncio.server import serve
from websockets.asyncio.client import connect

from core.network.trusted_devices import (
    get_trusted_device,
    is_trusted_device,
)
from core.network.pairing import sign_challenge, verify_signature

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 8765


async def start_server(host=DEFAULT_HOST, port=DEFAULT_PORT):

    async def handler(websocket):

        print("NEXIS NETWORK: Connection received.")

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
                    "message": "Invalid identity message"
                }))
                await websocket.close()
                return

            device_id = identity.get("device_id")

            if not device_id:
                await websocket.send(json.dumps({
                    "status": "rejected",
                    "message": "Device identity missing"
                }))
                await websocket.close()
                return

            print(
                f"NEXIS NETWORK: Device identified: {device_id}"
            )

            # --------------------------------------------------
            # STEP 2 — Check trusted-device database
            # --------------------------------------------------

            if not is_trusted_device(device_id):

                print(
                    f"NEXIS NETWORK: REJECTED untrusted device: "
                    f"{device_id}"
                )

                await websocket.send(json.dumps({
                    "status": "rejected",
                    "message": "Device is not trusted"
                }))

                await websocket.close()
                return

            trusted_device = get_trusted_device(device_id)

            public_key = trusted_device["public_key"]

            # --------------------------------------------------
            # STEP 3 — Generate cryptographic challenge
            # --------------------------------------------------

            challenge = secrets.token_hex(32)

            print(
                "NEXIS NETWORK: Cryptographic challenge generated."
            )

            await websocket.send(json.dumps({
                "status": "challenge",
                "challenge": challenge,
            }))

            # --------------------------------------------------
            # STEP 4 — Receive signed challenge
            # --------------------------------------------------

            raw_signature = await websocket.recv()

            try:
                signature_data = json.loads(raw_signature)
            except json.JSONDecodeError:
                await websocket.send(json.dumps({
                    "status": "rejected",
                    "message": "Invalid signature message"
                }))
                await websocket.close()
                return

            signature = signature_data.get("signature")

            if not signature:
                await websocket.send(json.dumps({
                    "status": "rejected",
                    "message": "Signature missing"
                }))
                await websocket.close()
                return

            # --------------------------------------------------
            # STEP 5 — Verify signature
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
                    "NEXIS NETWORK: ❌ Cryptographic verification failed."
                )

                await websocket.send(json.dumps({
                    "status": "rejected",
                    "message": "Cryptographic verification failed"
                }))

                await websocket.close()
                return

            # --------------------------------------------------
            # STEP 6 — AUTHENTICATED
            # --------------------------------------------------

            print(
                f"NEXIS NETWORK: 🔐 Cryptographically authenticated: "
                f"{device_id}"
            )

            await websocket.send(json.dumps({
                "status": "authenticated",
                "device_id": device_id,
            }))

            # --------------------------------------------------
            # STEP 7 — Receive authenticated messages
            # --------------------------------------------------

            async for message in websocket:

                print("\nNEXIS NETWORK: Message received:")
                print(message)

                try:
                    data = json.loads(message)

                    response = {
                        "status": "received",
                        "message_id": data.get("message_id"),
                    }

                    await websocket.send(json.dumps(response))

                except json.JSONDecodeError:

                    await websocket.send(json.dumps({
                        "status": "error",
                        "message": "Invalid JSON"
                    }))

        except websockets.exceptions.ConnectionClosed:
            print("NEXIS NETWORK: Device disconnected.")

    print(
        f"NEXIS NETWORK: Listening on "
        f"ws://{host}:{port}"
    )

    async with serve(handler, host, port):
        await asyncio.Future()


async def authenticate_and_send(
    device_id,
    private_key_hex,
    host=DEFAULT_HOST,
    port=DEFAULT_PORT,
):
    """
    Connect to NEXIS and authenticate using the device's
    Ed25519 private key.
    """

    uri = f"ws://{host}:{port}"

    print(f"NEXIS NETWORK: Connecting to {uri}")

    async with connect(uri) as websocket:

        # --------------------------------------------------
        # STEP 1 — Send identity
        # --------------------------------------------------

        await websocket.send(json.dumps({
            "device_id": device_id,
        }))

        print("NEXIS NETWORK: Identity sent.")

        # --------------------------------------------------
        # STEP 2 — Receive challenge
        # --------------------------------------------------

        raw_response = await websocket.recv()

        response = json.loads(raw_response)

        print(
            "NEXIS NETWORK: Server response:"
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
            "NEXIS NETWORK: Challenge signed."
        )

        # --------------------------------------------------
        # STEP 4 — Send signature
        # --------------------------------------------------

        await websocket.send(json.dumps({
            "signature": signature,
        }))

        # --------------------------------------------------
        # STEP 5 — Receive authentication result
        # --------------------------------------------------

        raw_result = await websocket.recv()

        result = json.loads(raw_result)

        print(
            "NEXIS NETWORK: Authentication result:"
        )
        print(result)

        return result


if __name__ == "__main__":

    print("=" * 60)
    print("NEXIS CRYPTOGRAPHIC TRANSPORT TEST")
    print("=" * 60)

    async def test():

        from core.network.identity import create_identity
        from core.network.trusted_devices import add_trusted_device

        # --------------------------------------------------
        # Create simulated phone identity
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
        # Trust the phone
        # --------------------------------------------------

        add_trusted_device(
            device_id=phone_id,
            device_name="NEXIS-PHONE-TEST",
            device_type="phone",
            public_key=phone_public_key,
        )

        print("Phone added to trusted devices.")

        # --------------------------------------------------
        # Start server
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

            server_task.cancel()

            try:
                await server_task
            except asyncio.CancelledError:
                pass

    asyncio.run(test())