/**
 * What is wrong with this house, before you spend an hour on it.
 *
 * Rainer, 2026-08-19: "every single floorplan is a fight from beginning to
 * end". He is right, and the reason is that every failure in this pipeline is
 * SILENT. In one day: a scale saved onto the wrong floor and looked done;
 * eight drawn Aussenflaechen thrown away because that scale was missing; 65
 * houses with wound stairs built as straight ramps; furniture written to a
 * different data root than the renders. Nothing warned. Each one was found by
 * digging after the fact.
 *
 * So this reports the traps by name, per house, from the annotation itself:
 *
 *   scale        per FLOOR -- "Massstab festlegen" writes only to the active
 *                floor, so it is easy to set it twice on the same one. The
 *                render plan refuses any level without one.
 *   surroundings drawn areas are silently dropped when the scale is missing,
 *                so areas-without-scale is called out as its own fault.
 *   stairs       point count decides the type (2 straight, 3 quarter,
 *                4+ half/multi turn). All of them build correctly now, but a
 *                1-point or empty path cannot.
 *   image        no raster means no scale can be measured at all.
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

type Finding = { level: "blocker" | "warning" | "ok"; what: string; detail: string; fix?: string };

function stairKind(points: number) {
  if (points >= 4) return "halbgewendelt / Podesttreppe";
  if (points === 3) return "viertelgewendelt";
  if (points === 2) return "gerade";
  return "unbrauchbar";
}

export async function GET(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });

  const plan = new URL(request.url).searchParams.get("plan") || "";
  if (!/^[A-Za-z0-9_-]+$/.test(plan)) {
    return Response.json({ error: "plan is required." }, { status: 400 });
  }

  const folder = resolve(process.cwd(), "..", "floorplan-simplifier", "projects", plan);
  let annotation: Record<string, any>;
  try {
    annotation = JSON.parse(await readFile(join(folder, "annotations.json"), "utf8"));
  } catch {
    return Response.json({ plan, findings: [
      { level: "blocker", what: "Annotation", detail: "Keine annotations.json in diesem Projekt." },
    ] });
  }

  const findings: Finding[] = [];

  // --- a raster to measure against -----------------------------------------
  let hasRaster = false;
  try {
    const entries = await readdir(folder);
    hasRaster = entries.some((e) => RASTER.some((x) => e.toLowerCase().endsWith(x)));
    if (!hasRaster) {
      for (const entry of entries) {
        try {
          if ((await stat(join(folder, entry))).isDirectory()) {
            const inner = await readdir(join(folder, entry));
            if (inner.some((e) => RASTER.some((x) => e.toLowerCase().endsWith(x)))) {
              hasRaster = true;
              break;
            }
          }
        } catch { /* keep looking */ }
      }
    }
  } catch { /* handled below */ }
  findings.push(hasRaster
    ? { level: "ok", what: "Vorlage", detail: "Bild im Ordner" }
    : { level: "blocker", what: "Vorlage", detail: "Kein Bild im Ordner - ohne Bild laesst sich kein Massstab messen." });

  // --- the scale, PER FLOOR ------------------------------------------------
  const levels: string[] = Array.from(new Set(
    ((annotation.annotations as any[]) || []).map((a) => a?.floor_level).filter(Boolean),
  ));
  const scale: Record<string, number> = annotation.floor_scale || {};
  const missing = levels.filter((l) => !scale[l]);
  if (levels.length === 0) {
    findings.push({ level: "warning", what: "Massstab", detail: "Keine annotierten Geschosse gefunden." });
  } else if (missing.length === 0) {
    findings.push({ level: "ok", what: "Massstab", detail: `gesetzt fuer ${levels.join(", ")}` });
  } else {
    // Not every missing level is equally bad, and calling them all blockers
    // produced a false alarm on twostorey_030, which builds fine.
    //   - The GROUND floor's scale maps the Aussenflaechen ("groundfloor if
    //     present, else the first level"). Without it they are dropped.
    //   - Any other level only matters to the annotation-proof path, which
    //     refuses a level without a scale. Building from an approved revision
    //     does not care.
    const ground = levels.includes("groundfloor") ? "groundfloor" : levels[0];
    const groundMissing = missing.includes(ground);
    findings.push({
      level: groundMissing ? "blocker" : "warning",
      what: "Massstab",
      detail: groundMissing
        ? `fehlt fuer ${ground}${Object.keys(scale).length ? ` (gesetzt nur fuer ${Object.keys(scale).join(", ")})` : ""}`
        : `fehlt fuer ${missing.join(", ")} - fuer den Bau aus einer freigegebenen Revision reicht ${ground}, `
          + "nur der Annotations-Pfad braucht jedes Geschoss",
      fix: "„Massstab festlegen“ schreibt nur auf das AKTIVE Geschoss. „Gebäudemaß“ setzt alle Geschosse auf einmal.",
    });
  }

  // --- surroundings --------------------------------------------------------
  const areas = (annotation.exterior_areas as any[]) || [];
  if (areas.length === 0) {
    findings.push({ level: "warning", what: "Umgebung", detail: "Keine Aussenflaechen gezeichnet - das Haus steht auf blankem Boden." });
  } else if (missing.includes(levels.includes("groundfloor") ? "groundfloor" : levels[0])) {
    findings.push({
      level: "blocker",
      what: "Umgebung",
      detail: `${areas.length} Flaechen gezeichnet, werden aber VERWORFEN weil der Massstab fehlt.`,
      fix: "Erst den Massstab setzen, dann sind die Flaechen sofort gueltig - neu zeichnen ist nicht noetig.",
    });
  } else {
    findings.push({ level: "ok", what: "Umgebung", detail: `${areas.length} Flaechen` });
  }

  // --- stairs --------------------------------------------------------------
  const stairs = ((annotation.elements as any[]) || []).filter((e) => e?.type === "stairs");
  if (stairs.length === 0) {
    findings.push({ level: "ok", what: "Treppe", detail: "keine (eingeschossig?)" });
  } else {
    const bad = stairs.filter((e) => ((e.points || []).length) < 2);
    const kinds = stairs.map((e) => `${e.floor_level}: ${stairKind((e.points || []).length)}`);
    findings.push(bad.length
      ? { level: "blocker", what: "Treppe", detail: `${bad.length} Treppe(n) mit weniger als 2 Punkten - daraus laesst sich keine Laufrichtung lesen.` }
      : { level: "ok", what: "Treppe", detail: kinds.join("  |  ") });
  }

  const blockers = findings.filter((f) => f.level === "blocker").length;
  return Response.json(
    { plan, ready: blockers === 0, blockers, findings },
    { headers: { "Cache-Control": "no-store" } },
  );
}
