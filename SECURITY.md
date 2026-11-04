# Security policy

## Supported versions

The latest version on the [Comfy Registry](https://registry.comfy.org/nodes/comfyui-dailies) is the supported version.

## Reporting a vulnerability

Report privately via [GitHub security advisories](https://github.com/zhang-liz/comfyui-dailies/security/advisories/new). Do not open a public issue for a vulnerability.

Relevant surface: the node runs `ffprobe` on a path from the workflow, reads and hashes model files, and writes JSON beside the video. Reports about path handling or command construction are especially welcome.
