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


def _hasher(resolve):
    if resolve is None:
        return lambda name: None
    from dailies.take import hash_file
    cache = {}

    def hash_name(name):
        if name in cache:
            return cache[name]
        path = resolve(name)
        cache[name] = hash_file(path) if path else None
        return cache[name]
    return hash_name


def extract(graph, resolve=None):
    """The "recipe" block of take.json, minus env.

    resolve: optional callable name -> absolute path (or None). When given,
    every model and LoRA file it resolves is content-hashed. Hashing multi-GB
    weights is slow, so callers opt in.
    """
    graph = graph or {}
    hash_name = _hasher(resolve)
    models, loras, conditioning, seeds = [], [], [], {}
    seen = set()
    for nid, node in graph.items():
        ct = node.get("class_type", "")
        inputs = _inputs(node)
        for key, v in inputs.items():
            if key in SEED_KEYS and isinstance(v, int) and not isinstance(v, bool):
                seeds[nid] = v
                continue
            if not isinstance(v, str):
                continue
            low = v.lower()
            if low.endswith(MODEL_EXT):
                if (v, ct) in seen:
                    continue
                seen.add((v, ct))
                if "lora" in ct.lower() or "lora" in key.lower():
                    strength = next((inputs[k] for k in STRENGTH_KEYS if k in inputs), None)
                    loras.append({"file": v, "sha256": hash_name(v), "strength": strength})
                else:
                    models.append({"file": v, "sha256": hash_name(v), "loader": ct})
            elif low.endswith(MEDIA_EXT):
                conditioning.append({"role": ct, "file": v, "sha256": None})
    return {
        "workflow": graph,
        "models": models,
        "loras": loras,
        "conditioning": conditioning,
        "seeds": seeds,
        "prompt_text": prompt_text(graph),
    }


def env():
    """Runtime the take was rendered in. Every field is best effort."""
    out = {"comfyui": None, "torch": None, "gpu": None, "platform": platform.platform()}
    try:
        import comfyui_version
        out["comfyui"] = getattr(comfyui_version, "__version__", None)
    except Exception:
        pass
    try:
        import torch
        out["torch"] = torch.__version__
        if torch.cuda.is_available():
            out["gpu"] = torch.cuda.get_device_name(0)
        elif getattr(torch.backends, "mps", None) and torch.backends.mps.is_available():
            out["gpu"] = "Apple MPS"
    except Exception:
        pass
    return out
