/**
 * Rechteerklaerung lesen und abgeben -- die UI-Huelle um scripts/rechte.py.
 *
 * Die Rechtefrage ist keine Qualitaetspruefung: kein Mass an Arbeit macht
 * `commercial_use_allowed` wahr. Sie ist eine Entscheidung, und eine
 * Entscheidung darf einmal gestellt und dann gemerkt werden -- statt bei jedem
 * der 55 gesperrten Haeuser neu (Rainer, 2026-08-25: "wieso wird mir das
 * sichern so erschwert?").
 *
 * GET  ?plan=<id>  -> was fuer diesen Plan gilt, und wie viele Haeuser am
 *                     selben Datensatz haengen
 * POST {plan, antwort, grund, geltung, wer} -> Antwort festhalten
 *
 * Gerechnet wird in rechte.py -- eine Quelle der Wahrheit, dieselbe Pruefung
 * wie in approve-plan.py und publish-renders.py.
 */
import { spawn } from "node:child_process";
import { readdir, readFile } from "node:fs/promises";
import { join, resolve } from "node:path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

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

function suite() {
  return resolve(process.cwd(), "..");
}

function projects() {
  return join(suite(), "floorplan-simplifier", "projects");
}

async function readJson(path: string) {
  try {
    return JSON.parse((await readFile(path, "utf8")).replace(/^﻿/, ""));
  } catch {
    return null;
  }
}

/** Was der Herkunftsnachweis sagt -- unveraendert, nur gelesen. */
async function herkunft(plan: string) {
  const doc = await readJson(join(projects(), plan, "german-catalog-source.json"));
  const rechte = doc?.usage_rights || {};
  return {
    datensatz: doc?.dataset || null,
    quelldatei: doc?.source_file || null,
    lizenz: rechte.license || null,
    gesperrt: rechte.commercial_use_allowed === false,
  };
}

/** Wie viele Haeuser haengen am selben Datensatz -- fuer "gilt fuer alle N". */
async function haeuserImDatensatz(datensatz: string | null) {
  if (!datensatz) return 0;
  let namen: string[] = [];
  try {
    namen = await readdir(projects());
  } catch {
    return 0;
  }
  let zahl = 0;
  for (const name of namen) {
    const doc = await readJson(join(projects(), name, "german-catalog-source.json"));
    if (doc?.dataset === datensatz
        && (doc?.usage_rights || {}).commercial_use_allowed === false) zahl += 1;
  }
  return zahl;
}

function python() {
  return process.env.FLOORPLAN_PYTHON?.trim() || process.env.PYTHON_EXECUTABLE || "python";
}

/** rechte.py laufen lassen und stdout einsammeln. */
function lauf(args: string[]) {
  return new Promise<{ code: number; ausgabe: string }>((fertig) => {
    const kind = spawn(python(), args, { cwd: join(process.cwd(), "scripts") });
    let ausgabe = "";
    kind.stdout.on("data", (teil) => { ausgabe += teil; });
    kind.stderr.on("data", (teil) => { ausgabe += teil; });
    kind.on("error", (fehler) => fertig({ code: 1, ausgabe: String(fehler) }));
    kind.on("close", (code) => fertig({ code: code ?? 1, ausgabe }));
  });
}

/** Die geltende Erklaerung -- gelesen aus derselben Datei wie die Skripte. */
async function erklaerungFuer(plan: string, datensatz: string | null) {
  const wurzel = process.env.FLOORPLAN_WORKBENCH_DATA_DIR?.trim();
  if (!wurzel) return null;
  const doc = await readJson(join(resolve(wurzel), "rechte-erklaerungen.json"));
  const alle: Record<string, unknown>[] = doc?.erklaerungen || [];
  const juengste = (liste: Record<string, unknown>[]) =>
    liste.length ? liste.sort((a, b) => String(a.wann).localeCompare(String(b.wann))).at(-1) : null;
  // Dieselbe Vorrangregel wie rechte.erklaerung_fuer: das einzelne Haus ist die
  // genauere Aussage und schlaegt den Datensatz, in beide Richtungen.
  const eigen = juengste(alle.filter((e) => e.geltung === "plan" && e.wert === plan));
  if (eigen) return eigen;
  if (!datensatz) return null;
  return juengste(alle.filter((e) => e.geltung === "datensatz" && e.wert === datensatz));
}

/** Wann freigegeben wurde -- das steht nur im lokalen Ledger (approve-plan.py). */
async function freigegebenAm(plan: string) {
  const ledger = await readJson(join(process.cwd(), "data", "simplifier-v2", "corpus-ledger.json"));
  const eintrag = (ledger?.projects || []).find((e: any) => e.project_id === plan);
  return eintrag?.approval_recorded_at || null;
}

export async function GET(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const plan = new URL(request.url).searchParams.get("plan") || "";
  if (!PLAN_OK.test(plan)) return Response.json({ error: "plan fehlt/ungueltig" }, { status: 400 });
  const quelle = await herkunft(plan);
  const erklaerung = await erklaerungFuer(plan, quelle.datensatz);
  return Response.json({
    plan,
    ...quelle,
    geschwister: await haeuserImDatensatz(quelle.datensatz),
    erklaerung,
    // Gefragt wird nur, wo der Nachweis widerspricht und noch niemand
    // geantwortet hat. Ein Nein ist eine Antwort, keine offene Frage.
    frage_noetig: quelle.gesperrt && !erklaerung,
    freigegeben_am: await freigegebenAm(plan),
  }, { headers: { "Cache-Control": "no-store" } });
}

export async function POST(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const body = await request.json().catch(() => ({}));
  const plan = String(body.plan || "");
  const antwort = String(body.antwort || "");
  const grund = String(body.grund || "").trim();
  const geltung = String(body.geltung || "plan");
  const wer = String(body.wer || "").trim();

  if (!PLAN_OK.test(plan)) return Response.json({ error: "plan fehlt/ungueltig" }, { status: 400 });
  if (antwort !== "ja" && antwort !== "nein") {
    return Response.json({ error: "antwort muss ja oder nein sein" }, { status: 400 });
  }
  if (!grund) {
    return Response.json({ error: "Ohne Begruendung keine Erklaerung." }, { status: 400 });
  }

  const quelle = await herkunft(plan);
  if (geltung === "datensatz" && !quelle.datensatz) {
    return Response.json({ error: `${plan} gehoert zu keinem Datensatz.` }, { status: 400 });
  }

  const args = [join(process.cwd(), "scripts", "rechte.py")];
  if (geltung === "datensatz") args.push("--datensatz", quelle.datensatz as string);
  else args.push("--plan", plan);
  args.push(antwort === "ja" ? "--ja" : "--nein", "--grund", grund);
  if (wer) args.push("--wer", wer);

  const ergebnis = await lauf(args);
  if (ergebnis.code !== 0) {
    return Response.json({ error: ergebnis.ausgabe.trim().slice(-400) || "rechte.py fehlgeschlagen" },
                         { status: 500 });
  }
  const erklaerung = await erklaerungFuer(plan, quelle.datensatz);
  return Response.json({ ok: true, ausgabe: ergebnis.ausgabe.trim(), erklaerung },
                       { headers: { "Cache-Control": "no-store" } });
}
