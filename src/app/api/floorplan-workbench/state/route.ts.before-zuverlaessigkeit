/**
 * One truthful state per house, with its blocker and its single next action.
 *
 * Codex ranked this first for getting from 1 finished house to 50: "Authoritative
 * per-house state machine/dashboard with truthful blockers and finish status."
 *
 * "Finished" is not "rendered". It is: searchable in the catalogue, images
 * uploaded, EVERY image released to customers, and the plan approved. Codex,
 * on the last two: "Automated verification approves geometry integrity — not
 * customer suitability." So they stay human, and this only reports them.
 *
 * The states are ordered so the list reads as a queue: the closest to finished
 * first, the impossible last.
 */
import { readdir, readFile, stat } from "node:fs/promises";
import { angenommenerOrdner } from "@/lib/floorplan-workbench/angenommener-ordner.mjs";
import { join, resolve } from "node:path";
import { spawn } from "node:child_process";
import { deriveHouseState, STATES, naechsteFertigVersion } from "@/lib/floorplan-workbench/house-state.mjs";
import { createHash } from "node:crypto";
import { rename, writeFile } from "node:fs/promises";
import { hausdaten } from "@/lib/floorplan-workbench/hausdaten.mjs";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const SITE = (process.env.B2T_SITE || "https://born2thrill.de").replace(/\/+$/, "");
const RASTER = [".png", ".jpg", ".jpeg", ".pdf"];

// STATES und die Ableitung leben in src/lib/floorplan-workbench/house-state.mjs
// -- eine Wahrheit fuer Liste, Knoepfe und Batch (Codex-Audit P0, Ralph-Item 1).
type State = (typeof STATES)[number];

function alignmentComplete(annotation: any, levels: string[], ground: string) {
  const marks = annotation?.floor_alignment || {};
  if (!Array.isArray(marks[ground]) || marks[ground].length !== 2) return false;
  return levels.every((level) => Array.isArray(marks[level]) && marks[level].length === 2);
}

function normalizedHostname(value: string) {
  const first = value.split(",")[0]?.trim().toLowerCase() || "";
  if (first.startsWith("[")) return first.slice(1, first.indexOf("]"));
  return first.split(":")[0];
}

function enabled(request: Request) {
  const urlHost = new URL(request.url).hostname.toLowerCase();
  const headerHost = normalizedHostname(
    request.headers.get("x-forwarded-host") || request.headers.get("host") || "",
  );
  return process.env.FLOORPLAN_WORKBENCH_ENABLED === "true"
    && ["127.0.0.1", "localhost", "::1"].includes(urlHost)
    && ["127.0.0.1", "localhost", "::1"].includes(headerHost);
}

async function hasRaster(folder: string) {
  try {
    return (await readdir(folder)).some((e) => RASTER.some((x) => e.toLowerCase().endsWith(x)));
  } catch {
    return false;
  }
}

async function countBlends(folder: string) {
  try {
    return (await readdir(folder)).filter((n) => n.endsWith(".blend")).length;
  } catch {
    return 0;
  }
}

/** Wie viele Bilder haengen am Plan -- unabhaengig davon, ob freigegeben. */
/** Wieviele Bilder liegen in der Mediathek, und wieviele sind angehakt?
 *  null = WordPress war nicht erreichbar. Das ist ETWAS ANDERES als "keine
 *  Bilder": aus einem Timeout wurde vorher "warten_auf_codex" samt der
 *  Empfehlung, alles neu hochzuladen (Codex, 2026-08-20, P0). */
async function bilderStand(plan: string) {
  try {
    const r = await fetch(`${SITE}/wp-json/b2t/v1/bilder?plan=${encodeURIComponent(plan)}`,
      { cache: "no-store" });
    if (!r.ok) return null;
    const rows = await r.json();
    const liste = Array.isArray(rows) ? rows : [];
    return { hochgeladen: liste.length,
             freigegeben: liste.filter((b: any) => b.send === true).length };
  } catch {
    return null;
  }
}

/** Zertifikat + Frische fuer alle Haeuser, aus DERSELBEN Python-Quelle wie
 *  go.py (batch-build.built_hash/annotation_state). Ein Prozess fuer den
 *  ganzen Bestand; faellt er aus, bleibt das Feld null und die Ableitung
 *  behandelt es als "nicht zertifiziert" statt still als "fertig". */
async function lieferzustand(suite: string) {
  const python = process.env.PYTHON_EXECUTABLE || "python";
  const script = join(suite, "born2thrill-local-workbench", "scripts", "haus-zustand.py");
  return new Promise<Record<string, { zertifikat: boolean; aktuell: boolean; grund: string; nur_renderer?: boolean }>>(
    (fertig) => {
      let out = "";
      const kind = spawn(python, [script, "--alle"], { cwd: join(suite, "born2thrill-local-workbench") });
      kind.stdout.on("data", (c) => { if (out.length < 4_000_000) out += String(c); });
      kind.on("error", () => fertig({}));
      kind.on("close", () => {
        try { fertig(JSON.parse(out)); } catch { fertig({}); }
      });
    });
}

/** Fertige Codex-Bilder, die lokal liegen (renders/codex-final-*). */
async function finalsLokal(dataRoot: string, plan: string) {
  const renders = join(dataRoot, "corrections", plan, "renders");
  try {
    // Dieselbe Stelle wie im Bilder-Tab. Rainer, 2026-08-29: "i do not
    // understand how there can be any confusion into where the stuff is
    // saved" -- die Verwirrung kam daher, dass diese Frage an vier Stellen
    // eigenstaendig beantwortet wurde. Jetzt nur noch an einer.
    const neuester = await angenommenerOrdner(renders);
    if (!neuester) return 0;
    return (await readdir(join(renders, neuester)))
      .filter((n) => /\.(png|jpg|jpeg|webp)$/i.test(n) && !n.startsWith("reference-")).length;
  } catch {
    return 0;
  }
}

export async function GET(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });

  const suite = resolve(process.cwd(), "..");
  const projects = join(suite, "floorplan-simplifier", "projects");
  // Nicht raten. 2026-08-21: der Datenordner zog von C: nach E:; ein
  // stiller Rueckfall auf den alten C:-Nachbarordner wuerde unbemerkt
  // gegen veraltete Daten arbeiten (Codex-Review desselben Tages).
  const _konfiguriert = process.env.FLOORPLAN_WORKBENCH_DATA_DIR?.trim();
  if (!_konfiguriert) {
    throw new Error("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt -- "
      + "verweigere, den Datenordner zu erraten. Siehe .env.local.");
  }
  const dataRoot = resolve(_konfiguriert);

  // The catalogue is the only place that knows what is published and approved.
  let published: Record<string, { images: number; released: number; approved: string }> = {};
  try {
    const rows = await fetch(`${SITE}/wp-json/b2t/v1/grundrisse`, { cache: "no-store" })
      .then((r) => (r.ok ? r.json() : []));
    for (const row of rows as { id: string; im: number; ok: string }[]) {
      published[row.id] = { images: row.im || 0, released: 0, approved: row.ok || "offen" };
    }
  } catch {
    published = {};
  }

  let names: string[] = [];
  try {
    names = await readdir(projects);
  } catch {
    return Response.json({ error: `cannot read ${projects}` }, { status: 500 });
  }

  const lieferung = await lieferzustand(suite);

  // FERTIG-BLEIBT-FERTIG-001 (Rainer, 2026-10-07): once fertig, a house stays
  // fertig. The ledger remembers every house that reached it, with a version.
  const ledgerPfad = join(dataRoot, "fertig-ledger.json");
  let ledger: Record<string, { version: string; seit: string; zuletzt: string; build: string }> = {};
  try { ledger = JSON.parse(await readFile(ledgerPfad, "utf8")); } catch { ledger = {}; }
  let ledgerGeaendert = false;

  const houses = [];
  for (const plan of names) {
    const folder = join(projects, plan);
    // Massstab und Dachform stehen je nach Haus in der Annotation ODER im
    // Sidecar gebaeudemass.json. Zusammengefuehrt wird das nur an einer
    // Stelle, mit derselben Vorrangregel wie der Bau:
    // src/lib/floorplan-workbench/hausdaten.mjs.
    const daten = await hausdaten(folder);
    const annotation = daten.annotationen;
    if (!annotation) continue;

    const rooms = (annotation.annotations as any[]) || [];
    const levels: string[] = Array.from(new Set(rooms.map((r) => r?.floor_level).filter(Boolean)));
    const scale = daten.floor_scale;
    const ground = levels.includes("groundfloor") ? "groundfloor" : levels[0];
    const raster = await hasRaster(folder);

    const renders = join(dataRoot, "corrections", plan, "renders", "go-baseline");
    const blends = await countBlends(renders);
    const catalogue = published[plan];

    const frisch = lieferung[plan] || { zertifikat: false, aktuell: false, grund: "" };
    // WordPress nur fuer Haeuser fragen, deren Lieferung aktuell ist: eine
    // Abfrage pro Haus ueber alle 234 machte aus der Statusroute einen
    // 120-Sekunden-Haenger (2026-08-20).
    const wordpress = frisch.aktuell ? await bilderStand(plan) : null;
    const abgeleitet = deriveHouseState({
      raster,
      rooms: rooms.length,
      levels,
      scale,
      // Nur die Vermessung selbst -- die Dachform gehoert nicht in die
      // Massstabs-Pruefung, das war der vierte Vorrang-Sonderweg.
      gebaeudemass: daten.hat_gebaeudemass,
      alignmentComplete: alignmentComplete(annotation, levels, ground),
      zertifikat: frisch.zertifikat,
      aktuell: frisch.aktuell,
      aktuellGrund: frisch.grund,
      nurRenderer: (frisch as any).nur_renderer === true,
      blends,
      finalsLokal: frisch.aktuell ? await finalsLokal(dataRoot, plan) : 0,
      wordpress: frisch.aktuell
        ? (wordpress === null
            ? { erreichbar: false }
            : { erreichbar: true, hochgeladen: wordpress.hochgeladen,
                freigegeben: wordpress.freigegeben })
        : null,
      catalogue: catalogue ? { images: catalogue.images, approved: catalogue.approved } : null,
      fertigLedger: ledger[plan] || null,
    }, plan);

    // Record / move up the version. "fertig" on a different certified build
    // than recorded is the next minor version; a house already published
    // (veroeffentlicht_build_alt) when the ledger first sees it starts at 1.0.
    if (abgeleitet.state === "fertig" || (!ledger[plan] && abgeleitet.state === "veroeffentlicht_build_alt")) {
      let build = "";
      try {
        build = createHash("sha256")
          .update(await readFile(join(renders, "delivery-manifest.json")))
          .digest("hex").slice(0, 16);
      } catch { build = ""; }
      const vorher = ledger[plan];
      const naechste = naechsteFertigVersion(vorher || null, build);
      if (!vorher || naechste.version !== vorher.version || (!vorher.build && build)) {
        const jetzt = new Date().toISOString();
        ledger[plan] = { version: naechste.version, seit: vorher?.seit || jetzt, zuletzt: jetzt,
                         build: naechste.build || build };
        ledgerGeaendert = true;
      }
      (abgeleitet as any).version = ledger[plan].version;
    }
    const state = abgeleitet.state as State;
    const blocker = abgeleitet.blocker;
    const action = abgeleitet.action;
    const bilder = wordpress;

    houses.push({
      plan, state, blocker, action,
      version: (abgeleitet as any).version || null,
      floors: levels.length,
      scale_missing: levels.filter((l) => !scale[l]),
      blends,
      catalogue_images: catalogue?.images ?? 0,
      approved: catalogue?.approved ?? null,
      in_catalogue: Boolean(catalogue),
    });
  }

  houses.sort((a, b) => STATES.indexOf(a.state) - STATES.indexOf(b.state)
    || a.plan.localeCompare(b.plan));

  if (ledgerGeaendert) {
    // write-then-rename: a crash mid-write must never leave a half ledger,
    // because the ledger is the only memory of "fertig".
    const tmp = `${ledgerPfad}.${process.pid}.tmp`;
    await writeFile(tmp, JSON.stringify(ledger, null, 2), "utf8");
    await rename(tmp, ledgerPfad);
  }

  const counts: Record<string, number> = {};
  for (const house of houses) counts[house.state] = (counts[house.state] || 0) + 1;

  return Response.json({ total: houses.length, counts, houses },
    { headers: { "Cache-Control": "no-store" } });
}
