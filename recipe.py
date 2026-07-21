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
