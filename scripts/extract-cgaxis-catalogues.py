# Pull the official model renders out of the CGAxis volume PDFs.
#
# The identification problem: 741 converted models named cgaxis_models_22_07
# in folders called "22 BATHROOMS". Matching on measured size alone put a
# vanity unit where a bath belonged and an oven where a washing machine
# belonged, because size cannot tell you what a thing is.
#
# Every CGAxis volume ships a PDF catalogue, and they are already on F:. One
# page per model, numbered in the same order as the files, each carrying the
# official studio render as the largest embedded image. Extracting those gives
# a labelled picture of every model in the library — better than the grey
# previews rendered here, and free.
#
# Output: tmp/cgaxis-renders/<volume>/<number>.jpg
#
# Usage:
#   python scripts/extract-cgaxis-catalogues.py [library_root]

import io
import os
import re
import sys

from pypdf import PdfReader

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.dirname(HERE)
OUT_ROOT = os.path.join(REPO, "tmp", "cgaxis-renders")


def volume_number(folder):
    match = re.match(r"\s*(\d+)", folder)
    return match.group(1) if match else None


def page_number(reader, index):
    """The model number printed on the page, e.g. 001 -> 1.

    Falls back to page order. The two agree in every volume checked, but the
    printed number is what the filenames follow, so prefer it.
    """
    try:
        text = reader.pages[index].extract_text() or ""
    except Exception:                                    # noqa: BLE001
        return index + 1
    for line in text.splitlines():
        stripped = line.strip()
        if re.fullmatch(r"\d{3}", stripped):
            return int(stripped)
    return index + 1


def extract(pdf_path, out_dir):
    reader = PdfReader(pdf_path)
    os.makedirs(out_dir, exist_ok=True)
    written = 0
    for index in range(len(reader.pages)):
        page = reader.pages[index]
        try:
            images = list(page.images)
        except Exception:                                # noqa: BLE001
            continue
        if not images:
            continue
        # The studio render is far larger than the page furniture around it.
        largest = max(images, key=lambda item: len(item.data))
        if len(largest.data) < 8000:
            continue
        number = page_number(reader, index)
        extension = os.path.splitext(largest.name)[1] or ".jpg"
        target = os.path.join(out_dir, f"{number:02d}{extension}")
        with open(target, "wb") as handle:
            handle.write(largest.data)
        written += 1
    return written, len(reader.pages)


def main():
    root = sys.argv[1] if len(sys.argv) > 1 else "F:\\"
    total = 0
    for folder in sorted(os.listdir(root)):
        directory = os.path.join(root, folder)
        if not os.path.isdir(directory):
            continue
        pdfs = [f for f in os.listdir(directory) if f.lower().endswith(".pdf")]
        if not pdfs:
            continue
        number = volume_number(folder)
        out_dir = os.path.join(OUT_ROOT, folder)
        written, pages = extract(os.path.join(directory, pdfs[0]), out_dir)
        total += written
        print(f"[cgaxis] vol {number or '??':>3}  {folder:28} {written:3}/{pages} renders")
    print(f"[cgaxis] {total} model renders extracted to {OUT_ROOT}")


if __name__ == "__main__":
    main()
