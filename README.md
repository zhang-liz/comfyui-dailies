# comfyui-dailies

[![Tests](https://github.com/zhang-liz/comfyui-dailies/actions/workflows/test.yml/badge.svg)](https://github.com/zhang-liz/comfyui-dailies/actions/workflows/test.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Render 50 takes overnight and one is right. Which seed, model, LoRA and prompt made it? ComfyUI does not say. This node writes a `take.json` beside every video it renders, so any take can be found, reproduced or rerun later, and a night of renders can be ranked without reopening ComfyUI. Plain JSON, next to the file.

Format: [take.json spec](https://github.com/zhang-liz/dailies/blob/main/SPEC.md). Reader: the [dailies](https://github.com/zhang-liz/dailies) triage CLI.

## Why

Video generation is a numbers game: 20 to 50 takes per usable shot. The metadata that explains a take dies at save time.

| Pain | What this fixes |
|---|---|
| The good take is in the output folder, the recipe is gone. Seeds, LoRA strengths and prompt edits are scattered across nodes you have since changed. | Every take carries its own recipe. Reproduce or rerun any clip weeks later. |
| The workflow is embedded in the MP4. Not greppable, not diffable, not readable by other tools. | Plain JSON beside the file. `grep`, `jq`, a spreadsheet, or the [dailies](https://github.com/zhang-liz/dailies) CLI all read it. |
| Ranking a night of renders means opening each one and guessing what made it. | `dailies review` ranks the folder, kills the dead takes with reasons, and writes its verdict into the same file. |
| Reruns lose their history. Nobody knows take 31 came from take 12. | `parent` links a rerun to its source. Lineage is a chain of pointers, no database. |
| Model updates every few weeks stale your results and nobody can say which model made what. | Model and LoRA filenames per take, content hashes on request. |


## Install

ComfyUI Manager: search **dailies**, install, restart.

Manual:

```sh
cd ComfyUI/custom_nodes
git clone https://github.com/zhang-liz/comfyui-dailies
pip install -r comfyui-dailies/requirements.txt
```

Restart ComfyUI.

## Use

1. Add the node **Dailies: Write take.json** (category `dailies`).
2. Give it the clip. Either:
   - connect `filenames` from **Video Combine** (VideoHelperSuite), or
   - type `video_path`, relative to the output folder (works with the core **Save Video** node).
3. Queue the prompt. `<clip>.take.json` appears next to the video.

Then, from a terminal:

```sh
dailies review ComfyUI/output/ --shot shot-07
```

### Optional inputs

| Input | Use |
|---|---|
| `video_info` | `VHS_VIDEOINFO` from a VHS loader. Fills fps, frames, width, height. Without it, `ffprobe` on PATH does the same. |
| `shot` | Shot name. Groups takes for ranking. |
| `parent` | `take_id` of the take this one reruns. |
| `hash_models` | Content-hash the model and LoRA files. Slow on big weights. Off by default. |

Output: `sidecar_path`, the JSON path.

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
    "env": { "comfyui": "0.8.32", "torch": "2.9.1", "gpu": "Apple MPS" }
  },
  "review": null
}
```

The node writes `recipe` and the identity fields only. `review`, `gold`, and blocks from other tools are kept as is.

Extraction does not depend on node names. Models are found by file extension, seeds by input name, the prompt by following `positive` links. New loaders and samplers work without a code change.

## Roadmap

- Gate node: `pass` and `kill` outputs after a judge, so post-processing runs on keepers only.
- Regen driver: requeue kills with new seeds under a budget cap.

## Develop

```sh
python3 -m unittest discover tests
```

No ComfyUI needed. See [CONTRIBUTING.md](CONTRIBUTING.md).

## License

MIT.
