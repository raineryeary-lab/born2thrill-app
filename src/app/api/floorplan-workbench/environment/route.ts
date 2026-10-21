/**
 * What each annotated house still needs, and what it CAN still be given.
 *
 * Rainer, 2026-08-18: "so many projects have neither image to trace nor walls
 * or anything in them". Measured over 234 annotation folders:
 *
 *   100  workable      raster present, drawing present
 *   118  no_source     rooms drawn, but the raster is gone from the folder
 *    14  empty         nothing at all
 *     1  blank         raster, nothing drawn
 *     1  unreadable    annotations.json will not parse
 *
 * The 118 matter because they look like pending work and are not: scale
 * calibration measures against the drawing, so with no raster the environment
 * step cannot be done at all. They also cannot be matched back to a template --
 * every project records a GENERIC source name ("original.pdf" appears 54
 * times) and not one carries a hash, upload name or template id. The link is
 * not lost, it was never written down.
 *
 * Deliberately no verdict on WHY the rasters are absent: the rulebook keeps
 * original plans out of publishable material, so their absence may be policy
 * rather than damage. This reports the state and lets a human decide.
 *
 * Read-only. Same local-only gate as the other floorplan-workbench routes.
 */
import { readFile, readdir, stat } from "node:fs/promises";
import { join, resolve } from "node:path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const RASTER = [".png", ".jpg", ".jpeg", ".pdf"];

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

/** Any raster anywhere under the project folder, not just at the top level. */
async function hasRaster(folder: string): Promise<boolean> {
  let entries: string[];
  try {
    entries = await readdir(folder);
  } catch {
    return false;
  }
  for (const entry of entries) {
    const full = join(folder, entry);
    if (RASTER.some((extension) => entry.toLowerCase().endsWith(extension))) return true;
    try {
      if ((await stat(full)).isDirectory() && await hasRaster(full)) return true;
    } catch {
      // unreadable child, keep looking
    }
  }
  return false;
}

export async function GET(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });

  const root = resolve(process.cwd(), "..", "floorplan-simplifier", "projects");
  let names: string[] = [];
  try {
    names = await readdir(root);
  } catch (error) {
    return Response.json(
      { error: `Cannot read ${root}: ${error instanceof Error ? error.message : String(error)}` },
      { status: 500 },
    );
  }

  const ready: string[] = [];      // scale AND surroundings done
  const todo: string[] = [];       // workable, still needs one of them
  const noSource: string[] = [];   // drawn, but no raster to calibrate against
  const empty: string[] = [];      // nothing in it
  const blank: string[] = [];      // raster, nothing drawn
  const unreadable: string[] = [];

  for (const name of names) {
    const folder = join(root, name);
    let parsed: Record<string, unknown>;
    try {
      parsed = JSON.parse(await readFile(join(folder, "annotations.json"), "utf8"));
    } catch {
      try {
        if ((await stat(join(folder, "annotations.json"))).isFile()) unreadable.push(name);
      } catch {
        // not an annotated project at all
      }
      continue;
    }

    const drawn = ((parsed.annotations as unknown[]) || []).length
      + ((parsed.elements as unknown[]) || []).length;
    const raster = await hasRaster(folder);

    if (!raster && !drawn) { empty.push(name); continue; }
    if (!raster) { noSource.push(name); continue; }
    if (!drawn) { blank.push(name); continue; }

    const scale = Object.keys((parsed.floor_scale as object) || {}).length > 0;
    const areas = Array.isArray(parsed.exterior_areas) && parsed.exterior_areas.length > 0;
    (scale && areas ? ready : todo).push(name);
  }

  return Response.json(
    {
      annotated: ready.length + todo.length + noSource.length + empty.length
        + blank.length + unreadable.length,
      ready: ready.sort(),
      todo: todo.sort(),
      no_source: noSource.sort(),
      empty: empty.sort(),
      blank: blank.sort(),
      unreadable: unreadable.sort(),
    },
    { headers: { "Cache-Control": "no-store" } },
  );
}
