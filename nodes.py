"""Dailies: Write take.json.

One node. Takes the path of a clip the graph just saved, writes
<clip>.take.json beside it with the "recipe" block filled from the resolved
graph, and leaves every other block (review, gold, anything a third tool
wrote) untouched. See SPEC.md in github.com/zhang-liz/dailies.
"""

import datetime
import json
import os
import shutil
import subprocess

import folder_paths
from dailies.take import hash_file, load, save

try:
    from . import recipe
except ImportError:  # run outside a package (tests)
    import recipe

VIDEO_EXT = (".mp4", ".webm", ".mov", ".mkv", ".avi", ".gif", ".webp", ".apng")
MODEL_FOLDERS = ("checkpoints", "diffusion_models", "unet", "loras", "vae", "clip",
                 "text_encoders", "clip_vision", "controlnet", "upscale_models", "embeddings")


def _pick_path(video_path, filenames):
    """The clip to describe: VHS_FILENAMES (save flag, [paths]) wins over the
    plain string. VHS lists the preview PNG first, then the video."""
    paths = []
    if filenames:
        if len(filenames) == 2 and isinstance(filenames[1], (list, tuple)):
            paths = list(filenames[1])
        else:
            paths = list(filenames)
    if paths:
        videos = [p for p in paths if str(p).lower().endswith(VIDEO_EXT)]
        return str((videos or paths)[-1])
    video_path = (video_path or "").strip()
    if not video_path:
        raise ValueError("Dailies: connect VHS filenames or give a video_path")
    if not os.path.isabs(video_path):
        video_path = os.path.join(folder_paths.get_output_directory(), video_path)
    return video_path


def _probe(path):
    """fps, frames, width, height via ffprobe, or all None."""
    out = {"fps": None, "frames": None, "width": None, "height": None}
    if not shutil.which("ffprobe"):
        return out
    try:
        r = subprocess.run(
            ["ffprobe", "-v", "error", "-count_frames", "-select_streams", "v:0",
             "-show_entries", "stream=width,height,avg_frame_rate,nb_read_frames",
             "-of", "json", path],
            capture_output=True, text=True, timeout=120)
        streams = json.loads(r.stdout or "{}").get("streams") or []
    except Exception:
        return out
    if not streams:
        return out
    s = streams[0]
    out["width"], out["height"] = s.get("width"), s.get("height")
    if s.get("nb_read_frames", "N/A") != "N/A":
        out["frames"] = int(s["nb_read_frames"])
    num, _, den = s.get("avg_frame_rate", "0/1").partition("/")
    if den and float(den):
        out["fps"] = round(float(num) / float(den), 3)
    return out


def _output_block(path, video_info):
    info = video_info or {}
    block = {
        "file": os.path.basename(path),
        "fps": info.get("loaded_fps") or info.get("source_fps"),
        "frames": info.get("loaded_frame_count") or info.get("source_frame_count"),
        "width": info.get("loaded_width") or info.get("source_width"),
        "height": info.get("loaded_height") or info.get("source_height"),
    }
    if any(block[k] is None for k in ("fps", "frames", "width", "height")):
        probed = _probe(path)
        for k, v in probed.items():
            if block[k] is None:
                block[k] = v
    return block


def _resolver():
    def resolve(name):
        for folder in MODEL_FOLDERS:
            try:
                p = folder_paths.get_full_path(folder, name)
            except Exception:
                p = None
            if p:
                return p
        return None
    return resolve


class WriteTake:
    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {},
            "optional": {
                "filenames": ("VHS_FILENAMES",),
                "video_path": ("STRING", {"default": "", "tooltip": "Clip path, absolute or relative to the output folder. Ignored when filenames is connected."}),
                "video_info": ("VHS_VIDEOINFO",),
                "shot": ("STRING", {"default": "", "tooltip": "Shot name, groups takes for ranking."}),
                "parent": ("STRING", {"default": "", "tooltip": "take_id this is a rerun of."}),
                "hash_models": ("BOOLEAN", {"default": False, "tooltip": "Content-hash model and LoRA files. Slow on big weights."}),
            },
            "hidden": {"prompt": "PROMPT", "extra_pnginfo": "EXTRA_PNGINFO"},
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("sidecar_path",)
    FUNCTION = "write"
    OUTPUT_NODE = True
    CATEGORY = "dailies"
    DESCRIPTION = "Writes <clip>.take.json beside the clip: content hash, seeds, models, LoRAs, prompt, resolved graph. Preserves any review block already there."

    @classmethod
    def IS_CHANGED(cls, **kw):
        return float("nan")

    def write(self, video_path="", filenames=None, video_info=None, shot="", parent="",
              hash_models=False, prompt=None, extra_pnginfo=None):
        path = _pick_path(video_path, filenames)
        take = load(path)
        take["take_id"] = hash_file(path)
        take["created"] = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        take["shot"] = (shot or "").strip() or take.get("shot")
        take["parent"] = (parent or "").strip() or take.get("parent")
        take["output"] = _output_block(path, video_info)
        rec = recipe.extract(prompt, resolve=_resolver() if hash_models else None)
        rec["env"] = recipe.env()
        take["recipe"] = rec
        sidecar = save(path, take)
        return {"ui": {"text": [sidecar]}, "result": (sidecar,)}


NODE_CLASS_MAPPINGS = {"DailiesWriteTake": WriteTake}
NODE_DISPLAY_NAME_MAPPINGS = {"DailiesWriteTake": "Dailies: Write take.json"}
