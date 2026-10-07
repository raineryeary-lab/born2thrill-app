# Batch-convert CGAxis .c4d models to .fbx so Blender can import them.
#
# Cinema 4D R19 has no headless Python (c4dpy arrived in R21), so this runs
# inside the C4D GUI:
#
#   Script menu -> Script Manager  (Shift+F11)
#   File -> Open... this file, or paste it in
#   Execute
#
# It then runs unattended. Progress goes to the Console (Script -> Console).
#
# R19's Python is 2.7 — no f-strings, no pathlib.
#
# Safe to re-run: files that already exist in the output tree are skipped, so
# an interrupted run resumes instead of redoing work.

import c4d
import json
import os
import time
from c4d import documents, plugins

SOURCE_ROOT = r"F:\\"
OUTPUT_ROOT = r"E:\_models_converted"
MANIFEST = os.path.join(OUTPUT_ROOT, "conversion-manifest.json")

FBX_EXPORTER_ID = 1026370

SKIP_DIRS = ("System Volume Information", ".Trashes", "$RECYCLE.BIN")


def configure_exporter():
    """Set FBX export options. Constants vary between C4D versions, so each
    one is set defensively rather than assuming R19 has it."""
    plug = plugins.FindPlugin(FBX_EXPORTER_ID, c4d.PLUGINTYPE_SCENESAVER)
    if plug is None:
        print("WARNING: FBX exporter plugin not found; using defaults")
        return

    data = {}
    if not plug.Message(c4d.MSG_RETRIEVEPRIVATEDATA, data):
        return
    settings = data.get("imexporter", None)
    if settings is None:
        return

    wanted = [
        ("FBXEXPORT_TEXTURES", True),
        ("FBXEXPORT_EMBED_TEXTURES", True),
        ("FBXEXPORT_MATERIALS", True),
        ("FBXEXPORT_SAVE_NORMALS", True),
        ("FBXEXPORT_TRIANGULATE", False),
        ("FBXEXPORT_SELECTION_ONLY", False),
        ("FBXEXPORT_CAMERAS", False),
        ("FBXEXPORT_LIGHTS", False),
        ("FBXEXPORT_SPLINES", False),
        ("FBXEXPORT_ASCII", False),
    ]
    for name, value in wanted:
        constant = getattr(c4d, name, None)
        if constant is None:
            continue
        try:
            settings[constant] = value
        except Exception:
            pass


def find_sources():
    found = []
    for folder, dirs, files in os.walk(SOURCE_ROOT):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        for name in files:
            if name.lower().endswith(".c4d"):
                found.append(os.path.join(folder, name))
    found.sort()
    return found


def output_path_for(source):
    """Mirror the source folder structure so the category organisation that
    makes F:\\ useful (BATHROOMS, KITCHEN APPLIANCES, BEDROOMS...) survives."""
    relative = os.path.relpath(source, SOURCE_ROOT)
    target = os.path.join(OUTPUT_ROOT, relative)
    return os.path.splitext(target)[0] + ".fbx"


def main():
    configure_exporter()
    sources = find_sources()
    total = len(sources)
    print("found %d .c4d files under %s" % (total, SOURCE_ROOT))
    print("writing to %s" % OUTPUT_ROOT)

    records = []
    converted = 0
    skipped = 0
    failed = []
    started = time.time()

    for index, source in enumerate(sources, 1):
        target = output_path_for(source)

        if os.path.isfile(target):
            skipped += 1
            records.append({
                "source": source,
                "output": target,
                "category": os.path.relpath(source, SOURCE_ROOT).split(os.sep)[0],
                "status": "already_present",
            })
            continue

        folder = os.path.dirname(target)
        if not os.path.isdir(folder):
            os.makedirs(folder)

        try:
            doc = documents.LoadDocument(
                source,
                c4d.SCENEFILTER_OBJECTS | c4d.SCENEFILTER_MATERIALS,
            )
            if doc is None:
                raise RuntimeError("LoadDocument returned None")

            ok = documents.SaveDocument(
                doc,
                target,
                c4d.SAVEDOCUMENTFLAGS_DONTADDTORECENTLIST,
                FBX_EXPORTER_ID,
            )
            if not ok:
                raise RuntimeError("SaveDocument returned False")

            converted += 1
            records.append({
                "source": source,
                "output": target,
                "category": os.path.relpath(source, SOURCE_ROOT).split(os.sep)[0],
                "status": "converted",
                "bytes": os.path.getsize(target) if os.path.isfile(target) else 0,
            })
        except Exception as error:
            failed.append((source, str(error)))
            records.append({
                "source": source,
                "output": target,
                "category": os.path.relpath(source, SOURCE_ROOT).split(os.sep)[0],
                "status": "failed",
                "error": str(error),
            })

        if index % 25 == 0 or index == total:
            elapsed = time.time() - started
            rate = index / elapsed if elapsed > 0 else 0
            remaining = (total - index) / rate if rate > 0 else 0
            print("[%d/%d] converted %d, skipped %d, failed %d — ~%d min left"
                  % (index, total, converted, skipped, len(failed), remaining / 60))

        c4d.EventAdd()

    if not os.path.isdir(OUTPUT_ROOT):
        os.makedirs(OUTPUT_ROOT)
    handle = open(MANIFEST, "w")
    json.dump({
        "source_root": SOURCE_ROOT,
        "output_root": OUTPUT_ROOT,
        "total": total,
        "converted": converted,
        "skipped": skipped,
        "failed": len(failed),
        "items": records,
    }, handle, indent=2)
    handle.close()

    print("")
    print("done: %d converted, %d already present, %d failed"
          % (converted, skipped, len(failed)))
    print("manifest: %s" % MANIFEST)
    for source, error in failed[:20]:
        print("  FAILED %s — %s" % (source, error))


main()
