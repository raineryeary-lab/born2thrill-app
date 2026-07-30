import { createHash, randomUUID } from "node:crypto";
import {
  mkdir,
  readFile,
  readdir,
  rename,
  writeFile,
} from "node:fs/promises";
import { basename, join, resolve } from "node:path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const MAX_REQUEST_BYTES = 2 * 1024 * 1024;
const MAX_REASON_LENGTH = 2_000;
const MAX_SUMMARIES = 100;

type JsonRecord = Record<string, unknown>;
type ReviewStatus = "approved_for_next_stage" | "rejected";

function isRecord(value: unknown): value is JsonRecord {
  return Boolean(value) && typeof value === "object" && !Array.isArray(value);
}

function normalizedHostname(value: string) {
  const firstHost = value.split(",")[0]?.trim().toLowerCase() ?? "";
  if (firstHost.startsWith("[")) {
    return firstHost.slice(1, firstHost.indexOf("]"));
  }
  return firstHost.split(":")[0];
}

function isLocalHostname(hostname: string) {
  return hostname === "127.0.0.1" || hostname === "localhost" || hostname === "::1";
}

function localWorkbenchEnabled(request: Request) {
  const urlHostname = new URL(request.url).hostname.toLowerCase();
  const forwardedHost = request.headers.get("x-forwarded-host");
  const headerHostname = normalizedHostname(
    forwardedHost || request.headers.get("host") || "",
  );
  return process.env.FLOORPLAN_WORKBENCH_ENABLED === "true"
    && isLocalHostname(urlHostname)
    && isLocalHostname(headerHostname);
}

function reviewDirectory() {
  const configured = process.env.FLOORPLAN_WORKBENCH_DATA_DIR?.trim();
  if (configured) return resolve(configured, "reviews");
  const localRoot = process.env.LOCALAPPDATA?.trim() || process.env.TEMP?.trim();
  if (!localRoot) {
    throw new Error("Kein lokales Datenverzeichnis für Freigaben konfiguriert.");
  }
  return join(localRoot, "Born2Thrill", "floorplan-workbench", "reviews");
}

function text(value: unknown) {
  return typeof value === "string" ? value.trim() : "";
}

function reviewSummary(review: JsonRecord) {
  const brief = isRecord(review.brief) ? review.brief : {};
  const variant = isRecord(review.variant) ? review.variant : {};
  const metrics = isRecord(variant.metrics) ? variant.metrics : {};
  return {
    id: text(review.id),
    created_at: text(review.created_at),
    review_status: text(review.review_status),
    project_name: text(brief.projectName),
    variant_id: text(variant.id),
    variant_name: text(variant.name),
    reference_layout_id: text(metrics.referenceLayoutId),
    snapshot_sha256: text(review.snapshot_sha256),
  };
}

async function queueState() {
  const directory = reviewDirectory();
  await mkdir(directory, { recursive: true });
  const entries = await readdir(directory, { withFileTypes: true });
  const files = entries
    .filter((entry) => entry.isFile() && entry.name.endsWith(".json"))
    .map((entry) => entry.name)
    .sort()
    .reverse();
  const latest = await Promise.all(
    files.slice(0, MAX_SUMMARIES).map(async (file) => {
      try {
        const parsed = JSON.parse(await readFile(join(directory, file), "utf8")) as unknown;
        return isRecord(parsed) ? reviewSummary(parsed) : null;
      } catch {
        return null;
      }
    }),
  );
  return {
    schema: "born2thrill-floorplan-review-queue-v1",
    count: files.length,
    storage: basename(resolve(directory, "..")),
    reviews: latest.filter(Boolean),
  };
}

function unavailable() {
  return Response.json(
    { error: "Der lokale Freigabe-Arbeitsplatz ist nicht aktiviert." },
    { status: 404 },
  );
}

export async function GET(request: Request) {
  if (!localWorkbenchEnabled(request)) return unavailable();
  try {
    return Response.json(await queueState(), {
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Freigabe-Queue nicht verfügbar.";
    return Response.json({ error: message }, { status: 500 });
  }
}

export async function POST(request: Request) {
  if (!localWorkbenchEnabled(request)) return unavailable();

  const body = await request.text();
  if (Buffer.byteLength(body, "utf8") > MAX_REQUEST_BYTES) {
    return Response.json({ error: "Die Freigabe ist zu groß." }, { status: 413 });
  }

  let source: unknown;
  try {
    source = JSON.parse(body);
  } catch {
    return Response.json({ error: "Ungültige JSON-Anfrage." }, { status: 400 });
  }
  if (!isRecord(source) || source.schema !== "born2thrill-floorplan-review-v1") {
    return Response.json({ error: "Ungültiges Freigabeformat." }, { status: 400 });
  }

  const reviewStatus = source.review_status;
  if (reviewStatus !== "approved_for_next_stage" && reviewStatus !== "rejected") {
    return Response.json({ error: "Ungültiger Freigabestatus." }, { status: 400 });
  }
  if (!isRecord(source.brief) || !isRecord(source.variant)) {
    return Response.json({ error: "Grundriss-Snapshot fehlt." }, { status: 400 });
  }
  if (!text(source.variant.id) || !text(source.variant.name)) {
    return Response.json({ error: "Variantenkennung fehlt." }, { status: 400 });
  }

  try {
    const id = randomUUID();
    const createdAt = new Date().toISOString();
    const snapshotJson = JSON.stringify({
      brief: source.brief,
      variant: source.variant,
    });
    const review = {
      schema: "born2thrill-floorplan-review-v1",
      id,
      created_at: createdAt,
      review_status: reviewStatus as ReviewStatus,
      training_eligible: false,
      publication_status: "not_published",
      reason: text(source.reason).slice(0, MAX_REASON_LENGTH),
      snapshot_sha256: createHash("sha256").update(snapshotJson).digest("hex"),
      brief: source.brief,
      variant: source.variant,
    };
    const directory = reviewDirectory();
    await mkdir(directory, { recursive: true });
    const timestamp = createdAt.replace(/\D/g, "").slice(0, 17);
    const filename = `${timestamp}-${id}.json`;
    const temporary = join(directory, `${filename}.tmp`);
    await writeFile(temporary, `${JSON.stringify(review, null, 2)}\n`, {
      encoding: "utf8",
      flag: "wx",
    });
    await rename(temporary, join(directory, filename));
    const state = await queueState();
    return Response.json({
      saved: true,
      count: state.count,
      review: reviewSummary(review),
    }, {
      status: 201,
      headers: { "Cache-Control": "no-store" },
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Freigabe konnte nicht gespeichert werden.";
    return Response.json({ error: message }, { status: 500 });
  }
}
