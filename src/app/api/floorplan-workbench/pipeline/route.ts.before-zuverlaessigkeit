/**
 * Die Pipeline-Schritte als API, damit sie in der Seite liegen statt in einer
 * zweiten Oberflaeche auf Port 8800.
 *
 * Codex, 2026-08-20, zum Umbau auf EINEN Ablauf: "Python-Webtool nicht
 * einbetten: seine Funktionen werden Backend-API bzw. Job-Runner: build,
 * register, upload, release, status. Next.js zeigt Buttons, Fortschritt, Logs
 * und Fehler direkt im jeweiligen Schritt."
 *
 * Die bestehenden Skripte werden unveraendert als Prozesse gestartet -- go.py
 * kann ein Haus schon so weit treiben, wie es ohne Menschen geht, und
 * approve-plan.py ist die Rechteerklaerung. Hier kommt nur die Huelle dazu.
 *
 * `freigeben` verlangt eine Begruendung und laesst sich nicht mit einem
 * Standardtext ueberspringen: es ist eine Rechteerklaerung, keine Routine.
 */
import { spawn } from "node:child_process";
import { readdir } from "node:fs/promises";
import { join, resolve } from "node:path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const SCHRITTE = ["bauen", "hochladen", "freigeben", "regenerieren", "codex", "treppe"] as const;
type Schritt = (typeof SCHRITTE)[number];

function normalizedHostname(value: string) {
  const first = value.split(",")[0]?.trim().toLowerCase() || "";
  if (first.startsWith("[")) return first.slice(1, first.indexOf("]"));
  return first.split(":")[0];
}

/** Nur lokal. Dieselbe Schranke wie die anderen Workbench-Routen. */
function enabled(request: Request) {
  const urlHost = new URL(request.url).hostname.toLowerCase();
  const headerHost = normalizedHostname(
    request.headers.get("x-forwarded-host") || request.headers.get("host") || "",
  );
  return process.env.FLOORPLAN_WORKBENCH_ENABLED === "true"
    && ["127.0.0.1", "localhost", "::1"].includes(urlHost)
    && ["127.0.0.1", "localhost", "::1"].includes(headerHost);
}

/** Der Plan muss existieren -- sonst startet niemand einen Blender-Lauf. */
async function planExists(suite: string, plan: string) {
  if (!/^[A-Za-z0-9_.-]+$/.test(plan)) return false;
  try {
    const namen = await readdir(join(suite, "floorplan-simplifier", "projects"));
    return namen.includes(plan);
  } catch {
    return false;
  }
}

function lauf(befehl: string, args: string[], cwd: string) {
  return new Promise<{ code: number; ausgabe: string }>((fertig) => {
    const kind = spawn(befehl, args, { cwd, windowsHide: true });
    let ausgabe = "";
    const sammeln = (d: Buffer) => { ausgabe += d.toString("utf8"); };
    kind.stdout.on("data", sammeln);
    kind.stderr.on("data", sammeln);
    kind.on("close", (code) => fertig({ code: code ?? -1, ausgabe }));
    kind.on("error", (e) => fertig({ code: -1, ausgabe: String(e) }));
  });
}

export async function POST(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });

  const body = await request.json().catch(() => ({}));
  const plan = String(body.plan || "");
  const schritt = String(body.schritt || "") as Schritt;
  const grund = String(body.grund || "").trim();
  const trotzTreppe = body.trotzTreppe === true;

  if (!SCHRITTE.includes(schritt)) {
    return Response.json({ error: `Unbekannter Schritt: ${schritt}` }, { status: 400 });
  }
  const suite = resolve(process.cwd(), "..");
  if (!(await planExists(suite, plan))) {
    return Response.json({ error: `Kein Projekt: ${plan}` }, { status: 400 });
  }
  if (schritt === "freigeben" && !grund) {
    return Response.json(
      { error: "Ohne Begruendung keine Freigabe -- das ist eine Rechteerklaerung." },
      { status: 400 },
    );
  }

  // Werden Raeume oder Aussenanlagen umgezeichnet, ist die gespeicherte
  // Korrektur-Revision auf eine Geometrie gebaut, die es nicht mehr gibt --
  // und die Moebel stehen mit ihr in der Luft. Rainer, 2026-08-20: "when
  // changes are made in the Raeume and exteriours then the data has to be
  // regenerated for the furnishing."
  //
  // Regenerieren heisst: die HEUTIGE Annotation noch einmal durch /generate
  // schicken und das Ergebnis als neuen Entwurf ablegen. Die gesetzten Moebel
  // liegen in eigenen Dateien (furniture/floor-N.json) und bleiben unberuehrt
  // -- sie sollen ja erhalten bleiben, nur eben auf der neuen Geometrie.
  if (schritt === "regenerieren") {
    const basis = new URL(request.url);
    const genUrl = new URL(basis.toString());
    genUrl.pathname = "/api/floorplan-workbench/generate";
    genUrl.search = `?reference=${encodeURIComponent(plan)}&transform=identity`;
    const gen = await fetch(genUrl.toString(), { cache: "no-store" });
    const frisch = await gen.json();
    if (!gen.ok || !frisch.candidate) {
      return Response.json(
        { ok: false, ausgabe: frisch.error || "Konnte die Geometrie nicht neu erzeugen." },
        { status: 400 },
      );
    }
    const korrUrl = new URL(basis.toString());
    korrUrl.pathname = "/api/floorplan-workbench/corrections";
    korrUrl.search = "";
    const speichern = await fetch(korrUrl.toString(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "save_draft", document: frisch.candidate }),
    });
    const ergebnis = await speichern.json();
    return Response.json({
      ok: speichern.ok && ergebnis.ok !== false,
      ausgabe: speichern.ok
        ? `Geometrie neu erzeugt (geometry_hash ${String(frisch.geometry_hash || "").slice(0, 16)}).\n`
          + "Die gesetzten Moebel wurden nicht angeruehrt -- sieh im Moebel-Schritt nach, "
          + "ob sie noch dort stehen, wo sie hingehoeren."
        : (ergebnis.error || "Speichern der Revision fehlgeschlagen."),
    }, { headers: { "Cache-Control": "no-store" } });
  }

  const scripts = join(suite, "born2thrill-local-workbench", "scripts");
  const python = process.env.PYTHON_EXECUTABLE || "python";
  const args =
    schritt === "bauen" ? [join(scripts, "go.py"), plan, ...(trotzTreppe ? ["--trotz-treppe"] : [])]
    // Nur pruefen, ob eine Wand die Treppe zusperrt (Rainer, 2026-10-17).
    // Baut den Plan in einen Temp-Ordner, kein Blender, gibt JSON aus.
    : schritt === "treppe" ? [join(scripts, "treppe_zugang.py"), plan]
    : schritt === "hochladen" ? [join(scripts, "go.py"), plan, "--hochladen"]
    // Erzeugt CODEX-AUFTRAG.md und codex-job.json neben die .blend: die
    // Dateiliste mit sha256, die Hero-Regeln und die geforderten Bildnamen.
    : schritt === "codex" ? [join(scripts, "make-codex-job.py"), plan]
    : [join(scripts, "approve-plan.py"), plan, "--reason", grund];

  const { code, ausgabe } = await lauf(python, args, scripts);

  // Freigeben hat zwei Haelften: approve-plan.py schreibt die Rechte ins
  // LOKALE Ledger, freigeben.py schaltet die Bilder im WordPress-Katalog
  // scharf. Bis heute lief nur die erste -- bungalow_039 stand mit 9
  // hochgeladenen Bildern auf im=0, weil die zweite niemand aufrief
  // (2026-08-20).
  if (schritt === "freigeben" && code === 0) {
    const wp = await lauf(python, [join(scripts, "freigeben.py"), plan], scripts);
    return Response.json({ ok: wp.code === 0, code: wp.code,
      ausgabe: `${ausgabe}\n${wp.ausgabe}` },
      { headers: { "Cache-Control": "no-store" } });
  }

  return Response.json({ ok: code === 0, code, ausgabe },
    { headers: { "Cache-Control": "no-store" } });
}
