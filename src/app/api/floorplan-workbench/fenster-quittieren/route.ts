/**
 * fenster-quittieren-v1 (Rainer, 2026-11-12: "sowas muss ich auch bestaetigen
 * und ausblenden koennen"): einen Fensterpruefer-Hinweis als gesehen merken.
 * <Datenordner>/fenster-quittiert.json = { plan: [Hinweistext, ...] }.
 * Der Wortlaut enthaelt die Masse -- aendert sich das Fenster, erscheint er neu.
 *
 * POST { plan, teil }
 */
import { readFile, rename, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";

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
  const teil = String(b.teil || "").trim();
  if (!NAME.test(plan) || !teil || teil.length > 500) {
    return Response.json({ ok: false, ausgabe: "Plan oder Hinweis fehlt." }, { status: 400 });
  }
  // zfh-quittieren-v1: ZFH-Verdacht bestaetigen -> floorplan-simplifier/zfh-quittiert.json
  // {plan: Grund}, neben zfh-verdacht.json; der Annotator liest dieselbe Datei.
  if (b.art === "zfh") {
    const pfadZ = join(resolve(process.cwd()), "..", "floorplan-simplifier", "zfh-quittiert.json");
    const alleZ = await readFile(pfadZ, "utf8").then((t) => JSON.parse(t) as Record<string, string>)
      .catch(() => ({} as Record<string, string>));
    alleZ[plan] = teil;
    await writeFile(pfadZ + ".tmp", JSON.stringify(alleZ, null, 1) + "\n", "utf8");
    await rename(pfadZ + ".tmp", pfadZ);
    return Response.json({ ok: true, plan }, { headers: { "Cache-Control": "no-store" } });
  }
  const daten = process.env.FLOORPLAN_WORKBENCH_DATA_DIR?.trim();
  if (!daten) return Response.json({ ok: false, ausgabe: "FLOORPLAN_WORKBENCH_DATA_DIR fehlt." }, { status: 500 });
  const pfad = join(resolve(daten), "fenster-quittiert.json");
  const alle = await readFile(pfad, "utf8").then((t) => JSON.parse(t) as Record<string, string[]>)
    .catch(() => ({} as Record<string, string[]>));
  const liste = new Set(alle[plan] || []);
  liste.add(teil);
  alle[plan] = [...liste];
  await writeFile(pfad + ".tmp", JSON.stringify(alle, null, 1) + "\n", "utf8");
  await rename(pfad + ".tmp", pfad);
  return Response.json({ ok: true, plan, anzahl: alle[plan].length }, { headers: { "Cache-Control": "no-store" } });
}
