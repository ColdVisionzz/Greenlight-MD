"""
helper.py - Help screen for Greenlight MD.

Displays usage instructions, keybinds, and tips inside a scrollable curses UI.
Exposes a `help_screen()` function that presents a static guide with navigation
keys:
- Arrow keys to scroll up/down
- CTRL+Q to quit help screen
"""

import curses
from greenlight.themes import init_colors

HELP_TEXT = """
Greenlight MD - Retro Markdown editor with Obsidian-style linking
=================================================================

Usage:
  greenlight <directory> <filename> [--theme <name>]
  greenlight <directory> --link-tree [-a|-q] [--theme <name>]
  greenlight <directory> --link-graph [--theme <name>]
  greenlight -h | --help

Modes:
  (default)        Edits a note
  --link-tree      Show incoming/outgoing links for all notes in directory
  --link-graph     Visualize notes as a graph
  -h, --help       Show this help screen

Options:
  --theme <name>   Set color theme (green, purple, cyan, blue, yellow, white, red, random)
  -a               Sort link tree alphabetically
  -q               Sort link tree by quantity of links

Keybinds:
  CTRL+S   Save
  CTRL+Q   Quit
  CTRL+G   Go to linked note

Tips:
  - Use [[NoteName]] to link between notes
  - Boot screen tips can be shuffled with SPACE
  - Themes can be randomized with --theme random

Greenlight MD v0.1.0
Created by Cold Visions, 2025
-
"""

def help_screen(stdscr, theme):
    # Initialize curses screen state for help display
    curses.curs_set(0)       # Hide blinking cursor in help UI
    stdscr.keypad(True)      # Enable arrow key handling
    init_colors(theme)       # Apply theme-based color scheme

    height, width = stdscr.getmaxyx()
    lines = HELP_TEXT.strip().splitlines()  # Pre-split static help text into lines

    offset = 0  # vertical scroll offset
    while True:
        stdscr.erase()
        # Select the currently visible slice of lines to render
        visible = lines[offset:offset + height - 1]

        for row, line in enumerate(visible):
            # Render each line within the visible window
            stdscr.addstr(row, 0, line[:width - 1], curses.color_pair(1))

        # Draw status bar at bottom indicating quit option
        stdscr.addstr(
            height - 1,
            0,
            "    CTRL + Q to Quit".ljust(width - 1),
            curses.color_pair(1) | curses.A_REVERSE,
        )
        stdscr.refresh()

        key = stdscr.getch()
        if key == 17:
            # CTRL+Q → exit help screen
            break
        elif key == curses.KEY_UP and offset > 0:
            # Scroll upward if possible
            offset -= 1
        elif key == curses.KEY_DOWN and offset < len(lines) - height:
            # Scroll downward if more content is available
            offset += 1