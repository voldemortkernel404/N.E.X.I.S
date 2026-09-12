"""
NEXIS - Windows System Tools

Provides:
- System information
- File listing
- Application discovery
- Application launching
- Process discovery
- Process termination
"""

import os
import subprocess
from pathlib import Path


# ============================================================
# NEXIS ROOT
# ============================================================

NEXIS_ROOT = Path(__file__).resolve().parent.parent


# ============================================================
# SYSTEM INFORMATION
# ============================================================

def get_system_info():
    """Return basic information about the computer."""

    return {
        "computer": os.environ.get("COMPUTERNAME", "Unknown"),
        "user": os.environ.get("USERNAME", "Unknown"),
        "platform": os.name,
        "nexis_root": str(NEXIS_ROOT),
    }


# ============================================================
# FILE SYSTEM
# ============================================================

def list_files(path="."):
    """
    List files and directories.

    Relative paths are resolved from the NEXIS root.
    """

    try:

        requested = Path(path)

        if requested.is_absolute():
            target = requested
        else:
            target = NEXIS_ROOT / requested

        if not target.exists():
            return f"Path not found: {path}"

        if not target.is_dir():
            return f"{path} is not a directory."

        results = []

        for item in sorted(
            target.iterdir(),
            key=lambda x: (not x.is_dir(), x.name.lower())
        ):

            if item.is_dir():
                results.append(f"[DIR]  {item.name}")
            else:
                results.append(f"[FILE] {item.name}")

        return "\n".join(results)

    except Exception as error:

        return f"File listing error: {error}"


# ============================================================
# APPLICATION DISCOVERY
# ============================================================

def find_applications():
    """
    Find applications available through the Windows Start Menu.
    """

    locations = [

        Path(
            os.environ.get("APPDATA", "")
        ) / "Microsoft/Windows/Start Menu/Programs",

        Path(
            os.environ.get("PROGRAMDATA", "")
        ) / "Microsoft/Windows/Start Menu/Programs",

    ]

    applications = {}

    for location in locations:

        if not location.exists():
            continue

        try:

            for item in location.rglob("*.lnk"):

                name = item.stem.strip()

                if name:
                    applications[name.lower()] = {
                        "name": name,
                        "path": str(item),
                    }

        except Exception:
            continue

    # Add common Windows applications.
    builtins = [
        "Calculator",
        "Notepad",
        "Task Manager",
        "File Explorer",
        "Command Prompt",
        "PowerShell",
        "Control Panel",
        "Registry Editor",
        "Character Map",
        "Snipping Tool",
    ]

    for name in builtins:

        key = name.lower()

        if key not in applications:

            applications[key] = {
                "name": name,
                "path": None,
            }

    return sorted(
        applications.values(),
        key=lambda x: x["name"].lower()
    )


# ============================================================
# APPLICATION LAUNCHING
# ============================================================

def launch_application(name):
    """
    Launch a Windows application.

    Uses:
    1. Windows built-in applications
    2. Microsoft Store URI handlers
    3. Start Menu shortcuts
    4. Windows PATH
    """

    requested = str(name).strip().lower()

    if not requested:
        return "You didn't specify an application, sir."

    # --------------------------------------------------------
    # Windows built-in applications
    # --------------------------------------------------------

    aliases = {

        "calculator": "calc.exe",
        "calc": "calc.exe",

        "notepad": "notepad.exe",

        "task manager": "taskmgr.exe",
        "taskmanager": "taskmgr.exe",

        "file explorer": "explorer.exe",
        "explorer": "explorer.exe",

        "command prompt": "cmd.exe",
        "cmd": "cmd.exe",

        "powershell": "powershell.exe",

        "control panel": "control.exe",

        "registry editor": "regedit.exe",

        "character map": "charmap.exe",

        "snipping tool": "SnippingTool.exe",

    }

    if requested in aliases:

        try:

            subprocess.Popen(
                aliases[requested],
                shell=True
            )

            return f"{name} is opening, sir."

        except Exception as error:

            return (
                f"I couldn't open {name}: {error}"
            )

    # --------------------------------------------------------
    # Microsoft Store applications
    # --------------------------------------------------------

    store_apps = {

        "spotify": "spotify:",

    }

    if requested in store_apps:

        try:

            os.startfile(
                store_apps[requested]
            )

            return f"{name} is opening, sir."

        except Exception as error:

            return (
                f"I couldn't open {name}: {error}"
            )

    # --------------------------------------------------------
    # Start Menu shortcuts
    # --------------------------------------------------------

    locations = [

        Path(
            os.environ.get("APPDATA", "")
        ) / "Microsoft/Windows/Start Menu/Programs",

        Path(
            os.environ.get("PROGRAMDATA", "")
        ) / "Microsoft/Windows/Start Menu/Programs",

    ]

    matches = []

    for location in locations:

        if not location.exists():
            continue

        try:

            for item in location.rglob("*.lnk"):

                shortcut_name = item.stem.strip()
                shortcut_lower = shortcut_name.lower()

                if shortcut_lower == requested:

                    matches.append(item)

                elif requested in shortcut_lower:

                    matches.append(item)

                elif shortcut_lower in requested:

                    matches.append(item)

        except Exception:
            continue

    # Remove duplicate shortcuts.
    unique_matches = []

    seen = set()

    for item in matches:

        key = str(item).lower()

        if key not in seen:

            seen.add(key)
            unique_matches.append(item)

    if unique_matches:

        # Prefer the closest/shortest match.
        unique_matches.sort(
            key=lambda x: len(x.stem)
        )

        selected = unique_matches[0]

        try:

            os.startfile(str(selected))

            return (
                f"{selected.stem} is opening, sir."
            )

        except Exception as error:

            return (
                f"I couldn't open {name}: {error}"
            )

    # --------------------------------------------------------
    # Windows PATH
    # --------------------------------------------------------

    try:

        result = subprocess.run(

            ["where", name],

            capture_output=True,

            text=True,

            encoding="utf-8",

            errors="replace",

            shell=False

        )

        if result.returncode == 0:

            executable = (
                result.stdout
                .strip()
                .splitlines()[0]
            )

            subprocess.Popen(
                executable,
                shell=True
            )

            return f"{name} is opening, sir."

    except Exception:
        pass

    # --------------------------------------------------------
    # Not found
    # --------------------------------------------------------

    return (
        f"I couldn't find an installed application "
        f"named {name}, sir."
    )


# ============================================================
# PROCESS DISCOVERY
# ============================================================

def find_process(name):
    """
    Find a running Windows process.
    """

    try:

        result = subprocess.run(

            [
                "tasklist",
                "/FI",
                f"IMAGENAME eq {name}"
            ],

            capture_output=True,

            text=True,

            encoding="utf-8",

            errors="replace",

            shell=False

        )

        output = result.stdout.strip()

        if not output:

            return f"No process named {name} is running."

        if (
            "No tasks are running"
            in output
        ):

            return (
                f"No process named {name} "
                f"is running."
            )

        return output

    except Exception as error:

        return (
            f"Process search error: {error}"
        )


# ============================================================
# LIST ALL PROCESSES
# ============================================================

def list_processes():
    """Return currently running Windows processes."""

    try:

        result = subprocess.run(

            ["tasklist"],

            capture_output=True,

            text=True,

            encoding="utf-8",

            errors="replace",

            shell=False

        )

        return result.stdout.strip()

    except Exception as error:

        return (
            f"Process listing error: {error}"
        )


# ============================================================
# TERMINATE PROCESS
# ============================================================

def terminate_process(name):
    """
    Attempt to terminate a process normally first,
    then report if Windows requires forceful termination.
    """

    try:

        # ----------------------------------------------------
        # First attempt: normal termination
        # ----------------------------------------------------

        result = subprocess.run(

            [
                "taskkill",
                "/IM",
                name
            ],

            capture_output=True,

            text=True,

            encoding="utf-8",

            errors="replace",

            shell=False

        )

        output = (
            result.stdout.strip()
            + "\n"
            + result.stderr.strip()
        ).strip()

        # ----------------------------------------------------
        # Successful termination
        # ----------------------------------------------------

        if result.returncode == 0:

            return (
                f"{name} was closed successfully, sir."
            )

        # ----------------------------------------------------
        # Windows says force termination is required
        # ----------------------------------------------------

        force_required = (
            "requires a forceful termination"
            in output.lower()
            or "force" in output.lower()
            and "child" in output.lower()
        )

        if force_required:

            return {
                "success": False,
                "force_required": True,
                "message": (
                    f"{name} could not be closed normally. "
                    f"Windows requires a forceful termination."
                )
            }

        return {
            "success": False,
            "force_required": False,
            "message": (
                f"{name} could not be terminated. "
                f"{output}"
            )
        }

    except Exception as error:

        return {
            "success": False,
            "force_required": False,
            "message": (
                f"Process termination error: {error}"
            )
        }


# ============================================================
# FORCE TERMINATE PROCESS
# ============================================================

def force_terminate_process(name):
    """
    Forcefully terminate a Windows process and its children.
    """

    try:

        result = subprocess.run(

            [
                "taskkill",
                "/F",
                "/T",
                "/IM",
                name
            ],

            capture_output=True,

            text=True,

            encoding="utf-8",

            errors="replace",

            shell=False

        )

        output = (
            result.stdout.strip()
            + "\n"
            + result.stderr.strip()
        ).strip()

        if result.returncode == 0:

            return (
                f"{name} and its child processes "
                f"were forcefully terminated, sir."
            )

        return (
            f"I couldn't force-close {name}, sir. "
            f"{output}"
        )

    except Exception as error:

        return (
            f"Force termination error: {error}"
        )


# ============================================================
# TEST
# ============================================================

if __name__ == "__main__":

    print("=" * 60)
    print("NEXIS SYSTEM TEST")
    print("=" * 60)

    print("\nSYSTEM:")
    print(get_system_info())

    print("\nAPPLICATIONS:")
    apps = find_applications()

    for app in apps:
        print(app["name"])

    print("\nSPOTIFY:")
    print(find_process("Spotify.exe"))

    print("\nSYSTEM TOOLS READY.")
# Compatibility alias
open_application = launch_application

def open_url(url):
    import webbrowser
    try:
        webbrowser.open(url)
        return f'Opening {url}, sir.'
    except Exception as error:
        return f'I could not open the URL, sir. {error}'

def read_file(path):
    """Read a text file from the NEXIS directory."""

    try:
        target = Path(path)

        if not target.is_absolute():
            target = NEXIS_ROOT / target

        if not target.exists():
            return f"File not found: {path}"

        if not target.is_file():
            return f"{path} is not a file."

        return target.read_text(
            encoding="utf-8",
            errors="replace"
        )

    except Exception as error:
        return f"Could not read {path}: {error}"


def write_file(path, content):
    """Write text to a file inside the NEXIS directory."""

    try:
        target = Path(path)

        if not target.is_absolute():
            target = NEXIS_ROOT / target

        target.parent.mkdir(
            parents=True,
            exist_ok=True
        )

        target.write_text(
            str(content),
            encoding="utf-8"
        )

        return f"File written successfully: {target}"

    except Exception as error:
        return f"Could not write {path}: {error}"
