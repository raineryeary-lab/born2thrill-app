/**
 * POST {plan, liste}: Rainer hat die kleinen Zimmer dieses Hauses geprueft
 * (kleine-zimmer-v1). Schreibt nur projects/<plan>/zimmer-geprueft.json; die
 * Zeichnung und data.json bleiben unberuehrt, kein Bau veraltet. Aendert sich
 * die Liste spaeter (neue Flaeche, neues Zimmer), wird das Haus wieder gruen.
 */
import { writeFile } from "node:fs/promises";
import { existsSync } from "node:fs";
import { join, resolve } from "node:path";
import { planNameOk } from "@/lib/floorplan-workbench/haus-verwerfen.mjs";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

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

export async function POST(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  let body: Record<string, unknown>;
  try {
    body = JSON.parse(await request.text());
  } catch {
    return Response.json({ error: "Ungültige Anfrage." }, { status: 400 });
  }
  const plan = String(body.plan || "");
  const liste = String(body.liste || "").slice(0, 500);
  if (!planNameOk(plan)) return Response.json({ error: "Ungültiger Plan." }, { status: 400 });
  // Wie haus-verwerfen/route.ts.
  const projects = join(resolve(process.cwd(), ".."), "floorplan-simplifier", "projects");
  const ordner = join(projects, plan);
  if (!existsSync(join(ordner, "annotations.json"))) {
    return Response.json({ error: "Haus nicht gefunden." }, { status: 404 });
  }
  await writeFile(join(ordner, "zimmer-geprueft.json"),
    JSON.stringify({ liste, geprueft_at: new Date().toISOString() }, null, 1) + "\n", "utf8");
  return Response.json({ ok: true, plan, liste });
}
