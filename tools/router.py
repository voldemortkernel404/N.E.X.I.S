"""
NEXIS - Action Router

Central gateway between the AI brain and local system tools.
"""

from tools.actions import execute_action


def run_action(action, arguments=None):
    """
    Execute a NEXIS action.

    Parameters:
        action (str): Action name.
        arguments (dict): Arguments for the action.

    Returns:
        Result returned by the action.
    """

    if not action:
        return "No action specified."

    if arguments is None:
        arguments = {}

    try:
        return execute_action(action, arguments)

    except Exception as error:
        return f"NEXIS action error: {error}"


if __name__ == "__main__":
    print("=" * 50)
    print("NEXIS ACTION ROUTER TEST")
    print("=" * 50)

    print("\nSystem:")
    print(run_action("system_info"))

    print("\nSpotify:")
    print(run_action(
        "find_process",
        {"name": "spotify.exe"}
    ))