// Workbench-owned furniture for one floor of one project.
// See plans/move-furniture-to-workbench.md, step 3.
//
// This is the successor to the annotator's `symbols` array, which is the data
// build-simplifier-render-plan.py actually turns into rendered furniture
// ("placements <- Rainer's hand-placed Ausstattung symbols, which is the whole
// point"). Two things change in the move and nothing else:
//
//   1. Coordinates are MILLIMETRES, not normalized 0-1. The workbench edits
//      canonical mm geometry, and the plan builder converts to mm anyway. A
//      normalized position is meaningless without the scale and the lost
//      image's aspect ratio — the exact trap that cost a day on
//      onehalfstorey_020.
//   2. It lives in the workbench data root, not in projects/. The annotation
//      package stays an immutable record of what was annotated.
//
// The symbol vocabulary is unchanged: same keys, same measured footprints,
// from the catalogue ported verbatim in symbol-catalog.mjs. A key this file
// does not recognise is rejected rather than stored, because a typo'd key
// renders as nothing at all and is invisible until someone looks at a picture.
//
// Presentation-only: furniture never enters geometry_hash, before or after.

import { getSymbol } from "./symbol-catalog.mjs";

export const FURNITURE_SCHEMA = "workbench-furniture-v1";

// Which millimetre space the positions are in. The renderer refuses a file
// that does not say, rather than approximating: a silently mis-spaced sofa
// lands in the wrong room looking plausible.
//
// Furniture is now placed on the CORRECTION document — the plan with the
// straightened walls — so the coordinates are that document's millimetres,
// SVG Y down. The old id described the annotation-derived render space and
// became a label that lied about its own contents the moment the editor
// moved. Files carrying it are refused rather than reinterpreted: the two
// spaces differ by a non-uniform factor per axis.
// Der Raum der BAU-Geometrie, wie geometry_only sie liefert: mm, y nach
// unten (Bildschirm), innerhalb der Raumausdehnung des Geschosses gespiegelt.
// Bis 2026-08-21 stand hier "correction-document-mm-svg-y-down-v1" -- derselbe
// Name, den auch der Korrektur-Kandidat traegt, obwohl es ein ANDERES Haus
// ist. Folge: alle Moebel aus dem Moebel-Schritt wurden im Bau gespiegelt
// eingebaut (Waschmaschine im HWR gesetzt, im Schlafzimmer gerendert).
// build-simplifier-render-plan.py rechnet diesen Raum beim Lesen nach Frame
// (y oben) um; alte Dateien migriert scripts/moebel-migrieren.py.
export const RENDER_COORDINATE_SPACE = "render-geometry-mm-y-down-v1";
export const LEGACY_RENDER_SPACE = "simplifier-render-plan-mm-v1";

export function emptyFurnitureDocument(projectId, floorId) {
  return {
    schema: FURNITURE_SCHEMA,
    project_id: projectId,
    floor_id: floorId,
    coordinate_space: RENDER_COORDINATE_SPACE,
    updated_at: null,
    symbols: [],
  };
}

function finiteNumber(value) {
  const number = Number(value);
  return Number.isFinite(number) ? number : null;
}

function normalizePoint(point) {
  if (!Array.isArray(point) || point.length < 2) return null;
  const x = finiteNumber(point[0]);
  const y = finiteNumber(point[1]);
  return x === null || y === null ? null : [Math.round(x * 10) / 10, Math.round(y * 10) / 10];
}

/**
 * Rotation is stored in whole degrees, 0-359. The annotator offered 45-degree
 * steps from a menu but free rotation from a drag, and both ended up in the
 * same field; normalising here keeps "is this rotated?" a single comparison
 * everywhere downstream.
 */
function normalizeRotation(value) {
  const number = finiteNumber(value) ?? 0;
  return ((Math.round(number) % 360) + 360) % 360;
}

export function normalizeFurnitureSymbol(entry, index = 0) {
  const key = `${entry?.symbol || ""}`;
  const symbol = getSymbol(key);
  if (!symbol) throw new Error(`Unknown furniture symbol: ${key || "(none)"}`);

  const normalized = {
    id: `${entry?.id || `${Date.now()}_${index}`}`,
    symbol: key,
    rotation_deg: normalizeRotation(entry?.rotation_deg),
    mirrored: entry?.mirrored === true,
  };

  if (symbol.placement === "stamp") {
    const position = normalizePoint(entry?.position_mm);
    if (!position) throw new Error(`Symbol ${key} needs a position_mm [x, y].`);
    normalized.position_mm = position;
    // The catalogue footprint is the default; a measurement taken off the
    // drawing overrides it, exactly as the annotator did — the drawing wins
    // over the nominal size of furniture in general.
    const width = finiteNumber(entry?.footprint_mm?.width_mm);
    const depth = finiteNumber(entry?.footprint_mm?.depth_mm);
    normalized.footprint_mm = (width > 0 && depth > 0)
      ? { width_mm: Math.round(width), depth_mm: Math.round(depth) }
      : { ...symbol.footprint_mm };
  } else {
    // path (Küchenzeile) and rect (Kücheninsel, Abstellschrank) carry drawn
    // geometry instead of a single point.
    const points = (entry?.points_mm || []).map(normalizePoint).filter(Boolean);
    if (points.length < 2) {
      throw new Error(`Symbol ${key} is a ${symbol.placement} tool and needs at least two points_mm.`);
    }
    normalized.points_mm = points;
    if (symbol.placement === "path") normalized.depth_mm = symbol.depth_mm;
  }
  // Glas-Schiebetuer: Fluegelzahl 1-3, sonst 2 (GLAS-SCHIEBETUER-001). Ohne
  // diese Zeile fiele das Feld beim Speichern still weg.
  if (key === "glasschiebetuer") {
    const n = Number(entry?.fluegel);
    normalized.fluegel = [1, 2, 3].includes(n) ? n : 2;
  }

  if (!normalized.mirrored && symbol.mirrorable === false) delete normalized.mirrored;
  return normalized;
}

export function normalizeFurnitureDocument(
  document,
  { projectId, floorId, geometryIdentity, floorRegistration } = {},
) {
  // Codex review, 2026-09-18: this function used to overwrite ANY incoming
  // `coordinate_space` with RENDER_COORDINATE_SPACE unconditionally -- correct
  // for a document this editor itself produced, but a silent relabel if the
  // loaded file was still LEGACY_RENDER_SPACE (never converted, e.g. loaded
  // and re-saved before `moebel-migrieren.py` ran). `useFurniture()` on the
  // client spreads the loaded document forward on every save (`{...current,
  // symbols: ...}`), so a legacy label survives untouched all the way here.
  // Relabelling it would mask exactly the state build-simplifier-render-
  // plan.py's `workbench_furniture()` already refuses to build -- the save
  // would make a legacy file LOOK migrated without transforming a single
  // coordinate. Refuse instead, same policy as that Python-side refusal.
  const eingehenderRaum = document?.coordinate_space;
  if (eingehenderRaum && eingehenderRaum !== RENDER_COORDINATE_SPACE) {
    throw new Error(
      `Diese Moebel stehen im Raum "${eingehenderRaum}", nicht im aktuellen `
      + `"${RENDER_COORDINATE_SPACE}". Speichern abgelehnt, um sie nicht falsch `
      + `umzuetikettieren. ${eingehenderRaum === LEGACY_RENDER_SPACE
        ? `Einmal migrieren: python scripts/moebel-migrieren.py ${projectId || document?.project_id || ""}`
        : "Unbekannter Raum -- pruefen, woher dieses Dokument kommt."}`,
    );
  }
  const entries = Array.isArray(document?.symbols) ? document.symbols : [];
  const seen = new Set();
  const symbols = entries.map((entry, index) => {
    const normalized = normalizeFurnitureSymbol(entry, index);
    // Duplicate ids would make "move the second sofa" ambiguous.
    if (seen.has(normalized.id)) normalized.id = `${normalized.id}_${index}`;
    seen.add(normalized.id);
    return normalized;
  });
  return {
    schema: FURNITURE_SCHEMA,
    project_id: `${projectId || document?.project_id || ""}`,
    floor_id: `${floorId || document?.floor_id || ""}`,
    // Stamped by the writer, never carried over from the posted document.
    // Preserving the client's value meant a file saved under the old space kept
    // claiming it forever, no matter how often it was re-saved — the tag could
    // never correct itself. What is being written now is what this code writes.
    coordinate_space: RENDER_COORDINATE_SPACE,
    // Welche Zeichnung war das? Der Editor zeichnet die Geometrie des
    // Bau-Compilers, also gilt beim Speichern dessen heutige Identitaet.
    // Fehlt sie (nicht ermittelbar), bleibt das Feld weg -- Altbestand
    // ohne Stempel baut weiter (build-simplifier-render-plan.py).
    ...(geometryIdentity ? { geometry_identity: geometryIdentity } : {}),
    // Der Editor zeigt Obergeschosse REGISTRIERT (frame_for_level), also
    // sind frisch gespeicherte Koordinaten registrierte Koordinaten.
    // Ohne diese Zeile loeschte jedes Speichern im Editor die Marke, die
    // moebel-registrieren.py gesetzt hat, und der naechste Bau verlangte
    // die Migration erneut (gefunden 2026-08-23 beim Lesen dieses Pfads).
    ...(floorRegistration ? { floor_registration: floorRegistration } : {}),
    updated_at: new Date().toISOString(),
    symbols,
  };
}

/**
 * Which catalogue symbols make sense in a room, by its German name. Drives the
 * palette filter, same knowledge the annotator used.
 */
export { symbolsForRoomLabel, SYMBOL_CATALOG, SYMBOL_CATEGORIES, getSymbol } from "./symbol-catalog.mjs";

/**
 * Axis-aligned footprint of a placed stamp, in mm, for hit-testing and for
 * drawing. Rotation is applied about the centre; mirroring does not change the
 * outline, only which way the artwork faces.
 */
export function symbolBoundsMm(placed) {
  const symbol = getSymbol(placed.symbol);
  if (!symbol || symbol.placement !== "stamp") return null;
  const width = placed.footprint_mm?.width_mm ?? symbol.footprint_mm.width_mm;
  const depth = placed.footprint_mm?.depth_mm ?? symbol.footprint_mm.depth_mm;
  const radians = (placed.rotation_deg * Math.PI) / 180;
  const cos = Math.abs(Math.cos(radians));
  const sin = Math.abs(Math.sin(radians));
  const spanX = width * cos + depth * sin;
  const spanY = width * sin + depth * cos;
  const [x, y] = placed.position_mm;
  return {
    x: x - spanX / 2, y: y - spanY / 2,
    width: spanX, height: spanY,
  };
}

/**
 * A world-space pointer delta (from a piece's centre), turned into the
 * piece's OWN local frame -- i.e. the inverse of the `rotate(rotation_deg)`
 * SVG transform the piece is drawn under. The resize handles sit at local
 * (±width/2, ±depth/2) inside that same rotated group (FurnitureSvg /
 * CorrectionFurnitureLayer), so a drag has to be un-rotated before it can be
 * read as a width/depth change -- otherwise a piece rotated to ~90°/270°
 * (routine: snapStampToWalls rotates to match the wall it snaps to) has its
 * width and depth swapped, invisible at 0°/180° which is why it went
 * unnoticed (Rainer, 2026-08-22: "x and y are mixed up" when scaling).
 */
export function worldDeltaToLocalMm(dx, dy, rotationDeg) {
  const radians = (rotationDeg * Math.PI) / 180;
  const cos = Math.cos(radians);
  const sin = Math.sin(radians);
  return {
    x: dx * cos + dy * sin,
    y: -dx * sin + dy * cos,
  };
}

export function symbolAtPointMm(document, point) {
  // Last drawn wins, so a small item dropped on a rug is the one you grab.
  for (let index = (document.symbols || []).length - 1; index >= 0; index -= 1) {
    const placed = document.symbols[index];
    const box = symbolBoundsMm(placed);
    if (!box) continue;
    if (point[0] >= box.x && point[0] <= box.x + box.width
      && point[1] >= box.y && point[1] <= box.y + box.height) {
      return placed;
    }
  }
  return null;
}

/**
 * Der Stuhl, der zu einem gesetzten Schreibtisch gehoert, oder null.
 *
 * Rainer, 2026-10-13: "could you also include the desk chair whenever a desk
 * is added? it is actually one set right?" Vor die Vorderseite (lokal +y),
 * Gesicht zum Tisch, 150 mm unter die Platte geschoben -- dieselbe Rechnung
 * wie `buero()` in moebel-vorschlag.mjs ("Bereich einrichten").
 */
const SCHREIBTISCHE = new Set(["schreibtisch", "schreibtisch_kind"]);

export function deskChairFor(desk) {
  if (!desk || !SCHREIBTISCHE.has(desk.symbol) || !desk.position_mm) return null;
  const tisch = getSymbol(desk.symbol);
  const stuhl = getSymbol("schreibtischstuhl");
  if (!tisch?.footprint_mm || !stuhl?.footprint_mm) return null;
  const tiefe = Number(desk.footprint_mm?.depth_mm ?? tisch.footprint_mm.depth_mm);
  const stuhlTiefe = Number(stuhl.footprint_mm.depth_mm);
  const vor = tiefe / 2 + stuhlTiefe / 2 - 150;
  const drehung = Number(desk.rotation_deg) || 0;
  const r = (drehung * Math.PI) / 180;
  const [x, y] = desk.position_mm;
  return {
    symbol: "schreibtischstuhl",
    position_mm: [Math.round(x - Math.sin(r) * vor), Math.round(y + Math.cos(r) * vor)],
    rotation_deg: (Math.round(drehung) + 180) % 360,
    mirrored: false,
    footprint_mm: {
      width_mm: Number(stuhl.footprint_mm.width_mm),
      depth_mm: stuhlTiefe,
    },
  };
}
