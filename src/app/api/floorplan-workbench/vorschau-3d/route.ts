/**
 * 3D-Vorschau des Hauses von aussen, vor dem Bau (vorschau-3d-v1).
 *
 * Rainer, 2026-11-03: "WOULD IT BE SUPER HARD TO DO A 3D PREVIEW OF SOME SORT
 * of the outside before we really go into the build?" -- Weg 2: der echte
 * Bau (Plan + render-exterior.py) ohne Render, als GLB. Die Rechnung steht in
 * scripts/vorschau-3d.py, nicht hier -- eine Fassung, auch auf der
 * Kommandozeile.
 *
 * GET  ?plan=<id>              -> vorschau.json (Daecher, gebaute Dateien) oder {}
 * GET  ?plan=<id>&dach=<form>  -> die GLB-Datei
 * POST { plan, dach }          -> neu bauen (ca. 6 s), Ergebnis als JSON
 *
 * Abgelegt unter <Datenordner>/vorschau-3d/<id>/ -- kein Lieferordner, keine
 * .blend, kein Bild.
 */
import { spawn } from "node:child_process";
import { readFile } from "node:fs/promises";
import { join, resolve } from "node:path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const PLAN_OK = /^[A-Za-z0-9_.-]+$/;
const DACH_OK = /^[a-z-]+$/;

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

function vorschauOrdner(plan: string) {
  const konfiguriert = process.env.FLOORPLAN_WORKBENCH_DATA_DIR?.trim();
  if (!konfiguriert) {
    throw new Error("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt -- "
      + "verweigere, den Datenordner zu erraten. Siehe .env.local.");
  }
  return join(resolve(konfiguriert), "vorschau-3d", plan);
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

export async function GET(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const params = new URL(request.url).searchParams;
  const plan = params.get("plan") || "";
  const dach = params.get("dach") || "";
  if (!PLAN_OK.test(plan)) return Response.json({ error: "Kein gültiger Plan." }, { status: 400 });
  const ordner = vorschauOrdner(plan);
  // fenster-3d-v1: der Plan der Vorschau (Waende, Oeffnungen in mm).
  if (params.get("datei") === "plan") {
    const text = await readFile(join(ordner, "plan.json"), "utf8").catch(() => "{}");
    return new Response(text, { headers: { "Content-Type": "application/json", "Cache-Control": "no-store" } });
  }
  if (dach) {
    if (!DACH_OK.test(dach)) return Response.json({ error: "Keine gültige Dachform." }, { status: 400 });
    const glb = await readFile(join(ordner, `${dach}.glb`)).catch(() => null);
    if (!glb) return Response.json({ error: "Noch nicht gebaut." }, { status: 404 });
    return new Response(new Uint8Array(glb), {
      headers: { "Content-Type": "model/gltf-binary", "Cache-Control": "no-store" },
    });
  }
  const info = await readFile(join(ordner, "vorschau.json"), "utf8")
    .then((text) => JSON.parse(text)).catch(() => ({}));
  return Response.json(info, { headers: { "Cache-Control": "no-store" } });
}

export async function POST(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const body = await request.json().catch(() => ({}));
  const plan = String(body.plan || "");
  const dach = String(body.dach || "");
  if (!PLAN_OK.test(plan)) return Response.json({ error: "Kein gültiger Plan." }, { status: 400 });
  if (dach && !DACH_OK.test(dach)) return Response.json({ error: "Keine gültige Dachform." }, { status: 400 });

  const scripts = join(resolve(process.cwd()), "scripts");
  const python = process.env.PYTHON_EXECUTABLE || "python";
  const args = [join(scripts, "vorschau-3d.py"), plan, vorschauOrdner(plan)];
  if (dach) args.push("--dach", dach);
  const { code, ausgabe } = await lauf(python, args, scripts);
  const letzte = ausgabe.trim().split(/\r?\n/).pop() || "";
  let ergebnis: any = null;
  try { ergebnis = JSON.parse(letzte); } catch { /* unten als Fehler */ }
  if (code !== 0 || !ergebnis?.ok) {
    return Response.json({ error: "3D-Vorschau fehlgeschlagen.", ergebnis, ausgabe: ausgabe.slice(-3000) },
                         { status: 500 });
  }
  return Response.json(ergebnis, { headers: { "Cache-Control": "no-store" } });
}
