from core.network.trusted_devices import add_trusted_device
from core.network.transport import send_message


PHONE_ID = "NEXIS-PHONE-TEST"


def main():
    print("=" * 60)
    print("NEXIS TRUSTED DEVICE TRANSPORT TEST")
    print("=" * 60)

    # Add simulated phone to trusted devices
    add_trusted_device(
        device_id=PHONE_ID,
        device_name="NEXIS-PHONE",
        device_type="phone",
        public_key="TEST_PUBLIC_KEY",
    )

    print("\nTRUSTED DEVICE ADDED:")
    print(PHONE_ID)

    import asyncio

    async def test():
        from core.network.transport import start_server
        from core.network.protocol import create_message

        server_task = asyncio.create_task(start_server())

        await asyncio.sleep(1)

        message = create_message(
            message_type="command",
            sender=PHONE_ID,
            action="test_connection",
            payload={
                "message": "Hello from trusted NEXIS phone"
            },
        )

        try:
            response = await send_message(message)

            print("\nFINAL RESULT:")
            print(response)

        finally:
            server_task.cancel()

            try:
                await server_task
            except asyncio.CancelledError:
                pass

    asyncio.run(test())


if __name__ == "__main__":
    main()