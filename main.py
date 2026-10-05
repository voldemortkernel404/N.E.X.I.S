"""
N.E.X.I.S.
Neural EXecution & Intelligence System

Main application launcher.
The GUI is now the primary interface.
"""

from core.GUI.interface import launch_gui


def main():
    print("=" * 60)
    print("N.E.X.I.S.")
    print("Neural EXecution & Intelligence System")
    print("=" * 60)
    print("NEXIS: Starting GUI...")


if __name__ == "__main__":
    main()
    launch_gui()