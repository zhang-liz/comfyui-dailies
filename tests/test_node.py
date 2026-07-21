"""The node end to end, with ComfyUI stubbed out.

Run from the repo root: python3 -m unittest discover tests
"""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import types
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# ComfyUI provides folder_paths at runtime. Stub it before importing the node.
_fp = types.ModuleType("folder_paths")
_fp.get_full_path = lambda folder, name: None
_fp.get_output_directory = lambda: tempfile.gettempdir()
sys.modules.setdefault("folder_paths", _fp)

import nodes  # noqa: E402

FFMPEG = shutil.which("ffmpeg")

GRAPH = {
    "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "wan.safetensors"}},
    "4": {"class_type": "CLIPTextEncode", "inputs": {"text": "a cup"}},
    "6": {"class_type": "KSampler", "inputs": {"positive": ["4", 0], "seed": 5}},
}


def gen(path, seconds=1, fps=12):
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-f", "lavfi", "-i", "testsrc=size=64x48",
         "-t", str(seconds), "-r", str(fps), "-pix_fmt", "yuv420p", path], check=True)


class WriteTake(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.clip = os.path.join(self.dir, "take-001.mp4")
        with open(self.clip, "wb") as f:
            f.write(b"not really a video but hashable")
        self.node = nodes.WriteTake()

    def tearDown(self):
        shutil.rmtree(self.dir)

    def run_node(self, **kw):
        kw.setdefault("prompt", GRAPH)
        kw.setdefault("extra_pnginfo", {"workflow": {"nodes": []}})
        return self.node.write(**kw)

    def read(self):
        with open(self.clip + ".take.json") as f:
            return json.load(f)

    def test_writes_sidecar_next_to_clip(self):
        out = self.run_node(video_path=self.clip)
        self.assertEqual(out["result"][0], self.clip + ".take.json")
        self.assertTrue(os.path.exists(self.clip + ".take.json"))

    def test_take_id_is_content_hash(self):
        self.run_node(video_path=self.clip)
        self.assertTrue(self.read()["take_id"].startswith(("sha256:", "blake3:")))

    def test_recipe_populated_review_null(self):
        self.run_node(video_path=self.clip)
        t = self.read()
        self.assertEqual(t["recipe"]["seeds"], {"6": 5})
        self.assertEqual(t["recipe"]["prompt_text"], "a cup")
        self.assertIsNone(t["review"])
        self.assertIsNotNone(t["created"])

    def test_existing_review_block_is_preserved(self):
        with open(self.clip + ".take.json", "w") as f:
            json.dump({"review": {"verdict": "kill"}, "custom_tool": {"x": 1}}, f)
        self.run_node(video_path=self.clip)
        t = self.read()
        self.assertEqual(t["review"], {"verdict": "kill"})
        self.assertEqual(t["custom_tool"], {"x": 1})
        self.assertEqual(t["recipe"]["seeds"], {"6": 5})

    def test_shot_and_parent(self):
        self.run_node(video_path=self.clip, shot="shot-07", parent="sha256:abc")
        t = self.read()
        self.assertEqual(t["shot"], "shot-07")
        self.assertEqual(t["parent"], "sha256:abc")

    def test_empty_shot_is_null(self):
        self.run_node(video_path=self.clip, shot="", parent="")
        t = self.read()
        self.assertIsNone(t["shot"])
        self.assertIsNone(t["parent"])

    def test_vhs_filenames_picks_last_video(self):
        png = os.path.join(self.dir, "take-001.png")
        open(png, "wb").close()
        self.run_node(filenames=(True, [png, self.clip]))
        self.assertTrue(os.path.exists(self.clip + ".take.json"))
        self.assertFalse(os.path.exists(png + ".take.json"))

    def test_video_info_fills_output(self):
        info = {"loaded_fps": 24.0, "loaded_frame_count": 121, "loaded_width": 1280, "loaded_height": 720}
        self.run_node(video_path=self.clip, video_info=info)
        o = self.read()["output"]
        self.assertEqual((o["fps"], o["frames"], o["width"], o["height"]), (24.0, 121, 1280, 720))
        self.assertEqual(o["file"], "take-001.mp4")

    def test_no_path_at_all_raises(self):
        with self.assertRaises(ValueError):
            self.run_node(video_path="")

    def test_env_recorded(self):
        self.run_node(video_path=self.clip)
        env = self.read()["recipe"]["env"]
        self.assertIn("comfyui", env)
        self.assertIn("torch", env)
        self.assertIn("gpu", env)

    @unittest.skipUnless(FFMPEG, "ffmpeg not on PATH")
    def test_ffprobe_fallback_fills_output(self):
        gen(self.clip)
        self.run_node(video_path=self.clip)
        o = self.read()["output"]
        self.assertEqual((o["width"], o["height"], o["fps"]), (64, 48, 12.0))
        self.assertEqual(o["frames"], 12)


class NodeContract(unittest.TestCase):
    def test_registered(self):
        self.assertIn("DailiesWriteTake", nodes.NODE_CLASS_MAPPINGS)
        self.assertEqual(nodes.WriteTake.RETURN_TYPES, ("STRING",))
        self.assertTrue(nodes.WriteTake.OUTPUT_NODE)

    def test_hidden_inputs_declared(self):
        hidden = nodes.WriteTake.INPUT_TYPES()["hidden"]
        self.assertEqual(hidden["prompt"], "PROMPT")
        self.assertEqual(hidden["extra_pnginfo"], "EXTRA_PNGINFO")


if __name__ == "__main__":
    unittest.main()
