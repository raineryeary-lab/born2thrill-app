"""ComfyUI polish pilot: img2img over the Stage-1 dollhouse render with
canny (from the geometry edge pass) + depth ControlNets, per the Codex
starting parameters in plans/variant-pipeline-rollout-v1.md."""
import json
import sys
import time
import urllib.request

HOST = "http://127.0.0.1:8188"
DENOISE = float(sys.argv[1]) if len(sys.argv) > 1 else 0.30
CANNY = float(sys.argv[2]) if len(sys.argv) > 2 else 0.80
DEPTH = float(sys.argv[3]) if len(sys.argv) > 3 else 0.45
TAG = sys.argv[4] if len(sys.argv) > 4 else "pilot"
# Optional palette/mood wording appended to the prompt: the automatic
# colour-variant path (Rainer 2026-08-11). At denoise <=0.35 the recolor
# stays subtle; 0.40-0.50 shifts colours decisively while both ControlNets
# hold the geometry. Example:
#   comfyui-polish-pilot.py 0.45 0.85 0.55 variant-sage "sage green walls,
#   light oak floor, brass accents"
PALETTE = sys.argv[5] if len(sys.argv) > 5 else ""
# Optional manifest to update with the polish recipe (arg 6).
MANIFEST = sys.argv[6] if len(sys.argv) > 6 else ""

PROMPT = ("professional architectural interior visualization, top-down dollhouse "
          "cutaway of a modern single-storey home, soft natural daylight, subtle "
          "ambient occlusion, photorealistic materials, oak parquet floor, matte "
          "black kitchen with granite worktop, grey fabric sofa, crisp white "
          "walls, high-end real estate rendering, sharp focus, 8k")
if PALETTE:
    PROMPT = PROMPT + ", colour palette: " + PALETTE
NEGATIVE = ("blurry, warped walls, bent lines, distorted geometry, extra rooms, "
            "furniture floating, text, watermark, people, cartoon, painting, "
            "oversaturated, lens flare")

g = {}
g["1"] = {"class_type": "CheckpointLoaderSimple",
          "inputs": {"ckpt_name": "RealVisXL_V5.0_fp16.safetensors"}}
g["2"] = {"class_type": "LoadImage", "inputs": {"image": "pilot-color.png"}}
g["3"] = {"class_type": "LoadImage", "inputs": {"image": "pilot-edge.png"}}
g["4"] = {"class_type": "LoadImage", "inputs": {"image": "pilot-depth.png"}}
# SDXL works best near 1MP-2MP; 1600x1200 keeps the 4:3 plan uncropped.
for src, node in (("2", "12"), ("3", "13"), ("4", "14")):
    g[node] = {"class_type": "ImageScale",
               "inputs": {"image": [src, 0], "upscale_method": "lanczos",
                           "width": 1600, "height": 1200, "crop": "disabled"}}
g["5"] = {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": PROMPT}}
g["6"] = {"class_type": "CLIPTextEncode", "inputs": {"clip": ["1", 1], "text": NEGATIVE}}
g["7"] = {"class_type": "ControlNetLoader",
          "inputs": {"control_net_name": "controlnet-canny-sdxl-1.0.safetensors"}}
g["8"] = {"class_type": "ControlNetLoader",
          "inputs": {"control_net_name": "controlnet-depth-sdxl-1.0.safetensors"}}
g["9"] = {"class_type": "ControlNetApplyAdvanced",
          "inputs": {"positive": ["5", 0], "negative": ["6", 0],
                      "control_net": ["7", 0], "image": ["13", 0],
                      "strength": CANNY, "start_percent": 0.0, "end_percent": 0.85,
                      "vae": ["1", 2]}}
g["10"] = {"class_type": "ControlNetApplyAdvanced",
           "inputs": {"positive": ["9", 0], "negative": ["9", 1],
                       "control_net": ["8", 0], "image": ["14", 0],
                       "strength": DEPTH, "start_percent": 0.0, "end_percent": 0.75,
                       "vae": ["1", 2]}}
g["11"] = {"class_type": "VAEEncode", "inputs": {"pixels": ["12", 0], "vae": ["1", 2]}}
g["15"] = {"class_type": "KSampler",
           "inputs": {"model": ["1", 0], "positive": ["10", 0], "negative": ["10", 1],
                       "latent_image": ["11", 0], "seed": 20260810, "steps": 28,
                       "cfg": 5.5, "sampler_name": "dpmpp_2m", "scheduler": "karras",
                       "denoise": DENOISE}}
g["16"] = {"class_type": "VAEDecode", "inputs": {"samples": ["15", 0], "vae": ["1", 2]}}
g["17"] = {"class_type": "SaveImage",
           "inputs": {"images": ["16", 0], "filename_prefix": TAG}}

req = urllib.request.Request(HOST + "/prompt",
                             json.dumps({"prompt": g}).encode(),
                             {"Content-Type": "application/json"})
with urllib.request.urlopen(req) as response:
    submitted = json.load(response)
prompt_id = submitted.get("prompt_id")
if not prompt_id:
    print("SUBMIT FAILED:", json.dumps(submitted)[:2000])
    sys.exit(1)
print("queued", prompt_id, f"denoise={DENOISE} canny={CANNY} depth={DEPTH}")

for _ in range(240):
    time.sleep(5)
    with urllib.request.urlopen(HOST + f"/history/{prompt_id}") as response:
        history = json.load(response)
    if prompt_id in history:
        entry = history[prompt_id]
        status = entry.get("status", {})
        if status.get("completed"):
            outputs = [image["filename"]
                       for node_output in entry.get("outputs", {}).values()
                       for image in node_output.get("images", [])]
            for name in outputs:
                print("OUTPUT", name)
            if MANIFEST and outputs:
                try:
                    with open(MANIFEST, encoding="utf-8") as handle:
                        manifest = json.load(handle)
                    manifest["polish"] = {
                        "output": outputs[0], "denoise": DENOISE,
                        "canny": CANNY, "depth": DEPTH,
                        "palette_prompt": PALETTE or None,
                        "seed": 20260810, "checkpoint": "RealVisXL_V5.0_fp16",
                    }
                    with open(MANIFEST, "w", encoding="utf-8") as handle:
                        json.dump(manifest, handle, indent=1)
                    print("MANIFEST updated:", MANIFEST)
                except Exception as error:
                    print("manifest update failed:", error)
            sys.exit(0)
        if status.get("status_str") == "error":
            print("ERROR:", json.dumps(status)[:3000])
            sys.exit(1)
print("TIMEOUT")
sys.exit(1)
