"""
NEXIS - AI + Web + Memory + Computer Control

The AI handles conversation and web questions.
Deterministic computer-command routing handles obvious
open/close/check commands reliably.
"""

import os
import json
import re

from dotenv import load_dotenv
from openai import OpenAI

from tools.memory import add_message, get_history
from tools.router import run_action


# ============================================================
# CONFIGURATION
# ============================================================

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")

if not API_KEY:
    raise RuntimeError("OPENAI_API_KEY is missing from .env")

client = OpenAI(api_key=API_KEY)


# ============================================================
# STATE
# ============================================================

# Last application NEXIS interacted with.
# Used for commands such as:
# "close it"
# "open it again"
# "shut it down"
last_application = None


# ============================================================
# PERSONALITY
# ============================================================

SYSTEM_PROMPT = """
You are NEXIS (Neural EXecution & Intelligence System),
the user's personal AI assistant running on their Windows computer.

Personality:
- Calm
- Intelligent
- Professional
- Helpful
- Concise
- British-assistant style
- Address the user as "sir" when appropriate.

You have access to:
- Conversation memory
- Live web search
- Computer-control tools

IMPORTANT COMPUTER RULES:

1. If the user asks you to OPEN, START or LAUNCH an application,
   use launch_application.

2. If the user asks you to CLOSE, EXIT, QUIT, KILL, STOP or
   SHUT DOWN an application/process, use terminate_process.

3. NEVER use find_process as a substitute for terminate_process.

4. find_process is ONLY for questions such as:
   - "Is Spotify running?"
   - "Check if Discord is open."
   - "Is Chrome running?"

5. terminate_process is for commands such as:
   - "Close Spotify."
   - "Kill Discord."
   - "Stop Chrome."
   - "Shut down Word."

6. If the user says "close it", "kill it", "shut it down",
   or similar, use the most recently mentioned application
   from the conversation when the target is obvious.

7. Never claim an action succeeded unless the computer tool
   confirms it.

8. Never invent computer-tool results.

9. Use web search for current, recent, live, or changing
   information.

10. For normal conversation, answer normally.

11. The assistant's name is NEXIS, not Nexus or Jarvis.
"""


# ============================================================
# COMPUTER TOOLS
# ============================================================

FUNCTION_TOOLS = [

    {
        "type": "function",
        "name": "system_info",
        "description": "Get basic information about the user's Windows computer.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "find_applications",
        "description": "Find installed Windows applications.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "launch_application",
        "description": (
            "OPEN, START, or LAUNCH an installed Windows application. "
            "Use this when the user wants an application opened."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "application": {
                    "type": "string",
                    "description": "Application name, such as Spotify, Discord, Word, Calculator."
                }
            },
            "required": ["application"],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "find_process",
        "description": (
            "CHECK whether a Windows process is currently running. "
            "DO NOT use this to close or kill a process."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Process executable name, for example Spotify.exe."
                }
            },
            "required": ["name"],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "terminate_process",
        "description": (
            "CLOSE, EXIT, STOP, KILL, or SHUT DOWN a Windows process. "
            "This is the correct tool when the user tells NEXIS to "
            "close an application. DO NOT use find_process first "
            "unless the user specifically asked whether it is running."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "name": {
                    "type": "string",
                    "description": "Process executable name, such as Spotify.exe or Discord.exe."
                }
            },
            "required": ["name"],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "list_processes",
        "description": "List currently running Windows processes.",
        "parameters": {
            "type": "object",
            "properties": {},
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "list_files",
        "description": "List files inside the NEXIS workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative path inside the NEXIS workspace."
                }
            },
            "required": ["path"],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "read_file",
        "description": "Read a text file inside the NEXIS workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative file path."
                }
            },
            "required": ["path"],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "write_file",
        "description": "Write a text file inside the NEXIS workspace.",
        "parameters": {
            "type": "object",
            "properties": {
                "path": {
                    "type": "string",
                    "description": "Relative file path."
                },
                "content": {
                    "type": "string",
                    "description": "Content to write."
                }
            },
            "required": ["path", "content"],
            "additionalProperties": False
        }
    },

    {
        "type": "function",
        "name": "open_url",
        "description": "Open a website URL in the default browser.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "URL to open."
                }
            },
            "required": ["url"],
            "additionalProperties": False
        }
    }
]


# ============================================================
# APPLICATION NAME HELPERS
# ============================================================

PROCESS_ALIASES = {
    "spotify": "Spotify.exe",
    "discord": "Discord.exe",
    "brave": "brave.exe",
    "brave nightly": "brave.exe",
    "chrome": "chrome.exe",
    "google chrome": "chrome.exe",
    "edge": "msedge.exe",
    "microsoft edge": "msedge.exe",
    "word": "WINWORD.EXE",
    "microsoft word": "WINWORD.EXE",
    "excel": "EXCEL.EXE",
    "microsoft excel": "EXCEL.EXE",
    "powerpoint": "POWERPNT.EXE",
    "task manager": "Taskmgr.exe",
    "notepad": "notepad.exe",
    "calculator": "CalculatorApp.exe",
}


def normalize_application_name(name):
    """
    Convert common application names into process names.
    """

    if not name:
        return None

    cleaned = name.strip().lower()

    cleaned = re.sub(
        r"^(the|my)\s+",
        "",
        cleaned
    )

    return PROCESS_ALIASES.get(
        cleaned,
        cleaned if cleaned.endswith(".exe")
        else cleaned + ".exe"
    )


# ============================================================
# DETERMINISTIC COMPUTER COMMANDS
# ============================================================

def handle_direct_computer_command(prompt):
    """
    Handle obvious computer commands without asking the LLM
    to choose between similar tools.

    Returns:
        None -> send to AI normally
        string -> completed response
    """

    global last_application

    text = prompt.strip()
    lower = text.lower()

    # --------------------------------------------------------
    # CLOSE / KILL / STOP / SHUT DOWN
    # --------------------------------------------------------

    close_match = re.search(
        r"\b(?:close|kill|stop|terminate|exit|quit|shutdown|shut down)\s+"
        r"(?:the\s+|my\s+)?(.+?)\s*$",
        lower
    )

    if close_match:

        target = close_match.group(1).strip()

        # Remove polite filler.
        target = re.sub(
            r"\bplease\b",
            "",
            target
        ).strip()

        # "it" means the last application.
        if target in {
            "it",
            "that",
            "this",
            "the app",
            "the application"
        }:

            if not last_application:
                return (
                    "I'm not sure which application you mean, sir."
                )

            target = last_application

        process_name = normalize_application_name(target)

        print("NEXIS DIRECT ACTION: terminate_process")
        print(f"NEXIS DIRECT ARGS: {{'name': '{process_name}'}}")

        result = run_action(
            "terminate_process",
            {
                "name": process_name
            }
        )

        return str(result)

    # --------------------------------------------------------
    # OPEN / START / LAUNCH
    # --------------------------------------------------------

    open_match = re.search(
        r"\b(?:open|launch|start)\s+"
        r"(?:the\s+|my\s+)?(.+?)\s*$",
        lower
    )

    if open_match:

        target = open_match.group(1).strip()

        target = re.sub(
            r"\bplease\b",
            "",
            target
        ).strip()

        if target in {
            "it",
            "that",
            "this",
            "the app",
            "the application"
        }:

            if not last_application:
                return (
                    "I'm not sure which application you mean, sir."
                )

            target = last_application

        # Don't steal web requests.
        if (
            target.startswith("http://")
            or target.startswith("https://")
            or "." in target and " " not in target
        ):
            return None

        print("NEXIS DIRECT ACTION: launch_application")
        print(f"NEXIS DIRECT ARGS: {{'application': '{target}'}}")

        result = run_action(
            "launch_application",
            {
                "application": target
            }
        )

        last_application = target.title()

        return str(result)

    # --------------------------------------------------------
    # IS X RUNNING?
    # --------------------------------------------------------

    running_match = re.search(
        r"\b(?:is|check(?:\s+if)?|see\s+if)\s+"
        r"(.+?)\s+(?:running|open|opened)\s*\??$",
        lower
    )

    if running_match:

        target = running_match.group(1).strip()

        process_name = normalize_application_name(target)

        print("NEXIS DIRECT ACTION: find_process")
        print(f"NEXIS DIRECT ARGS: {{'name': '{process_name}'}}")

        result = run_action(
            "find_process",
            {
                "name": process_name
            }
        )

        return str(result)

    return None


# ============================================================
# AI FUNCTION CALL
# ============================================================

def execute_function_call(function_call):

    action = function_call.name

    try:
        arguments = json.loads(
            function_call.arguments
        )
    except Exception:
        arguments = {}

    print(f"NEXIS ACTION: {action}")
    print(f"NEXIS ARGS: {arguments}")

    result = run_action(
        action,
        arguments
    )

    return {
        "type": "function_call_output",
        "call_id": function_call.call_id,
        "output": str(result)
    }


# ============================================================
# AI REQUEST
# ============================================================

def ask_ai(prompt):

    global last_application

    if not prompt:
        return "I didn't receive a question, sir."

    try:

        # ====================================================
        # DIRECT COMPUTER COMMANDS
        # ====================================================

        direct_result = handle_direct_computer_command(
            prompt
        )

        if direct_result is not None:

            add_message(
                "user",
                prompt
            )

            add_message(
                "assistant",
                direct_result
            )

            return direct_result

        # ====================================================
        # MEMORY
        # ====================================================

        history = get_history()

        input_messages = []

        for message in history:

            input_messages.append({
                "role": message["role"],
                "content": message["content"]
            })

        input_messages.append({
            "role": "user",
            "content": prompt
        })

        # ====================================================
        # AI REQUEST
        # ====================================================

        response = client.responses.create(

            model="gpt-5.6-luna",

            instructions=SYSTEM_PROMPT,

            tools=[
                {
                    "type": "web_search"
                },
                *FUNCTION_TOOLS
            ],

            input=input_messages
        )

        # ====================================================
        # FUNCTION CALLS
        # ====================================================

        function_outputs = []

        for item in response.output:

            if item.type == "function_call":

                function_output = execute_function_call(
                    item
                )

                function_outputs.append(
                    function_output
                )

                # Remember application used by AI.
                try:

                    args = json.loads(
                        item.arguments
                    )

                    if "application" in args:

                        last_application = (
                            args["application"]
                        )

                except Exception:
                    pass

        # ====================================================
        # TOOL FOLLOW-UP
        # ====================================================

        if function_outputs:

            follow_up_input = [
                *input_messages,
                *response.output,
                *function_outputs
            ]

            final_response = client.responses.create(

                model="gpt-5.6-luna",

                instructions=SYSTEM_PROMPT,

                tools=[
                    {
                        "type": "web_search"
                    },
                    *FUNCTION_TOOLS
                ],

                input=follow_up_input
            )

            answer = (
                final_response.output_text.strip()
            )

        else:

            answer = response.output_text.strip()

        # ====================================================
        # MEMORY
        # ====================================================

        add_message(
            "user",
            prompt
        )

        add_message(
            "assistant",
            answer
        )

        return answer

    except Exception as error:

        print(
            f"NEXIS AI ERROR: {error}"
        )

        return (
            "I'm having trouble reaching my intelligence "
            "and computer systems, sir."
        )


# ============================================================
# DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("NEXIS AI TEST")
    print("=" * 60)

    while True:

        try:

            user_input = input(
                "\nYOU: "
            ).strip()

            if user_input.lower() in {
                "exit",
                "quit",
                "shutdown"
            }:

                print(
                    "NEXIS: Standing by, sir."
                )

                break

            answer = ask_ai(
                user_input
            )

            print(
                f"NEXIS: {answer}"
            )

        except KeyboardInterrupt:

            print(
                "\nNEXIS: Standing by, sir."
            )

            break