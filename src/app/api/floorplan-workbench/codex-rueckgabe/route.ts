/**
 * Codex-Rueckgabe finden und einlesen -- ohne Pfade durch den Chat zu tragen.
 *
 * Rainer, 2026-08-23: "i would like to add the path to the images and all the
 * stuff from codex into our workflow, not always have to go through this
 * frame". Bisher lieferte Codex in seinen eigenen Ordner
 * (%USERPROFILE%\.codex\visualizations\...\<plan>-<irgendwas>\) und jemand
 * musste den Pfad von Hand weiterreichen und die Dateien kopieren.
 *
 * GET  ?plan=<id>   -> gefundene Rueckgabe-Ordner (und ZIPs) fuer diesen Plan
 * POST {plan, quelle} -> kopiert die Bilder nach
 *                        corrections/<plan>/renders/codex-final-<stempel>/
 *
 * Eingelesen wird NUR in den lokalen Lieferordner. Hochladen und Freigeben
 * bleiben eigene, ausdrueckliche Schritte -- diese Route veroeffentlicht
 * nichts.
 */
import { spawn } from "node:child_process";
import { copyFile, mkdir, readdir, readFile, stat, writeFile } from "node:fs/promises";
import { basename, extname, join, resolve } from "node:path";
import { homedir } from "node:os";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const BILD = new Set([".png", ".jpg", ".jpeg", ".webp"]);
const PLAN_OK = /^[A-Za-z0-9_.-]+$/;

function normalizedHostname(value: string) {
  const first = value.split(",")[0]?.trim().toLowerCase() || "";
  if (first.startsWith("[")) return first.slice(1, first.indexOf("]"));
  return first.split(":")[0];
}

function enabled(request: Request) {
  const urlHost = new URL(request.url).hostname.toLowerCase();
  const headerHost = normalizedHostname(request.headers.get("host") || "");
  const erlaubt = new Set(["localhost", "127.0.0.1", "::1"]);
  return erlaubt.has(urlHost) && (!headerHost || erlaubt.has(headerHost));
}

function dataRoot() {
  const konfiguriert = process.env.FLOORPLAN_WORKBENCH_DATA_DIR?.trim();
  if (!konfiguriert) throw new Error("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt.");
  return resolve(konfiguriert);
}

/** Wo Codex ablegt. Zusaetzliche Orte per FLOORPLAN_CODEX_DIRS (mit ; getrennt). */
function suchorte() {
  const orte = [join(homedir(), ".codex", "visualizations")];
  for (const extra of (process.env.FLOORPLAN_CODEX_DIRS || "").split(";")) {
    if (extra.trim()) orte.push(resolve(extra.trim()));
  }
  return orte;
}

async function bilderIn(ordner: string) {
  try {
    return (await readdir(ordner)).filter((n) => {
      const stem = basename(n, extname(n));
      // Codex' eigene Zwischenstaende gehoeren nicht in die Lieferung:
      // source-*, sowie Reparatur-/Umkodier-Varianten davon.
      const zwischenstand = /^(reference|source)-/.test(stem)
        || /-(reencoded|repaired|clean|pillow|raw)$/.test(stem);
      return BILD.has(extname(n).toLowerCase()) && !zwischenstand;
    });
  } catch {
    return [];
  }
}

/** Ordner (und ZIPs), deren Name den Plan nennt -- hoechstens `tiefe` Ebenen tief. */
async function suchen(plan: string, wurzel: string, tiefe = 4) {
  const treffer: { pfad: string; name: string; bilder: number; zeit: string; typ: string }[] = [];
  async function gehe(ordner: string, rest: number) {
    let eintraege: string[] = [];
    try {
      eintraege = await readdir(ordner);
    } catch {
      return;
    }
    for (const eintrag of eintraege) {
      const voll = join(ordner, eintrag);
      let info;
      try {
        info = await stat(voll);
      } catch {
        continue;
      }
      const passt = eintrag.toLowerCase().includes(plan.toLowerCase());
      if (info.isDirectory()) {
        if (passt) {
          const bilder = await bilderIn(voll);
          if (bilder.length) {
            treffer.push({ pfad: voll, name: eintrag, bilder: bilder.length,
                           zeit: info.mtime.toISOString(), typ: "ordner" });
          }
        }
        if (rest > 0) await gehe(voll, rest - 1);
      } else if (passt && extname(eintrag).toLowerCase() === ".zip") {
        treffer.push({ pfad: voll, name: eintrag, bilder: 0,
                       zeit: info.mtime.toISOString(), typ: "zip" });
      }
    }
  }
  await gehe(wurzel, tiefe);
  return treffer;
}

export async function GET(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const plan = new URL(request.url).searchParams.get("plan") || "";
  if (!PLAN_OK.test(plan)) return Response.json({ error: "plan fehlt/ungueltig" }, { status: 400 });
  const gefunden: any[] = [];
  for (const ort of suchorte()) gefunden.push(...await suchen(plan, ort));
  gefunden.sort((a, b) => b.zeit.localeCompare(a.zeit));
  return Response.json({ plan, gefunden: gefunden.slice(0, 12) },
                       { headers: { "Cache-Control": "no-store" } });
}

export async function POST(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const body = await request.json().catch(() => ({}));
  const plan = String(body.plan || "");
  const quelle = String(body.quelle || "");
  if (!PLAN_OK.test(plan)) return Response.json({ error: "plan fehlt/ungueltig" }, { status: 400 });

  // Die Quelle muss aus einem der bekannten Suchorte stammen -- sonst koennte
  // ein praeparierter Aufruf beliebige Dateien in die Lieferung kopieren.
  const erlaubt = suchorte().some((ort) => resolve(quelle).startsWith(resolve(ort)));
  if (!erlaubt) return Response.json({ error: "Quelle liegt ausserhalb der Codex-Ordner" },
                                     { status: 400 });

  const stempel = new Date().toISOString().slice(0, 16).replace(/[:T]/g, "").replace(/-/g, "-");
  const ziel = join(dataRoot(), "corrections", plan, "renders", `codex-final-${stempel}`);
  await mkdir(ziel, { recursive: true });

  let quellordner = quelle;
  if (extname(quelle).toLowerCase() === ".zip") {
    // Entpacken mit dem Python, das ohnehin im Projekt laeuft -- kein
    // zusaetzliches Node-Paket nur fuer ZIP.
    const python = process.env.FLOORPLAN_PYTHON?.trim() || process.env.PYTHON_EXECUTABLE || "python";
    const code = `import zipfile,sys;zipfile.ZipFile(sys.argv[1]).extractall(sys.argv[2])`;
    const ok = await new Promise<boolean>((fertig) => {
      const kind = spawn(python, ["-c", code, quelle, ziel]);
      kind.on("error", () => fertig(false));
      kind.on("close", (c) => fertig(c === 0));
    });
    if (!ok) return Response.json({ error: "ZIP konnte nicht entpackt werden" }, { status: 500 });
    quellordner = "";
  }

  let kopiert = 0;
  if (quellordner) {
    for (const name of await bilderIn(quellordner)) {
      await copyFile(join(quellordner, name), join(ziel, name));
      kopiert += 1;
    }
    try {
      await copyFile(join(quellordner, "catalog.json"), join(ziel, "catalog.json"));
    } catch { /* ohne catalog.json geht es auch */ }
  } else {
    kopiert = (await bilderIn(ziel)).length;
  }

  // Woher kam das? Steht neben den Bildern, damit spaeter nachvollziehbar
  // bleibt, welche Rueckgabe eingelesen wurde.
  await writeFile(join(ziel, "herkunft.json"),
                  JSON.stringify({ quelle, eingelesen_am: new Date().toISOString(), bilder: kopiert },
                                 null, 2), "utf8");
  return Response.json({ ok: true, plan, ziel, bilder: kopiert });
}
