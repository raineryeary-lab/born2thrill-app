/**
 * POST {plan}: schlechten Grundriss nach projects/_verworfen verschieben
 * (haus-verwerfen-v1). Nie loeschen; veroeffentlichte Haeuser und laufende
 * Baue werden abgelehnt. Kein WordPress-Aufruf ausser dem lesenden Katalog.
 */
import { join, resolve } from "node:path";
import { hausVerwerfen, planNameOk } from "@/lib/floorplan-workbench/haus-verwerfen.mjs";
import { laeuftBau } from "@/lib/floorplan-workbench/pipeline-lauf.mjs";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const SITE = (process.env.B2T_SITE || "https://born2thrill.de").replace(/\/+$/, "");

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

/** true/false aus dem Katalog; null wenn er nicht erreichbar ist. */
async function imKatalog(plan: string): Promise<boolean | null> {
  try {
    const r = await fetch(`${SITE}/wp-json/b2t/v1/grundrisse`,
      { cache: "no-store", signal: AbortSignal.timeout(20_000) });
    if (!r.ok) return null;
    const rows = await r.json();
    if (!Array.isArray(rows)) return null;
    return rows.some((row: { id?: string }) => row?.id === plan);
  } catch {
    return null;
  }
}

export async function POST(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  let body: Record<string, unknown>;
  try {
    body = JSON.parse(await request.text());
  } catch {
    return Response.json({ error: "Invalid JSON." }, { status: 400 });
  }
  const plan = String(body.plan || "");
  if (!planNameOk(plan)) return Response.json({ ok: false, fehler: "Unzulässiger Planname." }, { status: 400 });

  const veroeffentlicht = await imKatalog(plan);
  if (veroeffentlicht === null) {
    return Response.json({ ok: false, fehler: "Katalog nicht erreichbar – zur Sicherheit nicht verworfen." }, { status: 503 });
  }
  const projects = join(resolve(process.cwd(), ".."), "floorplan-simplifier", "projects");
  const r = await hausVerwerfen({ projects, plan, veroeffentlicht, imBau: Boolean(laeuftBau(plan)) });
  return Response.json(r, { status: r.ok ? 200 : 409 });
}
