# Contributing

Bug reports and pull requests are welcome. Small and focused beats large and mixed.

## Setup

```sh
git clone https://github.com/zhang-liz/comfyui-dailies
cd comfyui-dailies
pip install -r requirements.txt
python3 -m unittest discover tests
```

Tests need no ComfyUI; `folder_paths` is stubbed in `tests/test_node.py`. With `ffmpeg` on PATH one more test runs.

To try a change live, symlink the checkout into `ComfyUI/custom_nodes/` and restart ComfyUI.

## Ground rules

- **The sidecar format is [SPEC.md in dailies](https://github.com/zhang-liz/dailies/blob/main/SPEC.md).** This node writes the `recipe` block and the identity fields. Changes to the format go to that repo first.
- **Preserve what other tools wrote.** Read the sidecar, replace our block, write the rest back. Never strip unknown keys.
- **No new dependencies without a reason.** ComfyUI installs are fragile. Standard library plus `video-dailies` is the whole footprint.
- **No hard dependency on node class names.** Models are found by file extension, seeds by input name, prompts by following links. A new loader or sampler should work without a code change. If it does not, that is a bug.
- **Tests with the change.** Add a case to `tests/test_recipe.py` for extraction logic, `tests/test_node.py` for node behavior.

## Pull requests

- One change per PR.
- Short subject line, body only when the diff does not explain itself.
- CI runs the tests on Python 3.9 and 3.12.

## Releasing

Bump `version` in `pyproject.toml`, add a line to `CHANGELOG.md`, merge to main. The publish workflow pushes the new version to the Comfy registry.
