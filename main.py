"""
NEXIS - Main Voice Assistant
"""

from modules.voice import listen, speak, set_voice
from tools.ai import ask_ai


def is_nexis_shutdown_command(command):
    """
    Detect explicit commands intended to shut down NEXIS itself.

    These commands are handled locally and NEVER sent to
    the computer process-control system.
    """

    text = command.strip().lower()

    shutdown_commands = {
        "shutdown nexis",
        "shut down nexis",
        "exit nexis",
        "quit nexis",
        "close nexis",
        "stop nexis",
    }

    return text in shutdown_commands


def main():

    print("=" * 60)
    print("NEXIS")
    print("VOICE ASSISTANT")
    print("=" * 60)

    set_voice("Ryan")

    speak(
        "Good evening, sir. NEXIS is online."
    )

    print()

    running = True

    while running:

        try:

            command = listen(
                timeout=8,
                phrase_time_limit=10
            )

            if not command:
                continue

            command = command.strip()

            if not command:
                continue

            print(f"YOU: {command}")

            # =================================================
            # NEXIS SELF-SHUTDOWN
            # =================================================

            if is_nexis_shutdown_command(command):

                speak(
                    "Standing by, sir."
                )

                print(
                    "NEXIS: System shutting down."
                )

                running = False
                continue

            # =================================================
            # NORMAL AI PROCESSING
            # =================================================

            response = ask_ai(command)

            if response:

                speak(response)

        except KeyboardInterrupt:

            print(
                "\nNEXIS: Shutdown requested by user."
            )

            try:
                speak(
                    "Standing by, sir."
                )
            except Exception:
                pass

            running = False

        except Exception as error:

            print(
                f"NEXIS ERROR: {error}"
            )

            try:

                speak(
                    "I've encountered an error, sir."
                )

            except Exception:
                pass

    print(
        "NEXIS: Speech interrupted."
    )


if __name__ == "__main__":
    main()