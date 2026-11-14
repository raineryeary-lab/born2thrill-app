"""Clips, die nahtlos an einen anderen anschliessen (szenen.json: "folgt_auf").
Das letzte Bild des Vorgaengers wird als erstes Bild verankert
(MiniMaxH3AddGuide, frame 0), das Figurenblatt bleibt <Picture 1>.
Die Kamera darf hier zoomen, sonst gilt der Stil aus szenen.json.

    python kette-erzeugen.py 02b-budget-mittel 02c-budget-gross

Die Clips laufen nacheinander, weil jeder das Ende des vorigen braucht."""
import json, os, shutil, sys, time, urllib.request, uuid

import av  # liegt in der ComfyUI-Umgebung; mit deren python.exe starten

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import prompt_bauen
LOCAL = "http://127.0.0.1:8188"
OUT = r"E:/_comfyUI/ComfyUI/ComfyUI/output"


def upload(path, name):
    boundary = uuid.uuid4().hex
    body = (f"--{boundary}\r\nContent-Disposition: form-data; name=\"image\"; filename=\"{name}\"\r\n"
            f"Content-Type: image/png\r\n\r\n").encode() + open(path, "rb").read() + f"\r\n--{boundary}--\r\n".encode()
    req = urllib.request.Request(f"{LOCAL}/upload/image", data=body,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
    return json.loads(urllib.request.urlopen(req).read())["name"]


def letztes_bild(mp4, png):
    letztes = None
    with av.open(mp4) as c:
        for f in c.decode(video=0):
            letztes = f
    letztes.to_image().save(png)


def build(ref, start, prompt, prefix, seed=7, w=960, h=544, length=124, steps=20):
    return {
        "1": {"class_type": "UNETLoader", "inputs": {"unet_name": "minimax_h3_fl2va_pruned_int8_convrot.safetensors", "weight_dtype": "default"}},
        "2": {"class_type": "CLIPLoader", "inputs": {"clip_name": "qwen3vl_32b_minimax_h3_nvfp4_awq.safetensors", "type": "minimax", "device": "default"}},
        "3": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_video_vae_fp16.safetensors"}},
        "4": {"class_type": "VAELoader", "inputs": {"vae_name": "minimax_h3_audio_vae_fp32.safetensors"}},
        "5": {"class_type": "LoadImage", "inputs": {"image": ref}},
        "16": {"class_type": "LoadImage", "inputs": {"image": start}},
        "6": {"class_type": "MiniMaxH3ReferenceToVideo", "inputs": {
            "clip": ["2", 0], "prompt": prompt, "width": w, "height": h, "length": length,
            "ref_image_size": "match", "vae": ["3", 0], "audio_vae": ["4", 0],
            "ref_images.ref_image_1": ["5", 0]}},
        "17": {"class_type": "MiniMaxH3AddGuide", "inputs": {
            "positive": ["6", 0], "latent": ["6", 1], "frame_idx": 0, "vae": ["3", 0], "image": ["16", 0]}},
        "7": {"class_type": "RandomNoise", "inputs": {"noise_seed": seed, "control_after_generate": "fixed"}},
        "8": {"class_type": "BasicGuider", "inputs": {"model": ["1", 0], "conditioning": ["17", 0]}},
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
    szenen = {s["id"]: s for s in cfg["szenen"]}
    stil = cfg["stil"].replace("Static camera, no cuts.", "No cuts.")
    ref = upload(os.path.join(HERE, "familie-figuren.png"), "familie-figuren.png")
    for sid in sys.argv[1:]:
        s = szenen[sid]
        vor = os.path.join(HERE, "clips", s["folgt_auf"] + ".mp4")
        png = os.path.join(HERE, "clips", s["folgt_auf"] + "-ende.png")
        letztes_bild(vor, png)
        start = upload(png, os.path.basename(png))
        wf = build(ref, start, prompt_bauen.prompt(cfg, s, stil), "video/fragebogen-" + sid)
        req = urllib.request.Request(f"{LOCAL}/prompt", data=json.dumps({"prompt": wf}).encode(),
                                     headers={"Content-Type": "application/json"})
        try:
            pid = json.loads(urllib.request.urlopen(req).read())["prompt_id"]
        except urllib.error.HTTPError as e:
            sys.exit(e.read().decode()[:3000])
        print("laeuft", sid, flush=True)
        while True:
            time.sleep(15)
            h = json.loads(urllib.request.urlopen(f"{LOCAL}/history/{pid}").read())
            if pid in h:
                break
        st = h[pid].get("status", {})
        if st.get("status_str") != "success":
            sys.exit(f"FEHLER {sid} {json.dumps(st)[:800]}")
        datei = h[pid]["outputs"]["15"]["images"][0]
        shutil.copy(os.path.join(OUT, datei["subfolder"], datei["filename"]), os.path.join(HERE, "clips", sid + ".mp4"))
        print("fertig", sid, flush=True)


if __name__ == "__main__":
    main()
