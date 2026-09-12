"""
NEXIS - Core Brain
"""

import re
from datetime import datetime
from tools.ai import ask_ai

NEXIS_ALIASES = {
     "nex",
    "nexus",
    "nexis",
    "nexes",
    "nexis's",
    "nexus's",
}


def normalize_nexis(text):
    if not text:
        return ""

    words = text.split()
    result = []

    for word in words:
        clean = re.sub(r"[^\w]", "", word.lower())

        if clean in NEXIS_ALIASES:
            result.append("NEXIS")
        else:
            result.append(word)

    return " ".join(result)


def process_command(text):

    if not text:
        return "I didn't hear you, sir."

    text = normalize_nexis(text)
    command = text.lower().strip()

    if command in {
        "hello",
        "hi",
        "hey",
        "hello nexis",
        "hi nexis",
        "hey nexis",
    }:
        return "Yes, sir. NEXIS is online."

    if "who are you" in command:
        return "I am NEXIS, your personal AI assistant."

    if "status" in command:
        return "All primary systems are operational, sir."

    if "time" in command:
        current_time = datetime.now().strftime("%I:%M %p")
        return f"The current time is {current_time}, sir."

    if "date" in command or "what day" in command:
        current_date = datetime.now().strftime("%A, %d %B %Y")
        return f"Today is {current_date}, sir."

    if command in {
        "goodbye",
        "shutdown",
        "shutdown nexis",
        "go offline",
    }:
        return "Standing by, sir."

    return ask_ai(text)

def get_brain_status():
    return {
        "online": True,
        "name": "NEXIS",
        "mode": "LOCAL COMMAND PROCESSING",
    }


if __name__ == "__main__":

    print("=" * 60)
    print("NEXIS BRAIN TEST")
    print("=" * 60)

    tests = [
        "hello",
        "hello Nex",
        "hello Nexus",
        "who are you",
        "what is the time",
        "what is the date",
        "status",
        "test command",
    ]

    for command in tests:

        print(f"\nYOU: {command}")

        normalized = normalize_nexis(command)
        response = process_command(command)

        print(f"NORMALIZED: {normalized}")
        print(f"NEXIS: {response}")