/**
 * kopie-anlegen-v1 (Rainer, 2026-11-10): Haus als Vorlage duplizieren und auf
 * eine Wohnflaeche skalieren -- Vorschau, dann Kopie samt Moebel.
 * Die Vorlage wird nie veraendert (scripts/kopie-anlegen.py).
 */
import { readFile } from "node:fs/promises";
import { join, resolve } from "node:path";
import { lauf } from "@/lib/floorplan-workbench/pipeline-lauf.mjs";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

function lokal(request: Request) {
  const host = new URL(request.url).hostname.toLowerCase();
  return process.env.FLOORPLAN_WORKBENCH_ENABLED === "true"
    && ["127.0.0.1", "localhost", "::1"].includes(host);
}

const NAME = /^[A-Za-z0-9_.-]+$/;

export async function POST(request: Request) {
  if (!lokal(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const body = await request.json().catch(() => ({}));
  const quelle = String(body.quelle || "");
  const flaeche = Number(body.flaeche);
  const neu = String(body.neu || "").trim();
  if (!NAME.test(quelle)) return Response.json({ ok: false, ausgabe: "Keine Vorlage." }, { status: 400 });
  if (!(flaeche > 20 && flaeche < 1000)) {
    return Response.json({ ok: false, ausgabe: "Wohnfläche in m² angeben." }, { status: 400 });
  }
  if (neu && !NAME.test(neu)) {
    return Response.json({ ok: false, ausgabe: "Name nur aus Buchstaben, Ziffern, _ . -" }, { status: 400 });
  }
  const scripts = join(resolve(process.cwd(), ".."), "born2thrill-local-workbench", "scripts");
  const python = process.env.PYTHON_EXECUTABLE || "python";
  const args = [join(scripts, "kopie-anlegen.py"), quelle, "--flaeche", String(flaeche),
    ...(neu ? ["--anlegen", neu] : [])];
  const { code, ausgabe } = await lauf(python, args, scripts, 10 * 60_000);
  const zeile = String(ausgabe || "").trim().split(/\r?\n/).reverse().find((z: string) => z.startsWith("{"));
  if (code !== 0 || !zeile) {
    return Response.json({ ok: false, ausgabe: String(ausgabe || "").trim() || `Fehler (Code ${code})` },
      { headers: { "Cache-Control": "no-store" } });
  }
  const ergebnis = JSON.parse(zeile);
  let bild = "";
  if (ergebnis.vorschau) {
    bild = await readFile(ergebnis.vorschau).then((b) => "data:image/png;base64," + b.toString("base64"))
      .catch(() => "");
  }
  return Response.json({ ok: true, ...ergebnis, bild }, { headers: { "Cache-Control": "no-store" } });
}
