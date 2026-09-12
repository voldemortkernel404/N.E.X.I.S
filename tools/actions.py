"""
NEXIS - Action Execution Layer
"""

from tools.system import (
    get_system_info,
    list_files,
    open_application,
    open_url,
    read_file,
    write_file,
    find_applications,
    launch_application,
)

from tools.process import (
    list_processes,
    find_process,
    terminate_process,
    start_process,
)


def execute_action(action, arguments=None):
    """
    Execute a NEXIS system action.

    Returns a clean result that can be passed back
    to the AI/voice layer.
    """

    arguments = arguments or {}

    action = str(action).strip().lower()

    # ========================================================
    # SYSTEM
    # ========================================================

    if action == "system_info":

        return get_system_info()

    # ========================================================
    # FILES
    # ========================================================

    if action == "list_files":

        return list_files(
            arguments.get("path", ".")
        )

    if action == "read_file":

        return read_file(
            arguments.get("path", "")
        )

    if action == "write_file":

        return write_file(
            arguments.get("path", ""),
            arguments.get("content", "")
        )

    # ========================================================
    # APPLICATIONS
    # ========================================================

    if action in (
        "open_application",
        "launch_application",
    ):

        application = arguments.get(
            "application",
            ""
        )

        if not application:
            return "No application was specified, sir."

        return launch_application(
            application
        )

    if action == "find_applications":

        return find_applications()

    # ========================================================
    # WEB
    # ========================================================

    if action == "open_url":

        return open_url(
            arguments.get("url", "")
        )

    # ========================================================
    # PROCESSES
    # ========================================================

    if action == "list_processes":

        return list_processes()

    if action == "find_process":

        name = arguments.get(
            "name",
            ""
        )

        if not name:
            return "No process name was specified, sir."

        return find_process(name)

    if action == "terminate_process":

        name = arguments.get(
            "name",
            ""
        )

        if not name:
            return "No process name was specified, sir."

        return terminate_process(name)

    if action == "start_process":

        command = arguments.get(
            "command",
            ""
        )

        if not command:
            return "No process command was specified, sir."

        return start_process(command)

    # ========================================================
    # UNKNOWN ACTION
    # ========================================================

    return f"Unknown NEXIS action: {action}"