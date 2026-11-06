/**
 * Dachform pro Stil lesen und setzen -- die UI-Huelle um scripts/dachform.py.
 *
 * Die Maschinerie existiert seit dem 20.08. (roof_type_modern /
 * roof_type_classic in gebaeudemass.json, gelesen vom Plan-Builder pro Stil),
 * war aber nur per Kommandozeile erreichbar. Rainer, 2026-08-22: "i need the
 * 2 roof form option to build out 2 houses that is a must". Schreiben laeuft
 * ueber dachform.py selbst (eine Quelle der Wahrheit, gleiche Validierung),
 * nie durch direktes JSON-Schreiben hier.
 *
 * GET  ?plan=<id>            -> { modern, classic, formen }
 * POST { plan, modern, classic }
 */
import { spawn } from "node:child_process";
import { readFile } from "node:fs/promises";
import { join, resolve } from "node:path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const FORMEN = ["flachdach", "walmdach", "satteldach"] as const;

function normalizedHostname(value: string) {
  const first = value.split(",")[0]?.trim().toLowerCase() || "";
  if (first.startsWith("[")) return first.slice(1, first.indexOf("]"));
  return first.split(":")[0];
}

function enabled(request: Request) {
  const urlHost = new URL(request.url).hostname.toLowerCase();
  const headerHost = normalizedHostname(request.headers.get("host") || "");
  const allowed = new Set(["localhost", "127.0.0.1", "::1"]);
  return allowed.has(urlHost) && (!headerHost || allowed.has(headerHost));
}

function gebaeudemassPath(suite: string, plan: string) {
  return join(suite, "floorplan-simplifier", "projects", plan, "gebaeudemass.json");
}

const PLAN_OK = /^[A-Za-z0-9_.-]+$/;

export async function GET(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const plan = new URL(request.url).searchParams.get("plan") || "";
  if (!PLAN_OK.test(plan)) return Response.json({ error: "plan fehlt/ungueltig" }, { status: 400 });
  const suite = resolve(process.cwd(), "..");
  let modern: string | null = null;
  let classic: string | null = null;
  try {
    const mass = JSON.parse(await readFile(gebaeudemassPath(suite, plan), "utf8"));
    modern = mass.roof_type_modern || null;
    classic = mass.roof_type_classic || null;
  } catch { /* noch keine gebaeudemass.json -- beide null */ }
  return Response.json({ plan, modern, classic, formen: FORMEN },
                       { headers: { "Cache-Control": "no-store" } });
}

export async function POST(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const body = await request.json().catch(() => ({}));
  const plan = String(body.plan || "");
  const modern = String(body.modern || "");
  const classic = String(body.classic || "");
  if (!PLAN_OK.test(plan)) return Response.json({ error: "plan fehlt/ungueltig" }, { status: 400 });
  if (!FORMEN.includes(modern as any) || !FORMEN.includes(classic as any)) {
    return Response.json(
      { error: `Dachform muss eine von ${FORMEN.join(", ")} sein.` }, { status: 400 });
  }
  const suite = resolve(process.cwd(), "..");
  const scripts = join(suite, "born2thrill-local-workbench", "scripts");
  const python = process.env.PYTHON_EXECUTABLE || "python";
  const ergebnis: { code: number; ausgabe: string } = await new Promise((fertig) => {
    let ausgabe = "";
    const kind = spawn(python,
                       [join(scripts, "dachform.py"), plan,
                        "--modern", modern, "--classic", classic],
                       { cwd: scripts });
    const sammeln = (chunk: Buffer) => { if (ausgabe.length < 8000) ausgabe += String(chunk); };
    kind.stdout.on("data", sammeln);
    kind.stderr.on("data", sammeln);
    kind.on("close", (code) => fertig({ code: code ?? -1, ausgabe }));
    kind.on("error", (e) => fertig({ code: -1, ausgabe: String(e) }));
  });
  if (ergebnis.code !== 0) {
    return Response.json({ ok: false, error: ergebnis.ausgabe.trim().slice(-400) || "dachform.py fehlgeschlagen" },
                         { status: 500 });
  }
  return Response.json({ ok: true, plan, modern, classic });
}
