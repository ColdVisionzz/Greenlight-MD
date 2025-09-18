"""
links.py - Link tree view screen for Greenlight MD.

Displays a hierarchical tree of notes and their incoming/outgoing links.
Features:
- Optional sorting by alphabetical (-a) or by link quantity (-q).
- Highlight and navigation across [[links]].
- Jump to target note with CTRL+G.
"""

import curses

from .editor import editing_screen
from .themes import init_colors
from .link_utils import build_note_graph, build_incoming_links, link_pattern

def link_tree_screen(
    stdscr,
    root_dir,
    sort=None,
    theme="green",
    graph=None,
    paths=None,
    incoming=None,
):

    curses.curs_set(1)
    stdscr.keypad(True)
    init_colors(theme)

    # Compute graph and incoming links if they were not passed in
    if graph is None or paths is None:
        graph, paths = build_note_graph(root_dir)
    if incoming is None:
        incoming = build_incoming_links(graph)

    # Collect and optionally sort the note list
    notes = list(graph.keys())
    if sort == "alpha":
        notes = sorted(notes, key=str.lower)
    elif sort == "quantity":
        # Sort by total number of links (incoming + outgoing)
        notes = sorted(
            notes,
            key=lambda n: len(graph[n]) + len(incoming.get(n, [])),
            reverse=True,
        )

    # Build a flattened list of lines to display (notes + incoming/outgoing info)
    lines = []
    for note in notes:
        lines.append(note)

        # Prepare list of incoming notes
        inc = incoming.get(note, [])
        if sort == "alpha":
            inc = sorted(inc, key=str.lower)
        elif sort == "quantity":
            inc = sorted(inc, key=lambda x: len(graph.get(x, [])), reverse=True)

        lines.append(f"  Incoming ({len(inc)})")
        for src in inc:
            lines.append(f"    <- [[{src}]]")

        # Prepare list of outgoing notes
        out = graph[note]
        if sort == "alpha":
            out = sorted(out, key=str.lower)
        elif sort == "quantity":
            out = sorted(out, key=lambda x: len(graph.get(x, [])), reverse=True)

        lines.append(f"  Outgoing ({len(out)})")
        for tgt in out:
            lines.append(f"    -> [[{tgt}]]")

        lines.append("")  # blank line for spacing between notes

    # Cursor state (relative position in view)
    cursor_y, cursor_x = 0, 0
    offset = 0  # vertical scroll offset

    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        links_on_screen = []  # track link spans for hit detection

        # Slice visible lines based on terminal height
        visible = lines[offset : offset + height - 1]

        # Draw lines with inline highlighting of [[links]]
        for row, line in enumerate(visible):
            col = 0
            for match in link_pattern.finditer(line):
                start, end = match.span()
                note_name = match.group(1)
                links_on_screen.append(
                    {
                        "note": note_name,
                        "screen_y": row,
                        "x_start": start,
                        "x_end": end,
                    }
                )
                stdscr.addstr(row, col, line[col:start], curses.color_pair(1))
                stdscr.addstr(row, start, line[start:end], curses.color_pair(2))
                col = end
            if col < len(line):
                stdscr.addstr(row, col, line[col:], curses.color_pair(1))

        # Status bar (shows vault path, current link, and sort mode)
        current_link = None
        for link in links_on_screen:
            if (
                link["screen_y"] == cursor_y
                and link["x_start"] <= cursor_x < link["x_end"]
            ):
                current_link = link
                break

        left = f"    {root_dir}"
        middle = f"    |    Go to: [[{current_link['note']}]]" if current_link else ""
        right = f"Sort: {sort or 'none'}    "

        status = left + middle + right.rjust(width - len(left) - len(middle) - 1)
        stdscr.addstr(
            height - 1,
            0,
            status[: width - 1],
            curses.color_pair(1) | curses.A_REVERSE,
        )

        # Clamp cursor to visible window bounds
        if cursor_y >= len(visible):
            cursor_y = len(visible) - 1
        if cursor_x >= width:
            cursor_x = width - 1

        stdscr.move(cursor_y, cursor_x)
        stdscr.refresh()

        # --- Input handling ---
        key = stdscr.getch()
        if key == 17:  # CTRL+Q → quit
            break
        elif key == curses.KEY_UP:
            if cursor_y > 0:
                cursor_y -= 1
            elif offset > 0:
                offset -= 1
            else:
                cursor_x = 0  # snap to column 0 at top edge
        elif key == curses.KEY_DOWN:
            if cursor_y < len(visible) - 1:
                cursor_y += 1
            elif offset < len(lines) - (height - 1):
                offset += 1
            else:
                if visible:
                    cursor_x = len(visible[-1])  # snap to end at bottom edge
        elif key == curses.KEY_LEFT and cursor_x > 0:
            cursor_x -= 1
        elif key == curses.KEY_RIGHT and cursor_x < width - 1:
            cursor_x += 1
        elif key == 7:  # CTRL+G → follow link under cursor
            for link in links_on_screen:
                if (
                    link["screen_y"] == cursor_y
                    and link["x_start"] <= cursor_x < link["x_end"]
                ):
                    note_name = link["note"]
                    if note_name in paths:
                        target_file = paths[note_name]
                        editing_screen(stdscr, target_file, theme, root_dir)
                    break