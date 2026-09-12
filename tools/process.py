"""
NEXIS - Process Controller
"""

import subprocess


def list_processes():
    """Return currently running processes."""

    result = subprocess.run(
        ["tasklist"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if result.returncode != 0:
        return "Unable to retrieve running processes."

    return result.stdout


def find_process(name):
    """Check whether a process is running."""

    result = subprocess.run(
        ["tasklist", "/FI", f"IMAGENAME eq {name}"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    return result.stdout


def terminate_process(name):
    """
    Close a Windows process.

    First attempts a normal termination.
    If Windows requires force termination, retries with /F.
    """

    # First attempt: normal termination
    result = subprocess.run(
        ["taskkill", "/IM", name, "/T"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if result.returncode == 0:
        return f"Process {name} terminated successfully."

    # Second attempt: force termination
    force_result = subprocess.run(
        ["taskkill", "/F", "/IM", name, "/T"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )

    if force_result.returncode == 0:
        return f"Process {name} force-terminated successfully."

    return (
        force_result.stderr.strip()
        or f"Unable to terminate {name}."
    )

def start_process(command):
    """Start a process."""

    try:
        subprocess.Popen(command, shell=True)
        return f"Started: {command}"

    except Exception as error:
        return f"Unable to start process: {error}"