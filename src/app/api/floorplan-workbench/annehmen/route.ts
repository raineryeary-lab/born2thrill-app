/**
 * Eine Codex-Lieferung pruefen und annehmen -- eine Wahrheit je Haus.
 *
 * Rainer, 2026-08-27: "wieso werden so viele unterschiedliche ordner
 * verwendet?" Drei Stellen im Code erfanden drei Ordnernamen, und keine
 * kannte die andere; `bungalow_039` hat acht `codex-final-*`-Ordner, und der
 * Bilder-Tab nahm den alphabetisch letzten statt des juengsten. Ab hier steht
 * in `renders/ANGENOMMEN.json` genau ein Ordner, und dorthin kommt nur, was
 * `scripts/lieferung-pruefen.py` bestanden hat.
 *
 * GET  ?plan=<id>          -> die Lieferordner mit ihrem Befund
 * POST { plan, ordner }    -> pruefen und, wenn sauber, annehmen
 *
 * Die Pruefung selbst steht in Python, nicht hier: dasselbe Programm laeuft
 * auch auf der Kommandozeile, und es gibt nur eine Fassung davon.
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
  const headerHost = normalizedHostname(
    request.headers.get("x-forwarded-host") || request.headers.get("host") || "",
  );
  return process.env.FLOORPLAN_WORKBENCH_ENABLED === "true"
    && ["127.0.0.1", "localhost", "::1"].includes(urlHost)
    && ["127.0.0.1", "localhost", "::1"].includes(headerHost);
}

function datenOrdner() {
  // Nicht raten. 2026-08-21: der Datenordner zog von C: nach E:.
  const konfiguriert = process.env.FLOORPLAN_WORKBENCH_DATA_DIR?.trim();
  if (!konfiguriert) {
    throw new Error("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt -- "
      + "verweigere, den Datenordner zu erraten. Siehe .env.local.");
  }
  return resolve(konfiguriert);
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

/** Die Beanstandungen aus der Ausgabe des Pruefers, eine je Zeile mit "- ". */
function beanstandungen(ausgabe: string) {
  return ausgabe.split(/\r?\n/)
    .filter((zeile) => zeile.trimStart().startsWith("- "))
    .map((zeile) => zeile.trim().slice(2));
}

async function pruefer(plan: string, ordner: string, annehmen: boolean) {
  const scripts = join(resolve(process.cwd()), "scripts");
  const python = process.env.PYTHON_EXECUTABLE || "python";
  const args = [join(scripts, "lieferung-pruefen.py"), plan, ordner];
  if (annehmen) args.push("--annehmen");
  const { code, ausgabe } = await lauf(python, args, scripts);
  return { ok: code === 0, ausgabe, maengel: beanstandungen(ausgabe) };
}

export async function GET(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const plan = new URL(request.url).searchParams.get("plan") || "";
  if (!PLAN_OK.test(plan)) return Response.json({ error: "Kein gültiger Plan." }, { status: 400 });

  const renders = join(datenOrdner(), "corrections", plan, "renders");
  const eintraege = await readdir(renders, { withFileTypes: true }).catch(() => []);
  // go-baseline ist der Rohbau, kein Lieferordner.
  const ordner = eintraege
    .filter((e) => e.isDirectory() && e.name !== "go-baseline")
    .map((e) => e.name)
    .sort();

  const angenommen = await readFile(join(renders, "ANGENOMMEN.json"), "utf8")
    .then((text) => JSON.parse(text)).catch(() => null);

  const befunde = [];
  for (const name of ordner) {
    const { ok, maengel } = await pruefer(plan, name, false);
    befunde.push({ ordner: name, ok, maengel, ist_angenommen: angenommen?.ordner === name });
  }
  return Response.json({ plan, angenommen, lieferungen: befunde },
                       { headers: { "Cache-Control": "no-store" } });
}

export async function POST(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const body = await request.json().catch(() => ({}));
  const plan = String(body.plan || "");
  const ordner = String(body.ordner || "");
  if (!PLAN_OK.test(plan)) return Response.json({ error: "Kein gültiger Plan." }, { status: 400 });
  // Nur ein blosser Ordnername, keine Pfadbestandteile -- sonst waere das ein
  // Weg, einen beliebigen Ordner als Lieferung auszugeben.
  if (!PLAN_OK.test(ordner) || ordner === "go-baseline") {
    return Response.json({ error: "Kein gültiger Lieferordner." }, { status: 400 });
  }

  const { ok, maengel, ausgabe } = await pruefer(plan, ordner, true);
  if (!ok) {
    return Response.json({ error: "Lieferung nicht angenommen.", maengel, ausgabe },
                         { status: 409 });
  }
  return Response.json({ ok: true, plan, ordner, ausgabe },
                       { headers: { "Cache-Control": "no-store" } });
}
