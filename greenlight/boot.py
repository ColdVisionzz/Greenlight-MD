"""
boot.py - Bootup screen and pre-launching logic for Greenlight MD.

Handles loading animations, ASCII splash art, tooltips, and precomputing data
for different modes (editor, link tree, link graph) before handing control to
the main screen. Provides a retro boot UX with randomized startup messages.
"""

import curses
import time
import random

from concurrent.futures import ThreadPoolExecutor
from .themes import init_colors
from .editor import editing_screen
from .link_utils import build_note_graph, build_incoming_links
from .graph import graph_view_screen, force_layout
from .links import link_tree_screen

# User-facing tooltip strings shown randomly on the bootup screen
tooltips = [
    "Despite everything, it's still you.",
    "Now in 7 Colors!",
    "what if there was a secret color?",
    "CTRL + S to save your progress!",
    "Wanna know why it's called greenlight markdown?",
    "Wanna know how I got these graphs?",
    "They shouldn't have greenlit this stupid app.",
    "Shout out KanjiDev's PhoSimp!",
    "CTRL + Q to quit... or ALT + F4 works too...",
    "Noteapp walked so Greenlight MD could run.",
    "Purple is the dev choice.",
    "CTRL + G to GO because CTRL + J for JUMP was taken.",
    "I'm in the mainframe.",
    "The mainframe is in me.",
    "Screw Obsidian!!!",
    "Obsidian charges you for sync. I back up all your notes on floppy disks for free.",
    "Is your vault encrypted? No. But it's protected by a magic spell.",
    "I can't sleep, I'm having cold visions.",
    "pip install greenlight",
    "In a hurry? You can mash through tips with SPACE.",
    "Look at these graphs. Every time I do it makes me laugh.",
    "Reconnect with nature. Look at a link tree!",
    "Support your local underground!",
    "Ay man, hook a brother up with some old school!",
    "You should totally read the README or something...",
    "Now the shortcuts make 10% more linguistic sense!",
    "As seen on Reddit!",
    "It's Greenlight MD because it went to medical school.",
    "No more micromanaging dwarves in the link graph!",
    "Remember - Going to a link is always faster than reloading.",
    "If only there was more time to read these tooltips!",
    "Probably works on the Commadore!",
    "Cold Visions was able to build this in a weekend! With a box of scraps!",
    "This would have been crazy at the 1979 software expo!",
    "Jump to links, your changes aren't going anywhere.",
    "Purple console, easter bunny, I'm in Philly, Always Sunny.",
    "Help my soul is trapped in the terminal!",
    "Making markdown insufferable since 2025!",
    "Confused? --help or -h will sort you out!",
    "You REALLY don't want to know why it's called Greenlight.",
    "No secrets here!",
    "The --help flag is always there if you ever get lost!",
    "It was once called geekMD"
]
# ASCII art banner drawn on sufficiently large screens
ascii_lines = [
    "  ________________________________________ _______  .____    .___  ________  ___ ______________",
    " /  _____/\\______   \\_   _____/\\_   _____/ \\      \\ |    |   |   |/  _____/ /   |   \\__    ___/",
    "/   \\  ___ |       _/|    __)_  |    __)_  /   |   \\|    |   |   /   \\  ___/    ~    \\|    |   ",
    "\\    \\_\\  \\|    |   \\|        \\ |        \\/    |    \\    |___|   \\    \\_\\  \\    Y    /|    |   ",
    " \\______  /|____|_  /_______  //_______  /\\____|__  /_______ \\___|\\______  /\\___|_  / |____|   ",
    "        \\/        \\/        \\/         \\/         \\/        \\/           \\/       \\/           ",
    "       _____      _____ __________ ____  __.________   ________  __      _________             ",
    "      /     \\    /  _  \\\\______   \\    |/ _|\\______ \\  \\_____  \\/  \\    /  \\      \\            ",
    "     /  \\ /  \\  /  /_\\  \\|       _/      <   |    |  \\  /   |   \\   \\/\\/   /   |   \\           ",
    "    /    Y    \\/    |    \\    |   \\    |  \\  |    `   \\/    |    \\        /    |    \\          ",
    "    \\____|__  /\\____|__  /____|_  /____|__ \\/_______  /\\_______  /\\__/\\  /\\____|__  /          ",
    "            \\/         \\/       \\/        \\/        \\/         \\/      \\/         \\/           ",
]

def precompute_for_mode(mode, args, screen_size):
    # Run mode-specific precomputation before launching the interactive screen
    if mode == "edit":
        full_path, vault_root, theme = args
        return ("edit", (full_path, theme, vault_root))
    elif mode == "link-tree":
        root_dir, theme, sort = args
        graph, paths = build_note_graph(root_dir)
        incoming = build_incoming_links(graph)
        return ("link-tree", (root_dir, sort, theme, graph, paths, incoming))
    elif mode == "link-graph":
        root_dir, theme = args
        graph, paths = build_note_graph(root_dir)
        incoming = build_incoming_links(graph)
        height, width = screen_size
        # Precompute node layout so loading feels smooth
        positions = force_layout(graph, width, height)
        return ("link-graph", (root_dir, theme, graph, paths, incoming, positions))
    else:
        raise ValueError(f"Unknown mode: {mode}")

def bootup_screen(stdscr, mode, args, theme):
    stdscr.erase()
    stdscr.clear()
    curses.curs_set(0)
    init_colors(theme)

    height, width = stdscr.getmaxyx()
    tip_of_the_day = random.choice(tooltips)

    # Make input non-blocking so we can display animation while checking keys
    stdscr.nodelay(True)

    # Perform background precomputation in a separate thread
    with ThreadPoolExecutor() as executor:
        future = executor.submit(precompute_for_mode, mode, args, (height, width))

        dot_amount = 0
        start_time = time.time()
        min_duration = 3.0  # Enforce min boot screen time for visual effect

        # Stay in loading loop until precomputation is done *and* min time passed
        while not future.done() or (time.time() - start_time < min_duration):
            stdscr.erase()

            # Draw ASCII art and tooltip if screen has enough room
            if height >= 15 and width >= 80:
                for i, line in enumerate(ascii_lines):
                    stdscr.addstr(i, 0, line[:width - 1], curses.color_pair(1))
                stdscr.addstr(
                    len(ascii_lines) + 1, 0, tip_of_the_day[:width - 1], curses.color_pair(1)
                )
                loading_y = len(ascii_lines) + 2
            else:
                # Fallback for smaller terminals: show just tooltip and loading text
                stdscr.addstr(1, 0, tip_of_the_day[:width - 1], curses.color_pair(1))
                loading_y = 2

            # Mode-specific loading label
            if mode == "edit":
                loading_label = "Loading Editor"
            elif mode == "link-tree":
                loading_label = "Loading Link Tree"
            elif mode == "link-graph":
                loading_label = "Loading Graph"
            else:
                loading_label = "Loading"

            # Draw loading message with animated dots
            loading_status = loading_label + ("." * dot_amount)
            stdscr.addstr(
                loading_y, 0, (loading_status + "   ")[:width - 1], curses.color_pair(1)
            )
            stdscr.refresh()

            # Allow user to press spacebar to cycle tooltip
            key = stdscr.getch()
            if key == 32:  # spacebar
                tip_of_the_day = random.choice(tooltips)

                # Instantly redraw with new tip
                stdscr.erase()
                if height >= 15 and width >= 80:
                    for i, line in enumerate(ascii_lines):
                        stdscr.addstr(i, 0, line[:width - 1], curses.color_pair(1))
                    stdscr.addstr(
                        len(ascii_lines) + 1, 0, tip_of_the_day[:width - 1], curses.color_pair(1)
                    )
                    loading_y = len(ascii_lines) + 2
                else:
                    stdscr.addstr(1, 0, tip_of_the_day[:width - 1], curses.color_pair(1))
                    loading_y = 2

                stdscr.addstr(
                    loading_y, 0, (loading_status + "   ")[:width - 1], curses.color_pair(1)
                )
                stdscr.refresh()

                # Flush input buffer so repeated space presses don’t queue up
                while True:
                    flush_key = stdscr.getch()
                    if flush_key == -1:
                        break

            time.sleep(0.25)
            dot_amount = (dot_amount + 1) % 4

        # Finished precomputation → retrieve results
        mode, result = future.result()

    # Re-enable blocking input for interactive screens
    stdscr.nodelay(False)

    # Launch appropriate mode screen with precomputed data
    if mode == "edit":
        full_path, theme, vault_root = result
        editing_screen(stdscr, full_path, theme, vault_root)

    elif mode == "link-tree":
        root_dir, sort, theme, graph, paths, incoming = result
        link_tree_screen(
            stdscr,
            root_dir,
            sort=sort,
            theme=theme,
            graph=graph,
            paths=paths,
            incoming=incoming,
        )

    elif mode == "link-graph":
        root_dir, theme, graph, paths, incoming, positions = result
        graph_view_screen(
            stdscr,
            root_dir,
            theme=theme,
            graph=graph,
            paths=paths,
            incoming=incoming,
            positions=positions,
        )