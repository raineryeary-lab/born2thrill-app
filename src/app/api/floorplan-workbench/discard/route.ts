/**
 * Get a wrong render out of the way.
 *
 * Rainer, 2026-08-18: "a couple of them are just wrong and should be deleted".
 *
 * It MOVES the file into a `_verworfen/` folder beside it. It never unlinks.
 * This tree is not a git repo, so a delete here is unrecoverable and a
 * mis-click would cost a render. Moving is reversible by dragging the file
 * back, and the folder name says plainly what it holds.
 *
 * Same local-only gate as the other floorplan-workbench routes.
 */
import { mkdir, rename, stat } from "node:fs/promises";
import { basename, dirname, extname, join } from "node:path";
import { resolveAssetPath } from "@/lib/floorplan-workbench/inventory";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const DISCARD_DIR = "_verworfen";

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

/** A free name inside the discard folder, so a second discard never overwrites the first. */
async function freeName(folder: string, name: string) {
  const extension = extname(name);
  const stem = basename(name, extension);
  for (let attempt = 0; attempt < 100; attempt += 1) {
    const candidate = attempt === 0 ? name : `${stem}-${attempt}${extension}`;
    try {
      await stat(join(folder, candidate));
    } catch {
      return candidate;
    }
  }
  return `${stem}-${Date.now()}${extension}`;
}

export async function POST(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });

  let body: Record<string, unknown>;
  try {
    body = JSON.parse(await request.text());
  } catch {
    return Response.json({ error: "Invalid JSON." }, { status: 400 });
  }

  const absolute = resolveAssetPath(String(body.root || ""), String(body.path || ""));
  if (!absolute) return Response.json({ error: "Unknown asset." }, { status: 400 });

  // Refuse anything that is not a plain file we can see.
  try {
    const info = await stat(absolute);
    if (!info.isFile()) return Response.json({ error: "Not a file." }, { status: 400 });
  } catch {
    return Response.json({ error: "File is gone already." }, { status: 404 });
  }

  const folder = join(dirname(absolute), DISCARD_DIR);
  await mkdir(folder, { recursive: true });
  const name = await freeName(folder, basename(absolute));
  const target = join(folder, name);
  await rename(absolute, target);

  return Response.json({ ok: true, moved_to: target, note: "moved, not deleted" });
}
