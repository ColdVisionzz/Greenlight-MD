"""
graph.py - Graph visualization screen for Greenlight MD.

Implements a force-directed graph layout to visualize notes as nodes and links
as edges. Provides an interactive curses UI where the user can:
- View relative importance of notes based on incoming/outgoing degree.
- Navigate with arrow keys and focus node under cursor.
- Jump into linked notes via CTRL+G.
"""

import curses
import math
import random

from .themes import init_colors
from .editor import editing_screen
from .link_utils import build_note_graph, build_incoming_links

def force_layout(graph, width, height, iterations=200):
    """Force-directed layout tuned for clustering."""
    # Assign random initial positions within screen bounds
    positions = {
        note: [random.randint(1, width - 2), random.randint(1, height - 3)]
        for note in graph
    }

    # Ideal distance between nodes (based on screen area and graph size)
    k = math.sqrt((width * height) / (len(graph) + 1))

    for _ in range(iterations):
        # Track displacement vectors for each node
        disp = {note: [0, 0] for note in graph}

        # Repulsion forces (all nodes push each other apart)
        min_dist = 2.0
        for v in graph:
            for u in graph:
                if u != v:
                    dx = positions[v][0] - positions[u][0]
                    dy = positions[v][1] - positions[u][1]
                    dist = math.sqrt(dx * dx + dy * dy) + 0.01

                    # Stronger correction if nodes overlap/too close
                    if dist < min_dist:
                        force = 5.0 * (min_dist - dist)
                    else:
                        force = 0.02 * (k * k) / dist

                    disp[v][0] += (dx / dist) * force
                    disp[v][1] += (dy / dist) * force

        # Attraction forces (connected nodes pull toward each other)
        for v, targets in graph.items():
            for u in targets:
                if u in graph:
                    dx = positions[v][0] - positions[u][0]
                    dy = positions[v][1] - positions[u][1]
                    dist = math.sqrt(dx * dx + dy * dy) + 0.01
                    force = 1.0 * (dist * dist) / k

                    # Pull v and u towards each other
                    disp[v][0] -= (dx / dist) * force
                    disp[v][1] -= (dy / dist) * force
                    disp[u][0] += (dx / dist) * force
                    disp[u][1] += (dy / dist) * force

        # Apply displacements and clamp positions to screen area
        for v in graph:
            dx, dy = disp[v]
            dist = math.sqrt(dx * dx + dy * dy)
            if dist > 0:
                positions[v][0] += (dx / dist)
                positions[v][1] += (dy / dist)

            # Ensure positions stay inside the drawable screen region
            positions[v][0] = min(width - 2, max(1, positions[v][0]))
            positions[v][1] = min(height - 3, max(1, positions[v][1]))

    # Round coordinates to integers for display
    return {note: (int(x), int(y)) for note, (x, y) in positions.items()}


def graph_view_screen(
    stdscr,
    root_dir,
    theme="green",
    graph=None,
    paths=None,
    incoming=None,
    positions=None,
):
    """Graph view screen. Can accept precomputed graph/incoming/positions."""
    curses.curs_set(1)
    stdscr.keypad(True)
    init_colors(theme)

    # Build graph and incoming-links map if not provided
    if graph is None or paths is None:
        graph, paths = build_note_graph(root_dir)
    if incoming is None:
        incoming = build_incoming_links(graph)

    # Node importance measured by total degree (out + in links)
    degrees = {note: len(graph[note]) + len(incoming[note]) for note in graph}
    max_deg = max(degrees.values()) if degrees else 1  # avoid div by zero

    height, width = stdscr.getmaxyx()
    if positions is None:
        positions = force_layout(graph, width, height)

    # Cursor starts at center of screen
    cursor_x, cursor_y = width // 2, height // 2

    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()

        # --- Draw all graph nodes ---
        # Symbol reflects note importance (relative degree)
        for note, (x, y) in positions.items():
            deg = degrees[note]
            importance = deg / max_deg if max_deg > 0 else 0

            if importance > 0.66:      # top third
                symbol = "◉"
            elif importance > 0.45:    # upper-mid third
                symbol = "◎"
            elif importance > 0.25:    # lower-mid third
                symbol = "o"
            else:                      # bottom third
                symbol = "·"

            try:
                stdscr.addstr(y, x, symbol, curses.color_pair(1))
            except curses.error:
                # Ignore drawing errors when node lands outside screen
                pass

        # Highlight node under cursor (if any)
        current_note = None
        for note, (x, y) in positions.items():
            if cursor_x == x and cursor_y == y:
                current_note = note
                stdscr.addstr(y, x, "◎", curses.color_pair(1) | curses.A_REVERSE)

        # --- Status bar (left and right segments) ---
        left = f"    {root_dir}"
        drawn = set((int(x), int(y)) for x, y in positions.values())
        if current_note:
            left += f"    |    Go to: [[{current_note}]]"

            out_count = len(graph[current_note])
            in_count = len(incoming[current_note])
            right = f"Outgoing: {out_count}  Incoming: {in_count}    |    {len(graph)} Notes, {len(drawn)} Visible    "
        else:
            right = f"{len(graph)} Notes, {len(drawn)} Visible    "

        status = left + right.rjust(width - len(left) - 1)
        stdscr.addstr(
            height - 1,
            0,
            status[: width - 1],
            curses.color_pair(1) | curses.A_REVERSE,
        )

        # Draw cursor
        stdscr.move(cursor_y, cursor_x)
        stdscr.refresh()

        # --- Handle keys ---
        key = stdscr.getch()
        if key == 17:  # CTRL+Q → quit graph view
            break
        elif key == curses.KEY_UP and cursor_y > 0:
            cursor_y -= 1
        elif key == curses.KEY_DOWN and cursor_y < height - 2:
            cursor_y += 1
        elif key == curses.KEY_LEFT and cursor_x > 0:
            cursor_x -= 1
        elif key == curses.KEY_RIGHT and cursor_x < width - 1:
            cursor_x += 1
        elif key == 7 and current_note:  # CTRL+G → jump to note under cursor
            if current_note in paths:
                target_file = paths[current_note]
                editing_screen(stdscr, target_file, theme, root_dir)