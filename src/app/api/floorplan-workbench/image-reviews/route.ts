/**
 * Accept / request-changes on a single rendered image.
 *
 * Rainer, 2026-08-18: "where do i accept the image and where do i ask for
 * changes?" -- nowhere, until this. Geometry had an approval gate (correction
 * revisions) but the IMAGES Codex returns had none: `qc_status` in
 * catalog.json is written by Codex, not by the person reviewing.
 *
 * The verdict is stored as `review.json` NEXT TO the image, in the same
 * delivery folder as catalog.json, so a delivery carries its own review and
 * Codex can read which assets to re-render without another index to keep in
 * sync.
 *
 * Same local-only gate, same atomic temp+rename write as the other
 * floorplan-workbench routes.
 */
import { randomUUID } from "node:crypto";
import { readFile, rename, writeFile } from "node:fs/promises";
import { dirname, join, basename } from "node:path";
import { resolveAssetPath } from "@/lib/floorplan-workbench/inventory";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const MAX_REQUEST_BYTES = 8 * 1024;
const VERDICTS = new Set(["accepted", "changes_requested"]);
const SCHEMA = "dmh-image-review-v1";

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

type ReviewEntry = {
  image: string;
  verdict: string;
  note: string;
  decided_at: string;
};

async function readReviewFile(reviewPath: string) {
  try {
    const parsed = JSON.parse(await readFile(reviewPath, "utf8"));
    const reviews = Array.isArray(parsed?.reviews) ? (parsed.reviews as ReviewEntry[]) : [];
    return { schema: SCHEMA, reviews };
  } catch {
    return { schema: SCHEMA, reviews: [] as ReviewEntry[] };
  }
}

/** GET ?root=<key>&path=<relative dir or image> -> the folder's reviews. */
export async function GET(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const url = new URL(request.url);
  const absolute = resolveAssetPath(url.searchParams.get("root") || "", url.searchParams.get("path") || "");
  if (!absolute) return Response.json({ error: "Unknown asset." }, { status: 400 });
  const file = await readReviewFile(join(dirname(absolute), "review.json"));
  return Response.json(file, { headers: { "Cache-Control": "no-store" } });
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

  const verdict = String(body.verdict || "");
  if (!VERDICTS.has(verdict)) {
    return Response.json({ error: "verdict must be accepted or changes_requested." }, { status: 400 });
  }
  const absolute = resolveAssetPath(String(body.root || ""), String(body.path || ""));
  if (!absolute) return Response.json({ error: "Unknown asset." }, { status: 400 });

  const reviewPath = join(dirname(absolute), "review.json");
  const current = await readReviewFile(reviewPath);
  const image = basename(absolute);
  const entry: ReviewEntry = {
    image,
    verdict,
    note: String(body.note || "").trim().slice(0, 500),
    decided_at: new Date().toISOString(),
  };
  // One verdict per image: the latest replaces the previous.
  const reviews = current.reviews.filter((r) => r.image !== image).concat(entry);
  const payload = { schema: SCHEMA, updated_at: entry.decided_at, reviews };

  const temporary = `${reviewPath}.${randomUUID()}.tmp`;
  await writeFile(temporary, `${JSON.stringify(payload, null, 2)}\n`, { flag: "wx" });
  await rename(temporary, reviewPath);
  return Response.json({ ok: true, entry, path: reviewPath }, { status: 201 });
}
