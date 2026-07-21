# comfyui-dailies

One node: **Dailies: Write take.json**. Drop it after your video save node and every clip leaves the graph with a `<clip>.take.json` beside it: content hash, seeds, models, LoRAs, positive prompt, resolved graph, runtime. The format is [take.json](https://github.com/zhang-liz/dailies/blob/main/SPEC.md), the open sidecar the [dailies](https://github.com/zhang-liz/dailies) triage CLI reads and writes.

Generation metadata is lost at save time. This keeps it, next to the file, in a JSON you can grep.

## Install

ComfyUI Manager: search `dailies`. Or:

```sh
cd ComfyUI/custom_nodes
git clone https://github.com/zhang-liz/comfyui-dailies
pip install -r comfyui-dailies/requirements.txt
```

`ffprobe` on PATH is optional; it fills fps, frames, width, and height when no `VHS_VIDEOINFO` is connected.

## Use

Connect `filenames` from **Video Combine** (VideoHelperSuite), or type a `video_path` relative to the output folder. Optional: `video_info` from a VHS loader, `shot` and `parent` for lineage, `hash_models` to content-hash the weights (slow on big files, off by default).

The node writes only the `recipe` block plus `take_id`, `created`, `shot`, `parent`, `output`. An existing `review` block, `gold` label, or any block another tool wrote is preserved.

Then:

```sh
dailies review ComfyUI/output/ --shot shot-07
```

## Test

```sh
python3 -m unittest discover tests
```

No ComfyUI needed; `folder_paths` is stubbed. `ffmpeg` on PATH enables one extra test.

## License

MIT.
