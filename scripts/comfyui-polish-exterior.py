"""ComfyUI polish pass for exterior renders: img2img over the Blender color
render with canny (from the geometry edge pass) + depth ControlNets, same
recipe as comfyui-polish-pilot.py's interior pass, adapted for real-estate
exterior architecture photography and a house style (modern/classic).

Usage:
  comfyui-polish-exterior.py <color.png> <edge.png> <depth.png> <style> <tag> [denoise] [canny] [depth_strength] [mood]

mood: morning | golden_hour | midday (default golden_hour)
"""
import json
import os
import sys
import time
import urllib.request

HOST = "http://127.0.0.1:8188"

color_path, edge_path, depth_path, style, TAG = sys.argv[1:6]
DENOISE = float(sys.argv[6]) if len(sys.argv) > 6 else 0.38
CANNY = float(sys.argv[7]) if len(sys.argv) > 7 else 0.75
DEPTH = float(sys.argv[8]) if len(sys.argv) > 8 else 0.45
MOOD = sys.argv[9] if len(sys.argv) > 9 else "golden_hour"

STYLE_WORDS = {
    "modern": ("modern minimalist single-storey house, smooth white render facade, "
               "flat roof with dark parapet coping, anthracite aluminium window frames"),
    "classic": ("classic single-storey bungalow, warm cream plaster facade, "
                "terracotta hip roof tiles, dark metal window frames"),
}

MOOD_WORDS = {
    "morning": ("early morning light, pale cool blue sky with soft haze, low sun casting long cool-toned "
                "shadows, misty distant horizon, dew glistening on grass, muted desaturated colour palette"),
    "golden_hour": ("sunset golden hour, sky ablaze with orange and pink and deep purple clouds, sun low on "
                     "the horizon, intense warm orange rim light on the house facade, long dramatic shadows, "
                     "warm amber colour grade over the entire scene"),
    "midday": ("harsh bright midday sun directly overhead, saturated deep blue cloudless sky, high contrast, "
                "short hard-edged shadows directly beneath the roofline, vivid punchy colours, crisp clarity"),
}

# Reference bar (Rainer, 2026-08-13): a real listing photo with manicured
# hedges, layered flower beds, a furnished terrace, mature trees framing the
# plot -- landscaping detail this rich, not just a flat lawn. This is safe
# to push hard because it only ever lands in the sky/ground half of the
# masked composite; the building half comes from the low-denoise safe pass
# and never sees this prompt's freedom.
LANDSCAPE_WORDS = ("professionally landscaped garden, neatly trimmed boxwood hedges and shrubs, "
                    "layered flower beds with blooming plants, furnished outdoor terrace with modern "
                    "dining table and chairs, potted plants, mature trees framing the property, "
                    "gravel or paved garden path")

# Hard architectural datum (Rainer, 2026-08-13): generated facade lights
# must never float at an aesthetically guessed height.  Their physical
# centreline is tied to the head of the associated exterior opening.  When
# the renderer cannot establish that association it must omit the decorative
# fixture rather than inventing a position.
WALL_LIGHT_RULE = (
    "facade wall lights obey a strict architectural datum: each black wall-light fixture body is "
    "mounted beside its associated exterior door or window on solid wall, and the horizontal "
    "centreline of the fixture body exactly equals the top/head elevation of that door or window "
    "frame; never mount a fixture above the frame head, directly above a window, beneath the eaves, "
    "or at handle-height or mid-window height; if an associated opening head cannot be established, "
    "omit that decorative wall light instead of guessing its height"
)

PROMPT = ("professional real estate exterior architecture photography, "
          f"{STYLE_WORDS.get(style, STYLE_WORDS['modern'])}, "
          f"{MOOD_WORDS.get(MOOD, MOOD_WORDS['golden_hour'])}, "
          f"{LANDSCAPE_WORDS}, {WALL_LIGHT_RULE}, inviting emotional atmosphere, lush green lawn, "
          "photorealistic materials and textures, crisp architectural detail, shallow depth of field, "
          "high-end real estate listing photo, magazine quality, sharp focus, 8k")
NEGATIVE = ("blurry, warped walls, bent lines, distorted geometry, crooked windows, "
            "floating objects, people, cars, text, watermark, logo, cartoon, painting, "
            "oversaturated, overexposed, lens flare, night, dark, gloomy, low quality")


def upload(path):
    filename = os.path.basename(path)
    boundary = "----comfyupload"
    with open(path, "rb") as handle:
        data = handle.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="image"; filename="{filename}"\r\n'
        "Content-Type: image/png\r\n\r\n"
    ).encode() + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(
        HOST + "/upload/image", data=body,
        headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    with urllib.request.urlopen(req) as response:
        result = json.load(response)
    return result["name"]


color_name = upload(color_path)
edge_name = upload(edge_path)
depth_name = upload(depth_path)
print(f"uploaded: {color_name} / {edge_name} / {depth_name}")

g = {}
g["1"] = {"class_type": "CheckpointLoaderSimple",
          "inputs": {"ckpt_name": "RealVisXL_V5.0_fp16.safetensors"}}
g["2"] = {"class_type": "LoadImage", "inputs": {"image": color_name}}
g["3"] = {"class_type": "LoadImage", "inputs": {"image": edge_name}}
g["4"] = {"class_type": "LoadImage", "inputs": {"image": depth_name}}
for src, node in (("2", "12"), ("3", "13"), ("4", "14")):
    g[node] = {"class_type": "ImageScale",
               "inputs": {"image": [src, 0], "upscale_method": "lanczos",
                           "width": 1920, "height": 1280, "crop": "disabled"}}
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
# A fixed seed across mood variants was the actual bug behind "these three
# look identical" (Rainer, 2026-08-13): same seed + same img2img anchor +
# same ControlNet strength barely moves regardless of a few changed prompt
# words, since the sampler starts from nearly the same noise trajectory.
# Each mood needs its own seed so the model actually explores a different
# image, not just a reworded caption on the same one. Explicit lookup, not
# hash(MOOD): Python's string hash is randomized per-process, so it would
# pick a different seed on every single invocation, non-reproducible.
MOOD_SEEDS = {"morning": 20260813, "golden_hour": 20260901, "midday": 20261015}
SEED = MOOD_SEEDS.get(MOOD, 20260813)
g["15"] = {"class_type": "KSampler",
           "inputs": {"model": ["1", 0], "positive": ["10", 0], "negative": ["10", 1],
                       "latent_image": ["11", 0], "seed": SEED, "steps": 32,
                       "cfg": 6.0, "sampler_name": "dpmpp_2m", "scheduler": "karras",
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
print(f"queued {prompt_id} style={style} denoise={DENOISE} canny={CANNY} depth={DEPTH}")

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
            sys.exit(0)
        if status.get("status_str") == "error":
            print("ERROR:", json.dumps(status)[:3000])
            sys.exit(1)
print("TIMEOUT")
sys.exit(1)
