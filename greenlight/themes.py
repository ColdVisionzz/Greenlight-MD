"""
themes.py - Theme and color handling for Greenlight MD.

Provides:
- A set of predefined color themes (green, purple, cyan, blue, yellow, white, red).
- Logic to resolve "random" into a concrete theme.
- `init_colors()` to configure curses color pairs used across the app.
"""

import curses
import random

# All supported theme names
AVAILABLE_THEMES = ["green", "purple", "cyan", "blue", "yellow", "white", "red"]

def resolve_theme(theme: str) -> str:
    """Resolve 'random' theme into a specific choice from AVAILABLE_THEMES."""
    if theme == "random":
        # Pick a random theme name if user requested randomness
        return random.choice(AVAILABLE_THEMES)
    return theme

def init_colors(theme: str):
    # Initialize curses color subsystem and enable transparency with default terminal colors
    curses.start_color()
    curses.use_default_colors()

    # Default fallback pairs (will be overridden if a recognized theme is selected)
    # Pair 1 is always "primary text"; Pair 2 is "highlight (links)"
    curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)

    # Apply theme-specific overrides
    if theme == "green":
        curses.init_pair(1, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
    elif theme == "purple":
        curses.init_pair(1, curses.COLOR_MAGENTA, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
    elif theme == "cyan":
        curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
    elif theme == "blue":
        curses.init_pair(1, curses.COLOR_BLUE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_WHITE, curses.COLOR_BLACK)
    elif theme == "yellow":
        curses.init_pair(1, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    elif theme == "white":
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_CYAN, curses.COLOR_BLACK)
    elif theme == "red":
        curses.init_pair(1, curses.COLOR_RED, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_BLUE, curses.COLOR_BLACK)