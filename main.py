import curses
import subprocess
import sys
from editor import Editor


def flow_control(disable: bool = True):
    subprocess.run(["stty", "-ixon" if disable else "ixon"])


if __name__ == "__main__":
    file_name = sys.argv[1] if len(sys.argv) > 1 else None
    if not file_name:
        raise ValueError("No file name provided")
    try:
        flow_control()
        e = Editor(file_name)
        curses.wrapper(e.curser_init)
    finally:
        flow_control(False)
