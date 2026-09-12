"""
NEXIS - Wake Word Engine
"""

import os

import numpy as np
import pyaudio
from openwakeword.model import Model

from core.config import (
    WAKE_THRESHOLD,
    WAKE_SAMPLE_RATE,
    WAKE_CHUNK_SIZE,
)


# ============================================================
# CONFIGURATION
# ============================================================

MODEL_DIR = os.path.join(
    os.path.dirname(
        os.path.dirname(__file__)
    ),
    "assets",
    "wakewords",
)

MODEL_PATH = os.path.join(
    MODEL_DIR,
    "nexis.onnx",
)


class NexisWakeWord:

    def __init__(self):

        print("NEXIS: Initializing wake engine...")

        self.audio = None
        self.stream = None
        self.model = None

        if not os.path.exists(MODEL_PATH):

            print(
                "NEXIS: Custom NEXIS wake model not found."
            )

            print(
                f"NEXIS: Expected: {MODEL_PATH}"
            )

            return

        self.model = Model(
            wakeword_models=[
                MODEL_PATH
            ]
        )

        print(
            "NEXIS: Custom wake model loaded."
        )

    # ========================================================
    # MICROPHONE
    # ========================================================

    def start(self):

        if self.stream is not None:
            return

        self.audio = pyaudio.PyAudio()

        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=1,
            rate=WAKE_SAMPLE_RATE,
            input=True,
            frames_per_buffer=WAKE_CHUNK_SIZE,
        )

        print(
            "NEXIS: Wake microphone ready."
        )

    # ========================================================
    # STOP
    # ========================================================

    def stop(self):

        if self.stream:

            self.stream.stop_stream()
            self.stream.close()

            self.stream = None

        if self.audio:

            self.audio.terminate()
            self.audio = None

    # ========================================================
    # READ AUDIO
    # ========================================================

    def read_audio(self):

        audio = self.stream.read(
            WAKE_CHUNK_SIZE,
            exception_on_overflow=False,
        )

        return np.frombuffer(
            audio,
            dtype=np.int16,
        )

    # ========================================================
    # DETECT
    # ========================================================

    def detect(self):

        if self.model is None:
            return False

        audio = self.read_audio()

        predictions = self.model.predict(
            audio
        )

        score = max(
            predictions.values()
        )

        if score >= WAKE_THRESHOLD:

            print(
                f"NEXIS: Wake detected "
                f"({score:.2f})"
            )

            return True

        return False

    # ========================================================
    # LISTEN
    # ========================================================

    def listen(self):

        if self.model is None:

            print(
                "NEXIS: Wake model unavailable."
            )

            return False

        self.start()

        print(
            "NEXIS: Listening for 'NEXIS'..."
        )

        try:

            while True:

                if self.detect():

                    return True

        except KeyboardInterrupt:

            print(
                "NEXIS: Wake listener stopped."
            )

            return False

        finally:

            self.stop()


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    engine = NexisWakeWord()

    engine.listen()