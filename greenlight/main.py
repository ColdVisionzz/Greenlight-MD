"""
main.py - Entry point CLI for Greenlight MD.

Responsible for:
- Parsing command line arguments and determining mode (edit, help, link-tree,
  link-graph).
- Setting theme selection, link tree sorting, and file paths.
- Bootstrapping the curses UI by calling the appropriate screen through
  `bootup_screen()` or `help_screen()`.

Acts as the user-facing entry to launch the application.
"""

import sys
import os
import curses

from greenlight.themes import resolve_theme
from .helper import help_screen
from .boot import bootup_screen

def main_entry():
    # Initialize default configuration values and CLI placeholders
    args = sys.argv[1:]
    mode = "edit"
    theme = "green"
    link_tree_sort = None
    path = None           # vault directory containing notes
    file_name = None      # target note filename (without extension)
    extension = ".md"

    # Parse command line arguments to determine mode, theme, and file paths
    i = 0
    while i < len(args):
        arg = args[i]
        if arg == "--theme":
            # Theme requires a value (e.g., green, purple, random)
            if i + 1 < len(args):
                theme = args[i + 1]
                i += 1
            else:
                print("Error: --theme requires a value")
                sys.exit(1)
        elif arg == "--link-tree":
            mode = "link-tree"
        elif arg == "-h" or arg == "--help":
            mode = "help"
        elif arg == "-a":
            link_tree_sort = "alpha"
        elif arg == "-q":
            link_tree_sort = "quantity"
        elif arg == "--link-graph":
            mode = "link-graph"
        elif path is None:
            # First non-flag argument → treat as vault root directory
            path = arg
        elif file_name is None:
            # Second non-flag argument → treat as target note filename
            file_name = arg
        else:
            # Any extra arguments beyond expected are invalid
            print(f"Unknown argument: {arg}")
            sys.exit(1)
        i += 1

    # Resolve "random" theme option into a concrete theme name
    theme = resolve_theme(theme)

    # Launch the appropriate curses screen depending on the selected mode
    if mode == "edit":
        if not path or not file_name:
            print("Usage: greenlight <directory> <filename>")
            sys.exit(1)
        # Ensure the vault directory exists before writing files
        os.makedirs(path, exist_ok=True)
        # Build full filesystem path to target note
        full_path = os.path.join(path, file_name + extension)
        curses.wrapper(
            lambda stdscr: bootup_screen(
                stdscr, "edit", (full_path, path, theme), theme
            )
        )
    elif mode == "link-tree":
        if not path:
            print("Usage: greenlight <directory> --link-tree [-a|-q]")
            sys.exit(1)
        curses.wrapper(
            lambda stdscr: bootup_screen(
                stdscr, "link-tree", (path, theme, link_tree_sort), theme
            )
        )
    elif mode == "link-graph":
        if not path:
            print("Usage: greenlight <directory> --link-graph")
            sys.exit(1)
        curses.wrapper(
            lambda stdscr: bootup_screen(stdscr, "link-graph", (path, theme), theme)
        )
    elif mode == "help":
        curses.wrapper(
            lambda stdscr: help_screen(stdscr, theme)
        )

if __name__ == "__main__":
    main_entry()