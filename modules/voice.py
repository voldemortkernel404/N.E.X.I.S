"""
NEXIS - Voice System

Features:
- Ryan British English TTS
- Fast microphone reuse
- One-time microphone calibration
- Google Speech Recognition
- NEXIS name normalisation
- Markdown-safe speech
- Clean console output
- Ctrl+C support
"""

import asyncio
import os
import re
import tempfile
import time

import edge_tts
import pygame
import speech_recognition as sr


# ============================================================
# CONFIGURATION
# ============================================================

VOICE_PROFILES = {
    "Ryan": {
        "name": "Ryan - British Assistant",
        "edge_voice": "en-GB-RyanNeural",
    }
}

CURRENT_VOICE = "Ryan"

# Your headset microphone.
# We tested this device and it recognised your speech.
MICROPHONE_INDEX = 1


# ============================================================
# SPEECH RECOGNITION
# ============================================================

recognizer = sr.Recognizer()

recognizer.energy_threshold = 300
recognizer.dynamic_energy_threshold = True
recognizer.dynamic_energy_adjustment_damping = 0.15
recognizer.dynamic_energy_adjustment_ratio = 1.5

recognizer.pause_threshold = 0.7
recognizer.phrase_threshold = 0.25
recognizer.non_speaking_duration = 0.4


# ============================================================
# MICROPHONE STATE
# ============================================================

microphone = None
microphone_calibrated = False


def initialize_microphone():
    """
    Initialise and calibrate the selected microphone once.

    This prevents NEXIS from recalibrating every time
    the user speaks, reducing response latency.
    """

    global microphone
    global microphone_calibrated

    if microphone is not None and microphone_calibrated:
        return True

    try:

        print("NEXIS: Initialising microphone...")

        microphone = sr.Microphone(
            device_index=MICROPHONE_INDEX
        )

        with microphone as source:

            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.25
            )

        microphone_calibrated = True

        print("NEXIS: Microphone ready.")

        return True

    except Exception as error:

        print(
            f"NEXIS MICROPHONE ERROR: {error}"
        )

        microphone = None
        microphone_calibrated = False

        return False


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_for_speech(text):
    """
    Remove Markdown formatting before sending text to TTS.

    This prevents NEXIS from speaking things such as:
    **bold**
    *italic*
    `code`
    [links](url)
    """

    if not text:
        return ""

    text = str(text)

    # Markdown links
    text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        text
    )

    # Code blocks
    text = re.sub(
        r"```.*?```",
        "",
        text,
        flags=re.DOTALL
    )

    # Bold
    text = re.sub(
        r"\*\*([^*]+)\*\*",
        r"\1",
        text
    )

    # Italic
    text = re.sub(
        r"(?<!\*)\*([^*]+)\*(?!\*)",
        r"\1",
        text
    )

    # Underline/bold
    text = re.sub(
        r"__([^_]+)__",
        r"\1",
        text
    )

    # Underscore italic
    text = re.sub(
        r"(?<!_)_([^_]+)_(?!_)",
        r"\1",
        text
    )

    # Inline code
    text = re.sub(
        r"`([^`]+)`",
        r"\1",
        text
    )

    # Markdown headings
    text = re.sub(
        r"^\s*#{1,6}\s*",
        "",
        text,
        flags=re.MULTILINE
    )

    # Markdown bullets
    text = re.sub(
        r"^\s*[-*+]\s+",
        "",
        text,
        flags=re.MULTILINE
    )

    # Remove remaining Markdown characters
    text = text.replace("**", "")
    text = text.replace("__", "")
    text = text.replace("`", "")

    # Normalise spaces
    text = re.sub(
        r"[ \t]+",
        " ",
        text
    )

    text = re.sub(
        r"\n{3,}",
        "\n\n",
        text
    )

    return text.strip()


# ============================================================
# NEXIS NAME NORMALISATION
# ============================================================

def normalize_nexis_name(text):
    """
    Correct common speech-recognition variations of NEXIS.

    Example:

        hello Nexus
        ↓
        hello NEXIS
    """

    if not text:
        return ""

    words = text.split()

    corrected = []

    variants = {
        "nexus": "NEXIS",
        "nexis": "NEXIS",
        "nexes": "NEXIS",
        "nexis's": "NEXIS's",
        "nexus's": "NEXIS's",
    }

    for word in words:

        # Preserve punctuation around the word.
        leading = re.match(
            r"^[^\w]*",
            word
        ).group()

        trailing = re.search(
            r"[^\w]*$",
            word
        ).group()

        core = word[
            len(leading):
            len(word) - len(trailing)
            if trailing
            else len(word)
        ]

        replacement = variants.get(
            core.lower(),
            core
        )

        corrected.append(
            leading
            + replacement
            + trailing
        )

    return " ".join(corrected)


# ============================================================
# VOICE SELECTION
# ============================================================

def set_voice(name="Ryan"):

    global CURRENT_VOICE

    if name not in VOICE_PROFILES:

        print(
            f"NEXIS: Unknown voice: {name}"
        )

        return False

    CURRENT_VOICE = name

    print(
        f"NEXIS: Voice selected: "
        f"{VOICE_PROFILES[name]['name']}"
    )

    return True


# ============================================================
# TEXT TO SPEECH
# ============================================================

def speak(text):

    if not text:
        return

    speech_text = clean_for_speech(text)

    if not speech_text:
        return

    voice = VOICE_PROFILES[
        CURRENT_VOICE
    ]["edge_voice"]

    print(
        f"NEXIS: {speech_text}"
    )

    temp_path = None

    try:

        # ----------------------------------------------------
        # Create temporary MP3
        # ----------------------------------------------------

        fd, temp_path = tempfile.mkstemp(
            prefix="nexis_",
            suffix=".mp3"
        )

        os.close(fd)

        # ----------------------------------------------------
        # Generate TTS
        # ----------------------------------------------------

        async def generate():

            communicator = edge_tts.Communicate(
                speech_text,
                voice
            )

            await communicator.save(
                temp_path
            )

        asyncio.run(generate())

        # ----------------------------------------------------
        # Initialise audio
        # ----------------------------------------------------

        if pygame.mixer.get_init():

            try:
                pygame.mixer.music.stop()
            except Exception:
                pass

            pygame.mixer.quit()

        pygame.mixer.init()

        pygame.mixer.music.load(
            temp_path
        )

        pygame.mixer.music.play()

        clock = pygame.time.Clock()

        while pygame.mixer.music.get_busy():

            clock.tick(30)

        pygame.mixer.music.stop()

        pygame.mixer.quit()

        # Allow Windows to release the file.
        time.sleep(0.1)

    except KeyboardInterrupt:

        print(
            "\nNEXIS: Speech interrupted."
        )

        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception:
            pass

        raise

    except Exception as error:

        print(
            f"NEXIS TTS ERROR: {error}"
        )

        try:
            pygame.mixer.music.stop()
            pygame.mixer.quit()
        except Exception:
            pass

    finally:

        if temp_path:

            for _ in range(20):

                try:

                    if os.path.exists(temp_path):
                        os.remove(temp_path)

                    break

                except PermissionError:

                    time.sleep(0.1)


# ============================================================
# LISTEN
# ============================================================

def listen(
    timeout=8,
    phrase_time_limit=10
):
    """
    Listen for one spoken command.

    The microphone is calibrated only once.
    """

    if not initialize_microphone():

        return ""

    try:

        with microphone as source:

            audio = recognizer.listen(
                source,
                timeout=timeout,
                phrase_time_limit=phrase_time_limit
            )

        try:

            result = recognizer.recognize_google(
                audio,
                language="en-US"
            )

        except sr.UnknownValueError:

            return ""

        except sr.RequestError as error:

            print(
                f"NEXIS: Speech service error: {error}"
            )

            return ""

        if not result:

            return ""

        result = result.strip()

        if not result:

            return ""

        # Correct Nexus → NEXIS.
        result = normalize_nexis_name(
            result
        )

        return result

    except sr.WaitTimeoutError:

        return ""

    except KeyboardInterrupt:

        raise

    except Exception as error:

        print(
            f"NEXIS MICROPHONE ERROR: {error}"
        )

        return ""


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("NEXIS VOICE SYSTEM TEST")
    print("=" * 60)

    set_voice("Ryan")

    print()

    if not initialize_microphone():

        print(
            "NEXIS: Microphone initialisation failed."
        )

        raise SystemExit(1)

    print()

    speak(
        "Good evening, sir. "
        "This is NEXIS. "
        "My voice system is operational."
    )

    print()

    print(
        "Say: hello NEXIS"
    )

    try:

        result = listen(
            timeout=8,
            phrase_time_limit=8
        )

        print(
            f"HEARD: {result or 'Nothing'}"
        )

    except KeyboardInterrupt:

        print(
            "\nNEXIS: Voice test stopped."
        )