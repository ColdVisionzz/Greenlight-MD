"""
graph_utils.py - Utility functions for building note graph structures.

Provides common parsing and construction logic used by multiple screens:
- Regex matching of [[Note]] links inside markdown files.
- Extracting outbound links from a note.
- Building a global graph mapping each note → list of targets.
- Computing incoming link relationships for reverse navigation.
"""

import os
import re

# Pattern that matches [[NoteName]] style links inside markdown text
link_pattern = re.compile(r"\[\[([^\]]+)\]\]")

# Extract all [[links]] from a single markdown file
def extract_links_from_file(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            text = f.read()
    except FileNotFoundError:
        # File missing → return no links
        return []
    # Return only the inner note names (the captured groups from the regex)
    return link_pattern.findall(text)


# Walk through a vault directory and build a note graph + name→path map
def build_note_graph(root_dir):
    graph = {}   # mapping: note_name → list of outbound links
    paths = {}   # mapping: note_name → absolute file path
    for dirpath, _, files in os.walk(root_dir):
        for file in files:
            if file.endswith(".md"):
                name = file[:-3]  # strip extension ".md" to get note title
                path = os.path.join(dirpath, file)
                links = extract_links_from_file(path)
                graph[name] = links      # store outbound links for note
                paths[name] = path       # store actual filesystem path
    return graph, paths

# Compute reverse mapping: note_name → list of incoming links from other notes
def build_incoming_links(graph):
    # Initialize each note with an empty incoming list
    incoming = {note: [] for note in graph}
    for src, targets in graph.items():
        for tgt in targets:
            if tgt in incoming:
                # Add source note as an inbound link target
                incoming[tgt].append(src)
    return incoming