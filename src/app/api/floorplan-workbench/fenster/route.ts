/**
 * fenster-3d-v1 (Rainer, 2026-11-12): ein Fenster aus der 3D-Vorschau
 * verschieben oder aendern. Die Rechnung steht in scripts/fenster-bearbeiten.py
 * (schreibt annotations.json + source-state.json, Sicherung je Tag).
 *
 * POST { plan, id, verschieben?: [dx, dy] (mm), breite?: mm,
 *        typ?: "bodentief"|"bruestungsfenster", felder?: number|"auto" }
 */
import { join, resolve } from "node:path";
import { lauf } from "@/lib/floorplan-workbench/pipeline-lauf.mjs";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const NAME = /^[A-Za-z0-9_.-]+$/;

function lokal(request: Request) {
  const host = new URL(request.url).hostname.toLowerCase();
  return process.env.FLOORPLAN_WORKBENCH_ENABLED === "true"
    && ["127.0.0.1", "localhost", "::1"].includes(host);
}

export async function POST(request: Request) {
  if (!lokal(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const b = await request.json().catch(() => ({}));
  const plan = String(b.plan || "");
  const id = String(b.id || "");
  if (!NAME.test(plan) || !NAME.test(id)) {
    return Response.json({ ok: false, ausgabe: "Plan oder Fenster fehlt." }, { status: 400 });
  }
  const args: string[] = [];
  if (Array.isArray(b.verschieben) && b.verschieben.length === 2
      && b.verschieben.every((v: unknown) => Number.isFinite(Number(v)))) {
    args.push("--verschieben", `${Number(b.verschieben[0])},${Number(b.verschieben[1])}`);
  }
  if (Number(b.breite) > 200 && Number(b.breite) < 8000) args.push("--breite", String(Number(b.breite)));
  if (b.typ === "bodentief" || b.typ === "bruestungsfenster") args.push("--typ", b.typ);
  if (b.felder === "auto" || (Number(b.felder) >= 1 && Number(b.felder) <= 6)) {
    args.push("--felder", String(b.felder));
  }
  if (!args.length) return Response.json({ ok: false, ausgabe: "Nichts zu ändern." }, { status: 400 });
  const scripts = join(resolve(process.cwd()), "scripts");
  const python = process.env.PYTHON_EXECUTABLE || "python";
  const { code, ausgabe } = await lauf(python, [join(scripts, "fenster-bearbeiten.py"), plan, id, ...args],
    scripts, 60_000);
  const zeile = String(ausgabe || "").trim().split(/\r?\n/).pop() || "";
  let ergebnis: any = null;
  try { ergebnis = JSON.parse(zeile); } catch { /* unten */ }
  if (code !== 0 || !ergebnis?.ok) {
    return Response.json({ ok: false, ausgabe: String(ausgabe || "").slice(-1500) },
      { headers: { "Cache-Control": "no-store" } });
  }
  return Response.json(ergebnis, { headers: { "Cache-Control": "no-store" } });
}
