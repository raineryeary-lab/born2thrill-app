"""Alle Szenen aus szenen.json mit MiniMax H3 Reference-to-Video (lokales ComfyUI).
Platzhalter bis Seedance/Runway; ueberspringt Szenen, deren mp4 schon da ist.
Knoten und Dateien wie im Blueprint "Image to Video (MiniMax H3)", nur der
Bild-Knoten ist ReferenceToVideo mit dem Figurenblatt als <Picture 1>."""
import json, sys, time, urllib.request, uuid

LOCAL = "http://127.0.0.1:8188"
import os, shutil
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import prompt_bauen
SHEET = os.path.join(HERE, "familie-figuren.png")
OUT = r"E:/_comfyUI/ComfyUI/ComfyUI/output"


def upload(path):
    boundary = uuid.uuid4().hex
    data = open(path, "rb").read()
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"familie-figuren.png\"\r\n"
            f"Content-Type: image/png\r\n\r\n").encode() + data + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(f"{LOCAL}/upload/image", data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    return json.loads(urllib.request.urlopen(req).read())["name"]


PROMPT = """Hand-drawn 2D cartoon animation in the exact ink-and-watercolor style of <Picture 1>: thin scratchy black outlines, soft flat colors, plain off-white background, exaggerated long-nosed characters.

Characters from <Picture 1>, same faces, hair and clothes: the tall gangly father in the navy shirt and olive trousers, the mother with the messy blonde bun and mustard trousers, the teenage daughter in the red hoodie with headphones, the little blonde daughter in the heart T-shirt, the young son with the red cap and backpack. Only these five, each appears exactly once.

Timeline:
[0s-1.5s] The family stands in a row around a large paper sketch of a simple house lying on the floor. The father leans down, stretching his long body like rubber, scratching his chin.
[1.5s-3.5s] The little daughter jumps up with strong squash and stretch, pointing at the sketch; the son bounces on his toes; the mother laughs with her hands on her hips; the teenager rolls her eyes, then smiles.
[3.5s-5s] All five turn toward the viewer and freeze in an expectant pose, as if asking a question. Hold the last pose.

Bouncy classic cartoon timing, squash and stretch, smooth motion, static camera, no cuts.
Audio: light playful ukulele and soft footsteps, no speech.
No text, no letters, no extra people, no duplicate characters."""


def build(ref_name, PROMPT, prefix, seed=7, w=960, h=544, length=124, steps=20):
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_h3_fl2va_pruned_int8_convrot.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "type": "minimax", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_fp16.safetensors"}},
        "4": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}},
        "5": {"class_type": "LoadImage", "inputs": {"image": ref_name}},
        "6": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {
            "clip": ["2", 0], "prompt": PROMPT, "width": w, "height": h, "length": length,
            "ref_image_size": "match", "vae": ["3", 0], "audio_vae": ["4", 0],
            "ref_images.ref_image_1": ["5", 0]}},
        "7": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed, "control_after_generate": "fixed"}},
        "8": {"class_type": "BasicGuider", "inputs": {"model": ["1", 0], "conditioning": ["6", 0]}},
        "9": {"class_type": "KSamplerSelect", "inputs": {"sampler_name": "res_multistep"}},
        "10": {"class_type": "BasicScheduler", "inputs": {"model": ["1", 0], "scheduler": "simple", "steps": steps, "denoise": 1.0}},
        "11": {"class_type": "SamplerCustomAdvanced", "inputs": {"noise": ["7", 0], "guider": ["8", 0], "sampler": ["9", 0], "sigmas": ["10", 0], "latent_image": ["6", 1]}},
        "12": {"class_type": "VAEDecode", "inputs": {"samples": ["11", 0], "vae": ["3", 0]}},
        "13": {"class_type": "VAEDecodeAudio", "inputs": {"samples": ["11", 0], "vae": ["4", 0]}},
        "14": {"class_type": "CreateVideo", "inputs": {"images": ["12", 0], "audio": ["13", 0], "fps": 24.0}},
        "15": {"class_type": "SaveVideo", "inputs": {"video": ["14", 0], "filename_prefix": prefix, "format": "mp4", "codec": "h264"}},
    }


def main():
    cfg = json.load(open(os.path.join(HERE, "szenen.json"), encoding="utf-8-sig"))
    nur = sys.argv[1:]
    name = upload(SHEET)
    jobs = []
    # Mit Szenen-IDs als Argumente: nur diese, in dieser Reihenfolge.
    szenen = ([s for i in nur for s in cfg["szenen"] if s["id"] == i] if nur else cfg["szenen"])
    for s in szenen:
        ziel = os.path.join(HERE, "clips", s["id"] + ".mp4")
        if (nur and s["id"] not in nur) or (not nur and os.path.exists(ziel)):
            continue
        wf = build(name, prompt_bauen.prompt(cfg, s), "video/fragebogen-" + s["id"])
        if s.get("bewegung_von"):
            # Bewegung aus einem frueheren Clip (<Video 1>), Aussehen weiter
            # aus dem Figurenblatt (<Picture 1>).
            ziel_name = "bewegung-" + s["id"] + ".mp4"
            shutil.copy(os.path.join(HERE, s["bewegung_von"]), os.path.join(os.path.dirname(OUT), "input", ziel_name))
            wf["20"] = {"class_type": "LoadVideo", "inputs": {"file": ziel_name}}
            wf["21"] = {"class_type": "GetVideoComponents", "inputs": {"video": ["20", 0]}}
            wf["6"]["inputs"]["ref_videos.ref_video_1"] = ["21", 0]
        req = urllib.request.Request(f"{LOCAL}/prompt", data=json.dumps({"prompt": wf}).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            pid = json.loads(urllib.request.urlopen(req).read())["prompt_id"]
        except urllib.error.HTTPError as e:
            sys.exit(e.read().decode()[:3000])
        jobs.append((pid, s["id"], ziel))
        print("eingereiht", s["id"], flush=True)
    os.makedirs(os.path.join(HERE, "clips"), exist_ok=True)
    offen = list(jobs)
    while offen:
        time.sleep(15)
        for job in list(offen):
            pid, sid, ziel = job
            h = json.loads(urllib.request.urlopen(f"{LOCAL}/history/{pid}").read())
            if pid not in h:
                continue
            offen.remove(job)
            st = h[pid].get("status", {})
            if st.get("status_str") != "success":
                print("FEHLER", sid, json.dumps(st)[:800], flush=True)
                continue
            datei = h[pid]["outputs"]["15"]["images"][0]
            shutil.copy(os.path.join(OUT, datei["subfolder"], datei["filename"]), ziel)
            print("fertig", sid, f"({len(jobs) - len(offen)}/{len(jobs)})", flush=True)


if __name__ == "__main__":
    main()
