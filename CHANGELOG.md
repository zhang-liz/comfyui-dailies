# Changelog

## Unreleased

- Depend on `video-dailies` from PyPI (`>=0.2,<0.3`), not an unpinned git URL.

## 0.1.3 (2026-08-26)

- Description leads with the problem it solves. No code change.

## 0.1.2 (2026-08-26)

- Registry listing: display name, description, icon, OS classifier, links. No code change.

## 0.1.1 (2026-08-26)

- Clearer registry description and display name. No code change.

## 0.1.0 (2026-08-26)

First release. One node, **Dailies: Write take.json**.

- Writes `<clip>.take.json` beside a rendered video: content hash, created time, shot, parent, output geometry.
- `recipe` block: resolved graph, models, LoRAs with strength, conditioning media, seeds by node id, flattened positive prompt, runtime (ComfyUI, torch, GPU).
- Accepts VHS `filenames` and `video_info`, or a typed `video_path`. Falls back to `ffprobe` for fps, frames, width, height.
- Optional content hashing of model and LoRA files (`hash_models`, off by default).
- Preserves `review`, `gold`, and any block written by another tool.
