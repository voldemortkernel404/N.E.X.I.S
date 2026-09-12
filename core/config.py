"""
NEXIS - Central Configuration
"""

from pathlib import Path


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

CORE_DIR = BASE_DIR / "core"
MODULES_DIR = BASE_DIR / "modules"
TOOLS_DIR = BASE_DIR / "tools"
GUI_DIR = CORE_DIR / "GUI"

DATA_DIR = BASE_DIR / "data"
ASSETS_DIR = BASE_DIR / "assets"
LOGS_DIR = BASE_DIR / "logs"


# ============================================================
# NEXIS IDENTITY
# ============================================================

ASSISTANT_NAME = "NEXIS"

WAKE_PHRASE = "NEXIS"


# ============================================================
# VOICE
# ============================================================

VOICE_PROFILE = "Ryan - British Assistant"

VOICE_NAME = "en-GB-RyanNeural"

SPEECH_RATE = 165


# ============================================================
# MICROPHONE
# ============================================================

MIC_SAMPLE_RATE = 16000

LISTEN_TIMEOUT = 5

PHRASE_TIME_LIMIT = 6


# ============================================================
# WAKE ENGINE
# ============================================================

WAKE_MODEL = "hey_None"

WAKE_THRESHOLD = 0.5

WAKE_SAMPLE_RATE = 16000

WAKE_CHUNK_SIZE = 1280


# ============================================================
# SYSTEM
# ============================================================

DEBUG_MODE = True

VERSION = "0.1.0"

ENVIRONMENT = "development"


# ============================================================
# DIRECTORY INITIALIZATION
# ============================================================

for directory in [
    DATA_DIR,
    ASSETS_DIR,
    LOGS_DIR,
]:
    directory.mkdir(
        parents=True,
        exist_ok=True
    )


# ============================================================
# CONFIGURATION STATUS
# ============================================================

def get_config():

    return {
        "assistant_name": ASSISTANT_NAME,
        "wake_phrase": WAKE_PHRASE,
        "voice_profile": VOICE_PROFILE,
        "voice_name": VOICE_NAME,
        "wake_model": WAKE_MODEL,
        "wake_threshold": WAKE_THRESHOLD,
        "version": VERSION,
        "environment": ENVIRONMENT,
        "debug": DEBUG_MODE,
    }


if __name__ == "__main__":

    print("=" * 60)
    print("NEXIS CONFIGURATION")
    print("=" * 60)

    for key, value in get_config().items():
        print(f"{key}: {value}")