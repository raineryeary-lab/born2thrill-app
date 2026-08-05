import { randomUUID } from "node:crypto";
import { mkdir, rename, writeFile } from "node:fs/promises";
import { join, resolve } from "node:path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const MAX_REQUEST_BYTES = 8 * 1024;
const DECISIONS = new Set(["better", "worse", "reject"]);

function normalizedHostname(value: string) {
  const first = value.split(",")[0]?.trim().toLowerCase() || "";
  if (first.startsWith("[")) return first.slice(1, first.indexOf("]"));
  return first.split(":")[0];
}

function enabled(request: Request) {
  const urlHost = new URL(request.url).hostname.toLowerCase();
  const headerHost = normalizedHostname(request.headers.get("x-forwarded-host") || request.headers.get("host") || "");
  return process.env.FLOORPLAN_WORKBENCH_ENABLED === "true"
    && ["127.0.0.1", "localhost", "::1"].includes(urlHost)
    && ["127.0.0.1", "localhost", "::1"].includes(headerHost);
}

function dataRoot() {
  const configured = process.env.FLOORPLAN_WORKBENCH_DATA_DIR?.trim();
  return configured
    ? resolve(configured)
    : join(process.env.LOCALAPPDATA || process.env.TEMP || ".", "Born2Thrill", "floorplan-workbench");
}

function safeReference(value: unknown) {
  const reference = String(value || "").replace(/[^a-zA-Z0-9._-]/g, "");
  if (!reference) throw new Error("source_reference_id fehlt.");
  return reference;
}

export async function POST(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const text = await request.text();
  if (Buffer.byteLength(text) > MAX_REQUEST_BYTES) {
    return Response.json({ error: "Review request too large." }, { status: 413 });
  }
  let body: Record<string, unknown>;
  try {
    body = JSON.parse(text);
  } catch {
    return Response.json({ error: "Invalid JSON." }, { status: 400 });
  }
  const decision = String(body.decision || "");
  if (!DECISIONS.has(decision)) {
    return Response.json({ error: "Decision must be better, worse or reject." }, { status: 400 });
  }
  let reference: string;
  try {
    reference = safeReference(body.source_reference_id);
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : String(error) }, { status: 400 });
  }
  const comparedTo = body.compared_to ? safeReference(body.compared_to) : null;
  const record = {
    schema: "dmh-floorplan-reference-review-v1",
    review_id: randomUUID(),
    created_at: new Date().toISOString(),
    source_reference_id: reference,
    compared_to: comparedTo,
    decision,
    note: String(body.note || "").trim().slice(0, 500),
    geometry_hash: /^[a-f0-9]{64}$/i.test(String(body.geometry_hash || ""))
      ? String(body.geometry_hash)
      : null,
  };
  const directory = join(dataRoot(), "reference-reviews");
  await mkdir(directory, { recursive: true });
  const target = join(directory, `${record.created_at.replace(/[:.]/g, "-")}-${record.review_id}.json`);
  const temporary = `${target}.${randomUUID()}.tmp`;
  await writeFile(temporary, `${JSON.stringify(record, null, 2)}\n`, { flag: "wx" });
  await rename(temporary, target);
  return Response.json({ ok: true, record, path: target }, { status: 201 });
}
