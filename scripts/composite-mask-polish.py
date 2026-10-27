"""Composite the geometry-safe ComfyUI pass and the atmospheric ComfyUI pass
using the Blender structure mask: building pixels come from the safe pass
(low denoise, high ControlNet -- doesn't hallucinate windows/doors), sky and
ground pixels come from the atmospheric pass (high denoise -- real clouds,
grass texture, light). Feathered blend at the mask edge so the seam doesn't
read as a hard cutout.

Usage: composite-mask-polish.py <safe.png> <atmo.png> <mask.png> <out.png>
"""
import sys
from PIL import Image, ImageFilter

safe_path, atmo_path, mask_path, out_path = sys.argv[1:5]

safe = Image.open(safe_path).convert("RGB")
atmo = Image.open(atmo_path).convert("RGB").resize(safe.size)
mask = Image.open(mask_path).convert("L").resize(safe.size)
# Feather the mask edge so the safe/atmospheric seam blends instead of
# reading as a cutout paste.
mask = mask.filter(ImageFilter.GaussianBlur(radius=6))

out = Image.composite(safe, atmo, mask)
out.save(out_path)
print(f"wrote {out_path}")
