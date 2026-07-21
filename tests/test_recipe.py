"""Recipe extraction from a resolved ComfyUI prompt graph. Pure functions, no ComfyUI.

Run from the repo root: python3 -m unittest discover tests
"""

import os
import sys
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import recipe  # noqa: E402

# Shape of the hidden PROMPT input: {node_id: {"class_type", "inputs"}}.
# Links are [source_node_id, output_index].
GRAPH = {
    "1": {"class_type": "UNETLoader",
          "inputs": {"unet_name": "wan2.2_t2v_14b_fp8.safetensors", "weight_dtype": "fp8_e4m3fn"}},
    "2": {"class_type": "LoraLoaderModelOnly",
          "inputs": {"model": ["1", 0], "lora_name": "myrna_v3.safetensors", "strength_model": 0.85}},
    "3": {"class_type": "CLIPLoader",
          "inputs": {"clip_name": "umt5_xxl_fp8.safetensors", "type": "wan"}},
    "4": {"class_type": "CLIPTextEncode",
          "inputs": {"clip": ["3", 0], "text": "a woman lifts a cup, warm kitchen light"}},
    "5": {"class_type": "CLIPTextEncode",
          "inputs": {"clip": ["3", 0], "text": "blurry, watermark"}},
    "6": {"class_type": "KSampler",
          "inputs": {"model": ["2", 0], "positive": ["4", 0], "negative": ["5", 0],
                     "seed": 424242, "steps": 20, "cfg": 5.0, "latent_image": ["7", 0]}},
    "7": {"class_type": "EmptyHunyuanLatentVideo",
          "inputs": {"width": 1280, "height": 720, "length": 121, "batch_size": 1}},
    "8": {"class_type": "VAELoader", "inputs": {"vae_name": "wan_2.1_vae.safetensors"}},
    "9": {"class_type": "LoadImage", "inputs": {"image": "ref_myrna.png"}},
    "10": {"class_type": "VHS_VideoCombine",
           "inputs": {"images": ["11", 0], "frame_rate": 24, "format": "video/h264-mp4"}},
}


class Models(unittest.TestCase):
    def test_model_files_found_without_loras(self):
        r = recipe.extract(GRAPH)
        files = sorted(m["file"] for m in r["models"])
        self.assertEqual(files, ["umt5_xxl_fp8.safetensors", "wan2.2_t2v_14b_fp8.safetensors",
                                 "wan_2.1_vae.safetensors"])

    def test_model_hash_is_null_when_not_hashed(self):
        r = recipe.extract(GRAPH)
        self.assertTrue(all(m["sha256"] is None for m in r["models"]))

    def test_loras_carry_strength(self):
        r = recipe.extract(GRAPH)
        self.assertEqual(r["loras"], [{"file": "myrna_v3.safetensors", "sha256": None, "strength": 0.85}])

    def test_image_inputs_are_not_models(self):
        r = recipe.extract(GRAPH)
        self.assertNotIn("ref_myrna.png", [m["file"] for m in r["models"]])


class Seeds(unittest.TestCase):
    def test_seed_keyed_by_node_id(self):
        self.assertEqual(recipe.extract(GRAPH)["seeds"], {"6": 424242})

    def test_noise_seed_counts(self):
        g = {"1": {"class_type": "RandomNoise", "inputs": {"noise_seed": 7}}}
        self.assertEqual(recipe.extract(g)["seeds"], {"1": 7})

    def test_linked_seed_is_skipped(self):
        g = {"1": {"class_type": "KSampler", "inputs": {"seed": ["2", 0]}}}
        self.assertEqual(recipe.extract(g)["seeds"], {})


class PromptText(unittest.TestCase):
    def test_positive_prompt_only(self):
        self.assertEqual(recipe.extract(GRAPH)["prompt_text"], "a woman lifts a cup, warm kitchen light")

    def test_falls_back_to_first_text_encode(self):
        g = {"4": {"class_type": "CLIPTextEncode", "inputs": {"text": "only one"}}}
        self.assertEqual(recipe.extract(g)["prompt_text"], "only one")

    def test_no_text_is_null(self):
        self.assertIsNone(recipe.extract({})["prompt_text"])


class Workflow(unittest.TestCase):
    def test_workflow_is_the_graph_verbatim(self):
        self.assertEqual(recipe.extract(GRAPH)["workflow"], GRAPH)

    def test_conditioning_records_loaded_images(self):
        r = recipe.extract(GRAPH)
        self.assertEqual(r["conditioning"], [{"role": "LoadImage", "file": "ref_myrna.png", "sha256": None}])


class Hashing(unittest.TestCase):
    def test_hashes_resolved_files(self):
        def resolve(name):
            return __file__ if name.endswith(".safetensors") else None
        r = recipe.extract(GRAPH, resolve=resolve)
        for m in r["models"] + r["loras"]:
            self.assertTrue(m["sha256"].startswith(("sha256:", "blake3:")), m)

    def test_unresolved_file_stays_null(self):
        r = recipe.extract(GRAPH, resolve=lambda name: None)
        self.assertIsNone(r["models"][0]["sha256"])


if __name__ == "__main__":
    unittest.main()
