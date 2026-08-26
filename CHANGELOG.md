# Changelog

## 0.1.1 (2026-08-26)

- Clearer registry description and display name. No code change.

## 0.1.0 (2026-08-26)

First release. One node, **Dailies: Write take.json**.

- Writes `<clip>.take.json` beside a rendered video: content hash, created time, shot, parent, output geometry.
- `recipe` block: resolved graph, models, LoRAs with strength, conditioning media, seeds by node id, flattened positive prompt, runtime (ComfyUI, torch, GPU).
- Accepts VHS `filenames` and `video_info`, or a typed `video_path`. Falls back to `ffprobe` for fps, frames, width, height.
- Optional content hashing of model and LoRA files (`hash_models`, off by default).
- Preserves `review`, `gold`, and any block written by another tool.
