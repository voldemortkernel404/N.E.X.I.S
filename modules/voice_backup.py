"""
NEXIS - Voice System

Ryan British Neural TTS
Google Speech Recognition
Markdown-safe TTS
Robust microphone handling
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


# ============================================================
# TEXT CLEANING
# ============================================================

def clean_for_speech(text):
    """
    Remove Markdown formatting before sending text to TTS.

    This prevents Ryan from literally saying:
        star star Paris star star
    """

    if not text:
        return ""

    text = str(text)

    # Markdown links:
    # [Google](https://google.com)
    text = re.sub(
        r"\[([^\]]+)\]\([^)]+\)",
        r"\1",
        text
    )

    # Bold / italic markers
    text = re.sub(
        r"\*\*([^*]+)\*\*",
        r"\1",
        text
    )

    text = re.sub(
        r"__([^_]+)__",
        r"\1",
        text
    )

    text = re.sub(
        r"(?<!\*)\*([^*]+)\*(?!\*)",
        r"\1",
        text
    )

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

    # Code fences
    text = re.sub(
        r"```.*?```",
        "",
        text,
        flags=re.DOTALL
    )

    # Markdown headings
    text = re.sub(
        r"^\s*#{1,6}\s*",
        "",
        text,
        flags=re.MULTILINE
    )

    # Bullets
    text = re.sub(
        r"^\s*[-*+]\s+",
        "",
        text,
        flags=re.MULTILINE
    )

    # Excess whitespace
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
# NEXIS NAME NORMALIZATION
# ============================================================

def normalize_nexis_name(text):
    """
    Google Speech Recognition may hear NEXIS as:
        Nex
        Nexus
        Nexis
        NEX

    Normalize those common variants.
    """

    if not text:
        return ""

    text = re.sub(
        r"\b(?:nex|nexus|nexis)\b",
        "NEXIS",
        text,
        flags=re.IGNORECASE
    )

    return text.strip()


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

    # IMPORTANT:
    # TTS receives cleaned text.
    speech_text = clean_for_speech(text)

    if not speech_text:
        return

    voice = VOICE_PROFILES[
        CURRENT_VOICE
    ]["edge_voice"]

    # Console can still show the original AI response.
    print(
        f"NEXIS: {speech_text}"
    )

    temp_path = None

    try:

        # ----------------------------------------------------
        # Create unique MP3
        # ----------------------------------------------------

        fd, temp_path = tempfile.mkstemp(
            prefix="nexis_",
            suffix=".mp3"
        )

        os.close(fd)

        # ----------------------------------------------------
        # Generate speech
        # ----------------------------------------------------

        async def generate():

            communicator = edge_tts.Communicate(
                speech_text,
                voice
            )

            await communicator.save(
                temp_path
            )

        asyncio.run(
            generate()
        )

        # ----------------------------------------------------
        # Reset pygame
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

        time.sleep(0.15)

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

                    if os.path.exists(
                        temp_path
                    ):
                        os.remove(
                            temp_path
                        )

                    break

                except PermissionError:

                    time.sleep(0.1)


# ============================================================
# MICROPHONE
# ============================================================

def listen(
    timeout=8,
    phrase_time_limit=10
):
    """
    Listen once.

    Returns:
        recognized text
        or ""
    """

    recognizer = sr.Recognizer()

    recognizer.energy_threshold = 300

    recognizer.dynamic_energy_threshold = True

    recognizer.dynamic_energy_adjustment_damping = 0.15

    recognizer.dynamic_energy_adjustment_ratio = 1.5

    recognizer.pause_threshold = 0.7

    recognizer.phrase_threshold = 0.25

    recognizer.non_speaking_duration = 0.4

    try:

        with sr.Microphone() as source:

            # Short calibration.
            recognizer.adjust_for_ambient_noise(
                source,
                duration=0.25
            )

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

        return normalize_nexis_name(
            result
        )

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
            timeout=5,
            phrase_time_limit=7
        )

        print(
            f"HEARD: {result or 'Nothing'}"
        )

    except KeyboardInterrupt:

        print(
            "\nNEXIS: Voice test stopped."
        )