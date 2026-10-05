"""
N.E.X.I.S. - Fast Router

Routes user requests before they reach the main AI.

Fast path:
    Obvious computer commands -> Python

LLM path:
    Ambiguous commands -> Fast LLM classifier

Main AI path:
    Conversation / complex requests -> Main LLM
"""

import os
import json
import re

from dotenv import load_dotenv
from openai import OpenAI


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing from .env")

client = OpenAI(api_key=API_KEY)

ROUTER_MODEL = "gpt-5.6-luna"


# ============================================================
# APPLICATION ALIASES
# ============================================================

APPLICATION_ALIASES = {
    "spotify": "Spotify",
    "discord": "Discord",
    "brave": "Brave",
    "chrome": "Chrome",
    "google chrome": "Chrome",
    "edge": "Edge",
    "microsoft edge": "Edge",
    "word": "Word",
    "microsoft word": "Word",
    "excel": "Excel",
    "powerpoint": "PowerPoint",
    "task manager": "Task Manager",
    "notepad": "Notepad",
    "calculator": "Calculator",
}


# ============================================================
# RESULT
# ============================================================

def route_result(route, intent=None, target=None, confidence=1.0):
    return {
        "route": route,
        "intent": intent,
        "target": target,
        "confidence": confidence,
    }


# ============================================================
# FAST PYTHON ROUTER
# ============================================================

def fast_route(text):
    """
    Handle obvious commands without calling an LLM.
    """

    if not text:
        return route_result("main_llm", confidence=1.0)

    original = text.strip()
    lower = original.lower()

       # --------------------------------------------------------
    # OPEN / START / LAUNCH
    # --------------------------------------------------------

    open_match = re.match(
        r"^(?:"
        r"open(?:\s+up)?|"
        r"start|"
        r"launch|"
        r"run|"
        r"fire\s+up|"
        r"get"
        r")\s+(.+?)(?:\s+(?:for me|please))?\s*[.!?]?$",
        lower,
    )

    if open_match:
        target = open_match.group(1).strip()

        # Handle "get Spotify running"
        target = re.sub(
            r"\s+running$",
            "",
            target,
        ).strip()

        if target in APPLICATION_ALIASES:
            return route_result(
                "action",
                "launch_application",
                APPLICATION_ALIASES[target],
            )
    # --------------------------------------------------------
    # CLOSE / EXIT / QUIT / KILL / STOP
    # --------------------------------------------------------

    close_match = re.match(
        r"^(?:close|exit|quit|kill|stop)\s+(.+?)\s*[.!?]?$",
        lower,
    )

    if close_match:
        target = close_match.group(1).strip()

        if target in APPLICATION_ALIASES:
            return route_result(
                "action",
                "terminate_process",
                APPLICATION_ALIASES[target],
            )

    # --------------------------------------------------------
    # RUNNING / OPEN CHECK
    # --------------------------------------------------------

    running_match = re.match(
        r"^(?:is|check if|see if)\s+(.+?)\s+(?:running|open|opened)\??$",
        lower,
    )

    if running_match:
        target = running_match.group(1).strip()

        if target in APPLICATION_ALIASES:
            return route_result(
                "action",
                "find_process",
                APPLICATION_ALIASES[target],
            )

    # Nothing obvious.
    return None


# ============================================================
# LLM ROUTER
# ============================================================

def llm_route(text):
    """
    Use the fast LLM only when Python cannot confidently
    classify the request.
    """

    response = client.responses.create(
        model=ROUTER_MODEL,
        instructions="""
You are the NEXIS Fast Router.

Your ONLY job is to classify the user's request.

Return ONLY valid JSON:

{
  "route": "action" | "main_llm",
  "intent": "launch_application" | "terminate_process" | "find_process" | null,
  "target": "string" | null,
  "confidence": 0.0
}

Rules:

1. Use "action" only for clear computer application commands.

2. launch_application:
   The user wants an application opened, started, launched,
   fired up, brought up, etc.

3. terminate_process:
   The user wants an application closed, stopped, exited,
   killed, etc.

4. find_process:
   The user is asking whether an application is running/open.

5. Use "main_llm" for:
   - questions
   - explanations
   - casual conversation
   - web research
   - ambiguous requests
   - complex tasks

6. Never invent an application name.

7. Confidence must be between 0 and 1.

Return JSON only.
""",
        input=text,
    )

    try:
        data = json.loads(response.output_text)

        return route_result(
            data.get("route", "main_llm"),
            data.get("intent"),
            data.get("target"),
            float(data.get("confidence", 0.0)),
        )

    except Exception:
        return route_result(
            "main_llm",
            confidence=0.0,
        )


# ============================================================
# PUBLIC ROUTER
# ============================================================

def route(text):
    """
    Main routing entry point.

    1. Try zero-LLM Python routing.
    2. If uncertain, use the LLM router.
    """

    result = fast_route(text)

    if result is not None:
        return result

    return llm_route(text)


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    tests = [
        "open Spotify",
        "close Discord",
        "is Brave running",
        "can you fire up Spotify for me",
        "why is my computer slow",
    ]

    print("=" * 60)
    print("NEXIS FAST ROUTER TEST")
    print("=" * 60)

    for test in tests:

        print()
        print("INPUT:", test)

        result = route(test)

        print("RESULT:")
        print(json.dumps(result, indent=2))