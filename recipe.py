"""Recipe extraction from a resolved ComfyUI prompt graph.

Pure functions, no ComfyUI imports. The graph is the hidden PROMPT input a
node receives at execution: {node_id: {"class_type": str, "inputs": {...}}},
where a link is [source_node_id, output_index].

Nothing here depends on node class names staying stable. Models are found by
file extension, seeds by input name, prompt text by following "positive" links.
"""

import platform

MODEL_EXT = (".safetensors", ".ckpt", ".pt", ".pth", ".bin", ".gguf", ".sft")
MEDIA_EXT = (".png", ".jpg", ".jpeg", ".webp", ".bmp", ".gif", ".tif", ".tiff",
             ".mp4", ".webm", ".mov", ".mkv", ".wav", ".mp3", ".flac")
SEED_KEYS = ("seed", "noise_seed")
STRENGTH_KEYS = ("strength_model", "strength", "strength_clip")
MAX_LINK_DEPTH = 6


def _is_link(v):
    return isinstance(v, list) and len(v) == 2 and isinstance(v[1], int)


def _inputs(node):
    return node.get("inputs") or {}


def _text_behind(graph, nid, depth=0):
    """First string "text" input reachable from nid, following links."""
    node = graph.get(nid)
    if node is None or depth > MAX_LINK_DEPTH:
        return None
    inputs = _inputs(node)
    t = inputs.get("text")
    if isinstance(t, str):
        return t
    for v in inputs.values():
        if _is_link(v):
            found = _text_behind(graph, v[0], depth + 1)
            if found is not None:
                return found
    return None


def prompt_text(graph):
    """Flattened positive prompt: texts behind every "positive" link, deduped,
    joined by newlines. Falls back to the first CLIPTextEncode text."""
    texts = []
    for node in graph.values():
        pos = _inputs(node).get("positive")
        if _is_link(pos):
            t = _text_behind(graph, pos[0])
            if t and t not in texts:
                texts.append(t)
    if texts:
        return "\n".join(texts)
    for node in graph.values():
        t = _inputs(node).get("text")
        if isinstance(t, str) and "TextEncode" in node.get("class_type", ""):
            return t
    return None
