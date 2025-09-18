"""
editor.py - Core markdown editor screen for Greenlight MD.

Implements a curses-based text editor with the following features:
- Markdown note editing with [[Link]] detection and highlighting.
- Navigation with arrow keys, Enter, Backspace, Tab, etc.
- Saving via CTRL+S and quitting with CTRL+Q.
- Jumping directly to linked notes with CTRL+G, creating new notes if missing.
- Status bar showing file path, save state, and cursor position.
"""

import curses
import time
import os

from .themes import init_colors
from .link_utils import build_note_graph, link_pattern

extension = ".md"

def editing_screen(stdscr, file_path, theme, vault_root):
    curses.curs_set(1)
    stdscr.keypad(True)
    init_colors(theme)

    save_status = True
    last_saved_time = None

    # Load file contents into buffer, or create new buffer if file doesn't exist
    try:
        with open(file_path, "r") as f:
            buffer = f.read().splitlines()
    except FileNotFoundError:
        buffer = []

    if not buffer:
        buffer = [""]

    # Build note link graph for navigation
    graph, paths = build_note_graph(vault_root)

    # Cursor positions and viewport offset
    y, x = 0, 0
    offset = 0
    stdscr.timeout(1000)  # allow idle timeouts for saved status refresh

    while True:
        stdscr.erase()
        height, width = stdscr.getmaxyx()
        links_on_screen = []

        # Render visible lines of buffer, highlighting links
        visible_lines = buffer[offset:offset + height - 1]
        for row, line in enumerate(visible_lines):
            last_idx = 0
            for match in link_pattern.finditer(line):
                start, end = match.span()

                # Track link positions for cursor detection
                links_on_screen.append({
                    "note": match.group(1),
                    "y": row + offset,
                    "x_start": start,
                    "x_end": end
                })

                # Draw plain text before the link
                if start > last_idx:
                    stdscr.addstr(
                        row,
                        last_idx,
                        line[last_idx:start][:max(0, width - last_idx - 1)],
                        curses.color_pair(1)
                    )

                # Draw the link itself highlighted
                stdscr.addstr(
                    row,
                    start,
                    line[start:end][:max(0, width - start - 1)],
                    curses.color_pair(2)
                )

                # Update cursor baseline beyond this link
                last_idx = end

            # Draw remainder of line after last link
            if last_idx < len(line):
                stdscr.addstr(
                    row,
                    last_idx,
                    line[last_idx:][:max(0, width - last_idx - 1)],
                    curses.color_pair(1)
                )

        # Status bar
        current_link = None
        for link in links_on_screen:
            # If cursor is over a link, store it
            if y == link["y"] and link["x_start"] <= x < link["x_end"]:
                current_link = link
                break

        left = f"    {file_path}"
        if current_link:
            left += f"    |    Go to: [[{current_link['note']}]]"

        # Right side varies based on save state and recent activity
        if not save_status:
            right = f"[Unsaved]    |    Line {y + 1}, Col {x + 1}    "
        elif last_saved_time and time.time() - last_saved_time < 3:
            right = f"[Progress Saved]    |    Line {y + 1}, Col {x + 1}    "
        else:
            right = f"Line {y + 1}, Col {x + 1}    "

        status = left + right.rjust(width - len(left) - 1)
        stdscr.addstr(
            height - 1,
            0,
            status.rjust(width - 1),
            curses.color_pair(1) | curses.A_REVERSE,
        )

        # Move visual cursor based on logical y,x (with scroll offset applied)
        screen_y = y - offset
        screen_x = x
        if 0 <= screen_y < height - 1 and 0 <= screen_x < width - 1:
            stdscr.move(screen_y, screen_x)
        stdscr.refresh()

        # Input handling
        key = stdscr.getch()
        if key == -1:
            continue
        if key == 17:  # CTRL+Q
            break
        elif key == 19:  # CTRL+S
            # Save buffer content back to file
            save_status = True
            with open(file_path, "w") as f:
                f.write("\n".join(buffer))
            last_saved_time = time.time()
        elif key == 7 and current_link:  # CTRL+G (go to linked note)
            note_name = current_link["note"]
            if note_name in paths:
                # Open existing linked file
                target_file = paths[note_name]
                editing_screen(stdscr, target_file, theme, vault_root)
            else:
                # If missing, create a new note file and recurse into editor
                target_file = os.path.join(vault_root, note_name + extension)
                with open(target_file, "w") as f:
                    f.write("")
                editing_screen(stdscr, target_file, theme, vault_root)
        elif key in (10, 13):  # Enter → split line
            save_status = False
            current_line = buffer[y]
            buffer[y] = current_line[:x]
            buffer.insert(y + 1, current_line[x:])
            y += 1
            x = 0
        elif key == 9:  # TAB → insert indentation
            save_status = False
            buffer[y] = buffer[y][:x] + "    " + buffer[y][x:]
            x += 4
        elif key in (curses.KEY_BACKSPACE, 127, 8):
            # Handle backspace across line breaks
            save_status = False
            if x > 0:
                buffer[y] = buffer[y][:x - 1] + buffer[y][x:]
                x -= 1
            elif y > 0:
                prev_len = len(buffer[y - 1])
                buffer[y - 1] += buffer[y]
                buffer.pop(y)
                y -= 1
                x = prev_len
        elif key == curses.KEY_LEFT:
            if x > 0:
                x -= 1
            elif y > 0:
                # At start of line → wrap to end of previous line
                y -= 1
                x = len(buffer[y])
        elif key == curses.KEY_RIGHT:
            if x < len(buffer[y]):
                x += 1
            elif y < len(buffer) - 1:
                # At end of line → wrap to start of next line
                y += 1
                x = 0
        elif key == curses.KEY_UP:
            if y > 0:
                y -= 1
                # Align cursor x with shorter lines
                x = min(x, len(buffer[y]))
            else:
                # At top line → snap to column 0
                x = 0
        elif key == curses.KEY_DOWN:
            if y < len(buffer) - 1:
                y += 1
                # Prevent cursor from exceeding line length
                x = min(x, len(buffer[y]))
            else:
                # At bottom line → snap to end of line
                x = len(buffer[y])
        elif 32 <= key <= 126:
            # Insert printable characters
            save_status = False
            buffer[y] = buffer[y][:x] + chr(key) + buffer[y][x:]
            x += 1

        # Always adjust scroll offset after cursor movement
        if y < offset:
            offset = y
        elif y >= offset + (height - 2):
            offset = y - (height - 2)