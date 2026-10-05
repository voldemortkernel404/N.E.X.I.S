"""
N.E.X.I.S. Network
Session Manager

Manages an authenticated NEXIS device session over WSS.
"""

import asyncio
import json
import secrets
import time


class NexisSession:

    def __init__(self, websocket, device_id):
        self.websocket = websocket
        self.device_id = device_id
        self.session_id = secrets.token_hex(16)
        self.connected_at = time.time()
        self.authenticated = True
        self.last_activity = time.time()

    async def send(self, message):
        if not self.authenticated:
            raise RuntimeError("Session is not authenticated.")

        self.last_activity = time.time()

        await self.websocket.send(
            json.dumps(message)
        )

    async def receive(self):
        if not self.authenticated:
            raise RuntimeError("Session is not authenticated.")

        data = await self.websocket.recv()

        self.last_activity = time.time()

        return json.loads(data)

    async def close(self):
        self.authenticated = False

        await self.websocket.close()

    def info(self):
        return {
            "session_id": self.session_id,
            "device_id": self.device_id,
            "authenticated": self.authenticated,
            "connected_at": self.connected_at,
            "last_activity": self.last_activity,
        }


class SessionManager:

    def __init__(self):
        self.sessions = {}

    def add_session(self, session):
        self.sessions[session.session_id] = session

        return session.session_id

    def remove_session(self, session_id):
        return self.sessions.pop(
            session_id,
            None
        )

    def get_session(self, session_id):
        return self.sessions.get(session_id)

    def get_device_session(self, device_id):

        for session in self.sessions.values():

            if session.device_id == device_id:
                return session

        return None

    def list_sessions(self):
        return [
            session.info()
            for session in self.sessions.values()
        ]

    async def close_all(self):

        sessions = list(self.sessions.values())

        for session in sessions:

            try:
                await session.close()

            except Exception:
                pass

        self.sessions.clear()


async def heartbeat(session, interval=30):

    while session.authenticated:

        await asyncio.sleep(interval)

        try:

            await session.send({
                "type": "heartbeat",
                "timestamp": time.time(),
            })

        except Exception:

            session.authenticated = False
            break


if __name__ == "__main__":

    print("=" * 60)
    print("NEXIS SESSION MANAGER TEST")
    print("=" * 60)

    manager = SessionManager()

    print("\nSESSION MANAGER CREATED")

    print(
        "Active sessions:",
        manager.list_sessions()
    )

    print("\nSESSION MANAGER TEST COMPLETE")