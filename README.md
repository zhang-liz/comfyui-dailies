# comfyui-dailies

[![Tests](https://github.com/zhang-liz/comfyui-dailies/actions/workflows/test.yml/badge.svg)](https://github.com/zhang-liz/comfyui-dailies/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Lineage sidecars for every video ComfyUI renders.

One node, **Dailies: Write take.json**. Put it after your video save node and each clip leaves the graph with a `<clip>.take.json` beside it: content hash, seeds, models, LoRAs, positive prompt, the resolved graph, and the runtime it rendered on. Plain JSON, next to the file, readable by anything.

Generation metadata is lost at save time. The workflow embedded in an MP4 container is not greppable, and seeds, model files, and prompts scatter across nodes. This keeps them, per take, in the open [take.json](https://github.com/zhang-liz/dailies/blob/main/SPEC.md) format that the [dailies](https://github.com/zhang-liz/dailies) triage CLI reads and writes. Any tool can add its own block; this node never touches the others.

## Install

**ComfyUI Manager:** search `dailies`, install, restart.

**Manual:**

```sh
cd ComfyUI/custom_nodes
git clone https://github.com/zhang-liz/comfyui-dailies
pip install -r comfyui-dailies/requirements.txt
```

Restart ComfyUI. Optional: `ffprobe` on PATH fills fps, frames, width, and height when no `VHS_VIDEOINFO` is connected.

## Use

Add **Dailies: Write take.json** (category `dailies`) and give it the clip:

- Connect `filenames` from **Video Combine** (VideoHelperSuite). Preferred; no typing.
- Or type `video_path`, relative to the output folder or absolute. Works with the core **Save Video** node.

Optional inputs:

| Input | What it does |
|---|---|
| `video_info` | `VHS_VIDEOINFO` from a VHS loader, for fps, frames, width, height |
| `shot` | Groups takes for ranking in `dailies review` |
| `parent` | `take_id` of the take this one reruns |
| `hash_models` | Content-hash model and LoRA files. Slow on multi-GB weights. Off by default |

Output: `sidecar_path`, the path of the JSON written.

Then:

```sh
dailies review ComfyUI/output/ --shot shot-07
```

## What it writes

```json
{
  "take_id": "sha256:3f9c…",
  "shot": "shot-07",
  "parent": null,
  "created": "2026-08-26T07:14:00Z",
  "output": { "file": "take-031.mp4", "fps": 24, "frames": 121, "width": 1280, "height": 720 },
  "recipe": {
    "workflow": { "…": "resolved graph, verbatim" },
    "models": [ { "file": "wan2.2_t2v_14b_fp8.safetensors", "sha256": null, "loader": "UNETLoader" } ],
    "loras": [ { "file": "myrna_v3.safetensors", "sha256": null, "strength": 0.85 } ],
    "conditioning": [ { "role": "LoadImage", "file": "ref_myrna.png", "sha256": null } ],
    "seeds": { "6": 424242 },
    "prompt_text": "a woman lifts a cup, warm kitchen light",
    "env": { "comfyui": "0.8.32", "torch": "2.9.1", "gpu": "Apple MPS", "platform": "macOS-15.4-arm64" }
  },
  "review": null
}
```

`review` and `gold` belong to the reviewer and the human. If they exist, they are kept as is. Unknown keys from any other tool are kept too.

Extraction does not depend on node class names. Models are found by file extension, seeds by input name (`seed`, `noise_seed`), the prompt by following `positive` links back to a text encoder. New loaders and samplers work without a code change.

## Roadmap

- **Gate node:** judge a clip after decode, with `pass` and `kill` outputs so expensive post-processing runs on keepers only. Wraps an open video reward model; the calibrated threshold comes from `dailies calibrate`.
- **Regen driver:** requeue killed takes with new seeds under a budget cap.

Issues and PRs welcome. See [CONTRIBUTING.md](CONTRIBUTING.md).

## Test

```sh
python3 -m unittest discover tests
```

No ComfyUI needed. `ffmpeg` on PATH enables one extra test.

## Related

- [dailies](https://github.com/zhang-liz/dailies): the triage CLI and the owner of the sidecar spec
- [VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite): the `filenames` and `video_info` sockets this node accepts

## License

MIT.
