"use client";
/* eslint-disable @typescript-eslint/no-explicit-any, @next/next/no-img-element, react-hooks/refs */

import { sichtKasten, zoomUmZeiger, ZOOM_MIN, ZOOM_MAX, ZOOM_SCHRITT } from "@/lib/floorplan-workbench/sicht.mjs";
import { useEffect, useMemo, useRef, useState } from "react";
import { CorrectionFurnitureLayer, FurniturePalette, useFurniture, richtePunkteAus, schiebePunkte, punktSchrittMm, loeschePunkt, istDoppelklickDruck, leereRaeume, ladeMoebel, BereichEinrichten, mitteVon } from "./furniture";
import { richteBereichEin, richteAlleRaeumeEin, punktImPolygon, raumtypAusName, rechteckVon, RAUMTYPEN } from "@/lib/generator/moebel-vorschlag.mjs";
import { furnitureViewDocument } from "@/lib/generator/furniture-live-bootstrap.mjs";
import { getSymbol } from "@/lib/generator/symbol-catalog.mjs";
import { worldDeltaToLocalMm, symbolBoundsMm } from "@/lib/generator/furniture-document.mjs";
import {
  commitEditorHistory,
  CORRECTION_DEFAULTS,
  createEditorHistory,
  redoEditorHistory,
  resetEditorHistory,
  snapCoordinate,
  undoEditorHistory,
  withUpdatedHash,
} from "@/lib/generator/correction-editor.mjs";
import {
  doorColour,
  FLOORPLAN_RULEBOOK_VERSION,
  FLOORPLAN_RULES,
} from "@/lib/generator/floorplan-rulebook.mjs";

type Point = [number, number];
const ROOM_COLORS: Record<string, string> = {
  living: "#d9f7e5",
  sleeping: "#f5f1e8",
  wet: "#dcecff",
  service: "#fff1bd",
  flex: "#f4f1ec",
  circulation: "#ece9e2",
};
type Selection =
  | { type: "room"; id: string; point: number }
  | { type: "wall"; id: string; point: 0 | 1 }
  | { type: "opening"; id: string }
  | { type: "stair"; point: number };

function openingPoint(opening: any, wall: any): Point {
  return [
    wall.start[0] + (wall.end[0] - wall.start[0]) * opening.position,
    wall.start[1] + (wall.end[1] - wall.start[1]) * opening.position,
  ];
}

function openingEndpoints(opening: any, wall: any): [Point, Point] {
  const dx = wall.end[0] - wall.start[0];
  const dy = wall.end[1] - wall.start[1];
  const length = Math.max(1, Math.hypot(dx, dy));
  const half = Math.min(0.45, opening.width / length / 2);
  return [opening.position - half, opening.position + half].map((ratio) => [
    wall.start[0] + dx * Math.max(0, Math.min(1, ratio)),
    wall.start[1] + dy * Math.max(0, Math.min(1, ratio)),
  ]) as [Point, Point];
}

function documentBounds(document: any, floorIndex?: number) {
  const floors = floorIndex === undefined ? document.floors : [document.floors[floorIndex]];
  const points: Point[] = floors.flatMap((floor: any) => [
    ...(floor.footprint || []),
    ...floor.rooms.flatMap((room: any) => room.polygon),
    ...floor.walls.flatMap((wall: any) => [wall.start, wall.end]),
    ...(document.shared_stair_core?.polygon || []),
  ]);
  const xs = points.map((point) => point[0]);
  const ys = points.map((point) => point[1]);
  return {
    minX: Math.min(...xs) - 550,
    minY: Math.min(...ys) - 550,
    width: Math.max(...xs) - Math.min(...xs) + 1100,
    height: Math.max(...ys) - Math.min(...ys) + 1100,
  };
}

const MASSING_VIEWS = [
  { id: "garden", label: "Gartenseite", quarterTurns: 0 },
  { id: "street", label: "StraÃŸenseite", quarterTurns: 2 },
  { id: "east", label: "Ostseite", quarterTurns: 1 },
  { id: "west", label: "Westseite", quarterTurns: 3 },
] as const;

function Massing({ document, view }: { document: any; view: string }) {
  const footprint = document.floors[0].footprint as Point[];
  const footprintBox = documentBounds({ ...document, floors: [document.floors[0]] }, 0);
  const scale = 300 / Math.max(footprintBox.width, footprintBox.height);
  const floorHeight = Number(document.building?.floor_height_mm) || 2800;
  const centerX = footprint.reduce((sum, point) => sum + point[0], 0) / footprint.length;
  const centerY = footprint.reduce((sum, point) => sum + point[1], 0) / footprint.length;
  const quarterTurns = MASSING_VIEWS.find((candidate) => candidate.id === view)?.quarterTurns ?? 0;
  const rotate = (point: Point): Point => {
    let x = point[0] - centerX;
    let y = point[1] - centerY;
    for (let index = 0; index < quarterTurns; index += 1) [x, y] = [-y, x];
    return [x, y];
  };
  const project = (point: Point, z: number) => {
    const [x, y] = rotate(point);
    return {
      x: 325 + x * scale * 0.78 - y * scale * 0.52,
      y: 300 + x * scale * 0.27 + y * scale * 0.27 - z * scale * 0.72,
    };
  };
  const asPoints = (points: Array<{ x: number; y: number }>) =>
    points.map((point) => `${point.x.toFixed(1)},${point.y.toFixed(1)}`).join(" ");
  const roofBase = document.floors.length * floorHeight;
  const minX = Math.min(...footprint.map((point) => point[0]));
  const maxX = Math.max(...footprint.map((point) => point[0]));
  const minY = Math.min(...footprint.map((point) => point[1]));
  const maxY = Math.max(...footprint.map((point) => point[1]));
  const ridgeY = (minY + maxY) / 2;
  const ridgeHeight = Math.min(2200, Math.max(1300, (maxY - minY) * 0.32));
  const roofLeft = [
    project([minX, minY], roofBase),
    project([maxX, minY], roofBase),
    project([maxX, ridgeY], roofBase + ridgeHeight),
    project([minX, ridgeY], roofBase + ridgeHeight),
  ];
  const roofRight = [
    project([minX, ridgeY], roofBase + ridgeHeight),
    project([maxX, ridgeY], roofBase + ridgeHeight),
    project([maxX, maxY], roofBase),
    project([minX, maxY], roofBase),
  ];
  return <svg viewBox="0 0 650 390" className="w-full rounded-2xl bg-gradient-to-b from-sky-50 to-stone-100" aria-label="Corrected deterministic 1.5-storey massing preview">
    <text x="18" y="26" fontSize="12" fontWeight="700">Same approved geometry Â· {document.geometry_hash.slice(0, 16)}â€¦</text>
    <text x="18" y="46" fontSize="11" fill="#57534e">1.5 storeys Â· gable roof Â· wall-linked openings</text>
    {document.floors.map((floor: any, floorIndex: number) => {
      const lower = footprint.map((point) => project(point, floorIndex * floorHeight));
      const upper = footprint.map((point) => project(point, (floorIndex + 1) * floorHeight));
      return <g key={floor.id}>
        {footprint.map((_, index) => {
          const next = (index + 1) % footprint.length;
          return <polygon
            key={index}
            points={asPoints([lower[index], lower[next], upper[next], upper[index]])}
            fill={index % 2 ? "#e8dfd1" : "#f4eee4"}
            stroke="#4b4238"
            strokeWidth="1.4"
          />;
        })}
        {floor.openings.map((opening: any) => {
          const wall = floor.walls.find((candidate: any) => candidate.id === opening.wall_id);
          if (!wall || wall.wall_type !== "exterior") return null;
          const [first, second] = openingEndpoints(opening, wall);
          const base = floorIndex * floorHeight;
          const lower = opening.opening_type === "door"
            ? base
            : base + Number(opening.sill_height_mm || FLOORPLAN_RULES.windows.defaultSillHeightMm);
          const upper = opening.opening_type === "door"
            ? base + Number(opening.height_mm || 2100)
            : lower + Number(opening.height_mm || FLOORPLAN_RULES.windows.defaultHeightMm);
          const openingFace = [
            project(first, lower),
            project(second, lower),
            project(second, upper),
            project(first, upper),
          ];
          return <polygon
            key={opening.id}
            points={asPoints(openingFace)}
            fill={opening.opening_type === "window" ? "#6fb7d6" : doorColour(opening)}
            stroke="#ffffff"
            strokeWidth="1"
          />;
        })}
      </g>;
    })}
    <polygon points={asPoints(roofLeft)} fill="#77685d" stroke="#3f3732" strokeWidth="1.5" />
    <polygon points={asPoints(roofRight)} fill="#5f5148" stroke="#3f3732" strokeWidth="1.5" />
    <line x1="30" y1="352" x2="620" y2="352" stroke="#82926f" strokeWidth="2" />
    <text x="325" y="378" textAnchor="middle" fontSize="11" fill="#57534e">Deterministic massing guide â€” no AI redraw</text>
  </svg>;
}

function stairArrow(path: Point[], size = 180) {
  const end = path.at(-1);
  const previous = path.at(-2);
  if (!end || !previous) return "";
  const dx = end[0] - previous[0];
  const dy = end[1] - previous[1];
  const length = Math.max(1, Math.hypot(dx, dy));
  const ux = dx / length;
  const uy = dy / length;
  const nx = -uy;
  const ny = ux;
  const baseX = end[0] - ux * size;
  const baseY = end[1] - uy * size;
  return [
    end,
    [baseX + nx * size * 0.55, baseY + ny * size * 0.55],
    [baseX - nx * size * 0.55, baseY - ny * size * 0.55],
  ].map((point) => point.join(",")).join(" ");
}

function polygonBox(polygon: Point[]) {
  const xs = polygon.map((point) => point[0]);
  const ys = polygon.map((point) => point[1]);
  return {
    minX: Math.min(...xs),
    maxX: Math.max(...xs),
    minY: Math.min(...ys),
    maxY: Math.max(...ys),
  };
}

function reviewStairPath(stair: any): Point[] {
  const box = polygonBox(stair.polygon || []);
  const centerX = (box.minX + box.maxX) / 2;
  const height = box.maxY - box.minY;
  const margin = Math.max(220, height * 0.18);
  return [
    [centerX, box.maxY - margin],
    [centerX, box.minY + margin],
  ];
}

function roomLabelPoint(room: any, stair: any): Point {
  const roomBox = polygonBox(room.polygon);
  const center: Point = [
    (roomBox.minX + roomBox.maxX) / 2,
    (roomBox.minY + roomBox.maxY) / 2,
  ];
  if (room.kind !== "circulation" || !stair?.polygon?.length) return center;
  const stairBox = polygonBox(stair.polygon);
  const overlaps = Math.min(roomBox.maxX, stairBox.maxX) > Math.max(roomBox.minX, stairBox.minX)
    && Math.min(roomBox.maxY, stairBox.maxY) > Math.max(roomBox.minY, stairBox.minY);
  if (!overlaps) return center;
  const leftWidth = stairBox.minX - roomBox.minX;
  const rightWidth = roomBox.maxX - stairBox.maxX;
  return [
    leftWidth >= rightWidth
      ? (roomBox.minX + stairBox.minX) / 2
      : (stairBox.maxX + roomBox.maxX) / 2,
    (Math.max(roomBox.minY, stairBox.minY) + Math.min(roomBox.maxY, stairBox.maxY)) / 2,
  ];
}

function GeometryEditor({
  zeigeHintergrund = true,
  history,
  setHistory,
  floorIndex,
  selection,
  setSelection,
  grid,
  showHandles,
  furnitureDocument,
  activeSymbolKey,
  selectedFurnitureId,
  onFurniturePlace,
  onFurnitureSelect,
  onFurnitureMove,
  onFurniturePlaceDrawn,
  onFurnitureResize,
  onFurnitureSetPoints,
  onFurnitureMoveDrawn,
  sicht,
  setSicht,
  punktAuswahl,
  onPunktWaehlen,
  onPunktRechtsklick,
  onPunktMenue,
  onStampMenu,
  overrideFloor,
  projectId,
  // MOEBEL-BEREICH-EINRICHTEN-001
  einrichtenAktiv = false,
  einrichtBereich = null,
  onEinrichtBereich,
  moebelAuswahl = [],
  onFurnitureMoveGroup,
}: any) {
  const furnitureDrag = useRef<{ id: string; dx: number; dy: number } | null>(null);
  // Gruppenzug: Startpunkt und die Moebel, wie sie beim Zugbeginn standen.
  const gruppenZug = useRef<{ start: Point; originale: Record<string, any>; erster: boolean } | null>(null);
  // Bereich einrichten: Druckpunkt und die Rechteck-Vorschau beim Aufziehen.
  const einrichtZug = useRef<Point | null>(null);
  const [einrichtVorschau, setEinrichtVorschau] = useState<Point[] | null>(null);
  // Selbst gezeichneter Bereich: Ecken klicken, Doppelklick schliesst ab.
  // Rainer, 2026-10-09: "i have to be able to create my own areas".
  const [einrichtEcken, setEinrichtEcken] = useState<Point[]>([]);
  const einrichtDruck = useRef<{ t: number; x: number; y: number } | null>(null);
  useEffect(() => { if (!einrichtenAktiv) setEinrichtEcken([]); }, [einrichtenAktiv, floorIndex]);
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setEinrichtEcken([]);
      if (event.key === "Enter" && einrichtEcken.length >= 3) {
        onEinrichtBereich?.({ polygon: einrichtEcken, raumName: null });
        setEinrichtEcken([]);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [einrichtEcken, onEinrichtBereich]);
  const furnitureResize = useRef<{ id: string; centre: Point; rotationDeg: number } | null>(null);
  const rectCorner = useRef<{ id: string; points: Point[]; corner: number } | null>(null);
  // Einzelne Punkte an einem gezeichneten Lauf (Rainer, 2026-08-28: "make the
  // points selectable and moveable"). Die Auswahl gilt fuer das gerade
  // gewaehlte Moebel und faellt weg, sobald ein anderes gewaehlt wird.
  const pathPointDrag = useRef<{ id: string; punkt: number } | null>(null);
  const drawnDrag = useRef<{ id: string; last: Point } | null>(null);
  const [furnitureDraft, setFurnitureDraft] = useState<Point[]>([]);
  // Aufziehen eines Rechtecks (Kücheninsel): gedrückt gehaltener Zeiger.
  const rectDraw = useRef<{ start: Point } | null>(null);
  // Letzter Druck beim Zeichnen eines Laufs, in BILDSCHIRM-Pixeln.
  // Rainer, 2026-10-09: "eine gerade zeile mit 2 punkten endet immer in 3
  // punkte davon sind 2 fast aufeinander". Ein Doppelklick feuert zwei
  // pointerdown -- der zweite setzte einen Punkt neben den ersten. entdoppelt()
  // misst in Millimetern (60 mm); herausgezoomt ist ein Wackler der Hand
  // mehr als das, also blieb der Punkt. Hier wird der zweite Druck gar nicht
  // erst angehaengt, gemessen dort, wo die Hand ihn gemacht hat.
  const letzterDruck = useRef<{ t: number; x: number; y: number } | null>(null);
  const drawingFurniture = activeSymbolKey
    ? getSymbol(activeSymbolKey)?.placement !== "stamp"
    : false;
  useEffect(() => { setFurnitureDraft([]); }, [activeSymbolKey, floorIndex]);
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      if (event.key === "Escape") setFurnitureDraft([]);
      if (event.key === "Enter" && furnitureDraft.length >= 2) {
        onFurniturePlaceDrawn(activeSymbolKey, furnitureDraft);
        setFurnitureDraft([]);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [furnitureDraft, activeSymbolKey, onFurniturePlaceDrawn]);
  // A kitchen run turns square corners; Shift draws free.
  function squaredPoint(previous: Point | undefined, point: Point): Point {
    if (!previous) return point;
    return Math.abs(point[0] - previous[0]) >= Math.abs(point[1] - previous[1])
      ? [point[0], previous[1]]
      : [previous[0], point[1]];
  }
  const document = history.present;
  // Im Moebel-Schritt der Hausakte zeigt der Editor die Geometrie, DIE
  // GEBAUT WIRD (render_geometry aus build-simplifier-render-plan.py
  // --geometry-only), nicht den Korrektur-Kandidaten. Gemessen an
  // bungalow_036 am 2026-08-21: Editor-Haus bis x=12050, gebautes Haus bis
  // x=10047 -- fuenf korrekt platzierte Moebel (Ecksofa, Kochfeld, Spuele,
  // Lowboard, Fernseher) standen im Render ausserhalb der Bodenplatte.
  // geometry_only existierte genau dafuer und wurde nie aufgerufen.
  const floor = overrideFloor || document.floors[floorIndex];
  const box = (() => {
    const basis = overrideFloor
      ? (() => {
          const pts = overrideFloor.rooms.flatMap((room: any) => room.polygon);
          const xs = pts.map((pt: any) => pt[0]);
          const ys = pts.map((pt: any) => pt[1]);
          return { minX: Math.min(...xs) - 550, minY: Math.min(...ys) - 550,
                   width: Math.max(...xs) - Math.min(...xs) + 1100,
                   height: Math.max(...ys) - Math.min(...ys) + 1100 };
        })()
      : documentBounds(document, floorIndex);
    // Rainer, 2026-10-08, an bungalow_040_31: "i cant access the whole image
    // for furniture". Der Sichtbereich kam nur aus den RAEUMEN; die Vorlage
    // dahinter ist groesser -- sie traegt Masslinien, Beschriftung und
    // Aussenanlagen. Gemessen an diesem Haus: Bild 0..14824 x 0..13502,
    // Sichtbereich 404..13988 x 968..12709 -- oben 968 mm, rechts 837 mm,
    // unten 794 mm abgeschnitten, genau die Masslinien zum Abzeichnen.
    // Dieselbe Bedingung wie beim Zeichnen des Bildes weiter unten, damit
    // der Kasten GENAU dann waechst, wenn auch wirklich eine Vorlage liegt.
    const ecken = (floor as any)?.imageCorners as [number, number][] | null;
    if (!(projectId && floor?.name && floor?.rooms?.length > 0)
        || !ecken || ecken.length !== 4) return basis;
    const xs = ecken.map((q) => q[0]);
    const ys = ecken.map((q) => q[1]);
    const minX = Math.min(basis.minX, ...xs);
    const minY = Math.min(basis.minY, ...ys);
    const maxX = Math.max(basis.minX + basis.width, ...xs);
    const maxY = Math.max(basis.minY + basis.height, ...ys);
    return { minX, minY, width: maxX - minX, height: maxY - minY };
  })();
  // Zoom kommt von der Seite -- dort stehen die Knoepfe. Zwei Zustaende ueber
  // denselben Zoom waeren zwei Wahrheiten.
  const sichtbar = sichtKasten(box, sicht);
  const svgRef = useRef<SVGSVGElement>(null);
  const dragSource = useRef<any>(null);
  const marqueeDrag = useRef<{ start: Point } | null>(null);
  const [marqueeBox, setMarqueeBox] = useState<{ x: number; y: number; w: number; h: number } | null>(null);
  const [marqueeSelection, setMarqueeSelection] = useState<Selection[]>([]);

  // Strg+Rad zoomt um den Zeiger -- dieselbe Geste wie im Annotator, damit
  // man sie nur einmal lernen muss. Nicht ueber React onWheel: der Handler
  // muss `preventDefault` rufen duerfen, und dafuer muss er nicht-passiv
  // angemeldet sein.
  useEffect(() => {
    const svg = svgRef.current;
    if (!svg) return;
    function amRad(event: WheelEvent) {
      if (!event.ctrlKey && !event.metaKey) return;   // ohne Strg scrollt die Seite
      event.preventDefault();
      const rect = svg!.getBoundingClientRect();
      const anteil = { x: (event.clientX - rect.left) / rect.width,
                       y: (event.clientY - rect.top) / rect.height };
      setSicht((jetzt: { zoom: number; cx: number; cy: number } | null) => zoomUmZeiger(
        box, jetzt,
        (jetzt?.zoom || ZOOM_MIN) * (event.deltaY < 0 ? ZOOM_SCHRITT : 1 / ZOOM_SCHRITT),
        anteil));
    }
    svg.addEventListener("wheel", amRad, { passive: false });
    return () => svg.removeEventListener("wheel", amRad);
  }, [box.minX, box.minY, box.width, box.height]);

  function coordinate(event: React.PointerEvent): Point {
    const svg = svgRef.current!;
    const matrix = svg.getScreenCTM()!;
    return [
      snapCoordinate((event.clientX - matrix.e) / matrix.a, grid),
      snapCoordinate((event.clientY - matrix.f) / matrix.d, grid),
    ];
  }
  function pointFor(sel: Selection, doc: any): Point {
    const fl = doc.floors[floorIndex];
    if (sel.type === "room") return fl.rooms.find((room: any) => room.id === sel.id).polygon[sel.point];
    if (sel.type === "wall") { const wall = fl.walls.find((item: any) => item.id === sel.id); return sel.point ? wall.end : wall.start; }
    if (sel.type === "stair") return doc.shared_stair_core.polygon[sel.point];
    return [0, 0];
  }
  function setPointFor(doc: any, sel: Selection, value: Point) {
    const fl = doc.floors[floorIndex];
    if (sel.type === "room") fl.rooms.find((room: any) => room.id === sel.id).polygon[sel.point] = value;
    else if (sel.type === "wall") fl.walls.find((item: any) => item.id === sel.id)[sel.point ? "end" : "start"] = value;
    else if (sel.type === "stair") doc.shared_stair_core.polygon[sel.point] = value;
  }
  function sameSelection(a: Selection, b: Selection) {
    return a.type === b.type && (a as any).id === (b as any).id && (a as any).point === (b as any).point;
  }
  function nudgeGroup(dx: number, dy: number) {
    if (!marqueeSelection.length) return;
    setHistory((current: any) => {
      const before = current.present;
      const next = structuredClone(before);
      for (const sel of marqueeSelection) {
        const [x, y] = pointFor(sel, before);
        setPointFor(next, sel, [snapCoordinate(x + dx, grid), snapCoordinate(y + dy, grid)]);
      }
      return { source: current.source, past: [...current.past, before], present: withUpdatedHash(next), future: [] };
    });
  }
  useEffect(() => {
    function onKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") { setMarqueeSelection([]); return; }
      if (!marqueeSelection.length) return;
      const target = event.target as HTMLElement;
      if (target && ["INPUT", "TEXTAREA", "SELECT"].includes(target.tagName)) return;
      const step = event.shiftKey ? grid * 10 : grid;
      let dx = 0; let dy = 0;
      if (event.key === "ArrowUp") dy = -step;
      else if (event.key === "ArrowDown") dy = step;
      else if (event.key === "ArrowLeft") dx = -step;
      else if (event.key === "ArrowRight") dx = step;
      else return;
      event.preventDefault();
      nudgeGroup(dx, dy);
    }
    window.addEventListener("keydown", onKeyDown);
    return () => window.removeEventListener("keydown", onKeyDown);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [marqueeSelection, grid]);
  function collectPointsInBox(rect: { x: number; y: number; w: number; h: number }): Selection[] {
    const within = (point: Point) => point[0] >= rect.x && point[0] <= rect.x + rect.w && point[1] >= rect.y && point[1] <= rect.y + rect.h;
    const found: Selection[] = [];
    floor.rooms.forEach((room: any) => room.polygon.forEach((point: Point, index: number) => { if (within(point)) found.push({ type: "room", id: room.id, point: index }); }));
    floor.walls.forEach((wall: any) => {
      if (within(wall.start)) found.push({ type: "wall", id: wall.id, point: 0 });
      if (within(wall.end)) found.push({ type: "wall", id: wall.id, point: 1 });
    });
    if (document.shared_stair_core?.polygon) document.shared_stair_core.polygon.forEach((point: Point, index: number) => { if (within(point)) found.push({ type: "stair", point: index }); });
    return found;
  }
  function update(nextPoint: Point) {
    if (!selection) return;
    const next = structuredClone(history.present);
    const targetFloor = next.floors[floorIndex];
    if (selection.type === "room") {
      targetFloor.rooms.find((room: any) => room.id === selection.id).polygon[selection.point] = nextPoint;
    } else if (selection.type === "wall") {
      targetFloor.walls.find((wall: any) => wall.id === selection.id)[selection.point ? "end" : "start"] = nextPoint;
    } else if (selection.type === "stair") {
      next.shared_stair_core.polygon[selection.point] = nextPoint;
    } else if (selection.type === "opening") {
      const opening = targetFloor.openings.find((item: any) => item.id === selection.id);
      const wall = targetFloor.walls.find((item: any) => item.id === opening.wall_id);
      const dx = wall.end[0] - wall.start[0];
      const dy = wall.end[1] - wall.start[1];
      const length = dx * dx + dy * dy;
      opening.position = length ? Math.max(0, Math.min(1, ((nextPoint[0] - wall.start[0]) * dx + (nextPoint[1] - wall.start[1]) * dy) / length)) : 0;
    }
    setHistory((current: any) => ({ ...current, present: withUpdatedHash(next) }));
  }
  function begin(event: React.PointerEvent, nextSelection: Selection) {
    event.stopPropagation();
    event.currentTarget.setPointerCapture(event.pointerId);
    dragSource.current = structuredClone(history.present);
    setMarqueeSelection([]);
    setSelection(nextSelection);
  }
  function finish() {
    if (!dragSource.current) return;
    const before = dragSource.current;
    dragSource.current = null;
    setHistory((current: any) => ({
      source: current.source,
      past: [...current.past, before],
      present: current.present,
      future: [],
    }));
  }
  function startMarquee(event: React.PointerEvent) {
    const point = coordinate(event);
    marqueeDrag.current = { start: point };
    setMarqueeBox({ x: point[0], y: point[1], w: 0, h: 0 });
  }
  function updateMarquee(event: React.PointerEvent) {
    if (!marqueeDrag.current) return;
    const point = coordinate(event);
    const [startX, startY] = marqueeDrag.current.start;
    setMarqueeBox({ x: Math.min(startX, point[0]), y: Math.min(startY, point[1]), w: Math.abs(point[0] - startX), h: Math.abs(point[1] - startY) });
  }
  function finishMarquee() {
    if (!marqueeDrag.current) return;
    const rect = marqueeBox;
    marqueeDrag.current = null;
    setMarqueeBox(null);
    if (rect && (rect.w > grid || rect.h > grid)) {
      setMarqueeSelection(collectPointsInBox(rect));
    } else {
      setMarqueeSelection([]);
    }
  }
  return <svg
    ref={svgRef}
    // Gezoomt wird ueber den viewBox, NICHT ueber eine CSS-Transformation:
    // `coordinate()` rechnet mit getScreenCTM(), und die kennt den viewBox
    // von selbst. So kann sich der Zeiger nicht von der Zeichnung loesen.
    viewBox={`${sichtbar.minX} ${sichtbar.minY} ${sichtbar.width} ${sichtbar.height}`}
    className="h-[680px] w-full touch-none rounded-2xl border bg-white"
    // MOEBEL-BEREICH-EINRICHTEN-001: im Einrichten-Modus gehoert der Druck
    // dem Bereich, auch wenn er auf einem Moebel landet (Capture-Phase).
    onPointerDownCapture={(event) => {
      if (!einrichtenAktiv) return;
      event.stopPropagation();
      // Zweiter Druck eines Doppelklicks: keine neue Ecke (siehe
      // MOEBEL-DOPPELKLICK-001), der Doppelklick schliesst gleich ab.
      const druck = { t: event.timeStamp, x: event.clientX, y: event.clientY };
      const vorher = einrichtDruck.current;
      einrichtDruck.current = druck;
      if (istDoppelklickDruck(vorher, druck)) return;
      einrichtZug.current = coordinate(event);
      setEinrichtVorschau(null);
    }}
    onPointerDown={(event) => {
      // Placement takes the click before the marquee claims it.
      if (activeSymbolKey) {
        const point = coordinate(event);
        if (drawingFurniture) {
          // Squaring is for PATH runs (Küchenzeile, Vorwandinstallation) which
          // turn right angles. A rect tool (Kücheninsel, Abstellschrank) is two
          // opposite corners — squaring it collapses the rectangle to a line.
          const placement = getSymbol(activeSymbolKey)?.placement;
          const square = !event.shiftKey && placement === "path";
          // Aufziehen als zweiter Weg: druecken, ziehen, loslassen. Die zwei
          // Klicks bleiben, aber ohne Vorschau war das Rechteck blind zu
          // setzen -- wer eng klickte, bekam eine winzige Insel und musste sie
          // hinterher am Griff aufziehen (Rainer, 2026-08-25: "it is very hard
          // to just click pull and thus create it").
          if (placement === "rect") rectDraw.current = { start: point };
          const druck = { t: event.timeStamp, x: event.clientX, y: event.clientY };
          const vorher = letzterDruck.current;
          letzterDruck.current = druck;
          if (placement === "path" && istDoppelklickDruck(vorher, druck)) return;
          setFurnitureDraft((current) => {
            const next = [...current, square ? squaredPoint(current[current.length - 1], point) : point];
            // A rectangle IS two opposite corners — the second click finishes
            // it. No Enter, and no dashed line in between.
            if (placement === "rect" && next.length === 2) {
              onFurniturePlaceDrawn(activeSymbolKey, next);
              return [];
            }
            return next;
          });
        } else {
          onFurniturePlace(point);
        }
        return;
      }
      startMarquee(event);
    }}
    onPointerMove={(event) => {
      if (einrichtZug.current) {
        const [x0, y0] = einrichtZug.current;
        const [x1, y1] = coordinate(event);
        setEinrichtVorschau([[x0, y0], [x1, y0], [x1, y1], [x0, y1]]);
        return;
      }
      // Waehrend des Aufziehens zeigt der Entwurf schon das ganze Rechteck.
      if (rectDraw.current && drawingFurniture) {
        setFurnitureDraft([rectDraw.current.start, coordinate(event)]);
        return;
      }
      const corner = rectCorner.current;
      if (corner) {
        const [x, y] = coordinate(event);
        // Two opposite corners define the rectangle: move the dragged corner,
        // keep the one diagonally across from it.
        const [a, b] = [corner.points[0], corner.points[corner.points.length - 1]];
        const x0 = Math.min(a[0], b[0]); const x1 = Math.max(a[0], b[0]);
        const y0 = Math.min(a[1], b[1]); const y1 = Math.max(a[1], b[1]);
        const fixed: Point = [
          corner.corner === 0 || corner.corner === 3 ? x1 : x0,
          corner.corner === 0 || corner.corner === 1 ? y1 : y0,
        ];
        onFurnitureSetPoints(corner.id, [fixed, [x, y]]);
        return;
      }
      const punktZug = pathPointDrag.current;
      if (punktZug) {
        const item = (furnitureDocument?.symbols || []).find((x: any) => x.id === punktZug.id);
        if (item?.points_mm) {
          const [x, y] = coordinate(event);
          const neu = item.points_mm.map((p: Point, i: number) =>
            (i === punktZug.punkt ? [Math.round(x), Math.round(y)] as Point : p));
          onFurnitureSetPoints(punktZug.id, neu);
        }
        return;
      }
      const dragging = drawnDrag.current;
      if (dragging) {
        const point = coordinate(event);
        onFurnitureMoveDrawn(dragging.id, [point[0] - dragging.last[0], point[1] - dragging.last[1]]);
        dragging.last = point;
        return;
      }
      const sizing = furnitureResize.current;
      if (sizing) {
        const [x, y] = coordinate(event);
        // Symmetric about the centre: the handle is a corner, so the pointer
        // describes half-extents. The handles themselves sit INSIDE the
        // item's rotated group (local ±width/2, ±depth/2), so the world-space
        // pointer delta has to be turned into that same local frame first --
        // otherwise a piece rotated ~90°/270° gets width/depth swapped.
        const local = worldDeltaToLocalMm(
          x - sizing.centre[0], y - sizing.centre[1], sizing.rotationDeg);
        onFurnitureResize(sizing.id, Math.abs(local.x) * 2, Math.abs(local.y) * 2);
        return;
      }
      const gz = gruppenZug.current;
      if (gz) {
        const [x, y] = coordinate(event);
        onFurnitureMoveGroup?.(gz.originale, [x - gz.start[0], y - gz.start[1]], gz.erster);
        gz.erster = false;
        return;
      }
      const drag = furnitureDrag.current;
      if (drag) {
        const [x, y] = coordinate(event);
        onFurnitureMove(drag.id, [x - drag.dx, y - drag.dy]);
        return;
      }
      if (dragSource.current) { update(coordinate(event)); } else { updateMarquee(event); }
    }}
    onPointerUp={(event) => {
      if (einrichtZug.current) {
        const [x0, y0] = einrichtZug.current;
        const [x1, y1] = coordinate(event);
        einrichtZug.current = null;
        setEinrichtVorschau(null);
        if (Math.abs(x1 - x0) > 300 && Math.abs(y1 - y0) > 300) {
          // Aufgezogen: ein Rechteck ist fertig.
          setEinrichtEcken([]);
          onEinrichtBereich?.({ polygon: [[x0, y0], [x1, y0], [x1, y1], [x0, y1]], raumName: null });
        } else if (event.shiftKey) {
          // Shift+Klick: der ganze Raum unter dem Zeiger (Abkuerzung).
          setEinrichtEcken([]);
          const raum = (floor.rooms || []).find((r: any) =>
            (r.polygon || []).length >= 3 && punktImPolygon(x1, y1, r.polygon));
          onEinrichtBereich?.(raum ? { polygon: raum.polygon, raumName: raum.name } : null);
        } else {
          // Ein Klick: eine Ecke. Rechtwinklig zur vorigen, wie beim Lauf.
          setEinrichtEcken((ecken) => {
            const letzte = ecken[ecken.length - 1];
            if (!letzte) return [[x1, y1]];
            const gerade: Point = Math.abs(x1 - letzte[0]) >= Math.abs(y1 - letzte[1])
              ? [x1, letzte[1]] : [letzte[0], y1];
            return [...ecken, gerade];
          });
        }
        return;
      }
      const ziehen = rectDraw.current;
      rectDraw.current = null;
      if (ziehen && drawingFurniture && activeSymbolKey) {
        const ende = coordinate(event);
        // Weit genug gezogen heisst: fertig. Ein Klick auf der Stelle bleibt
        // ein Klick -- dann setzt der zweite die Gegenecke, wie bisher.
        if (Math.abs(ende[0] - ziehen.start[0]) > 300
            || Math.abs(ende[1] - ziehen.start[1]) > 300) {
          onFurniturePlaceDrawn(activeSymbolKey, [ziehen.start, ende]);
          setFurnitureDraft([]);
        } else {
          setFurnitureDraft([ziehen.start]);
        }
      }
      furnitureDrag.current = null; furnitureResize.current = null; gruppenZug.current = null;
      rectCorner.current = null; drawnDrag.current = null; pathPointDrag.current = null;
      finish(); finishMarquee();
    }}
    onDoubleClick={() => {
      if (einrichtenAktiv) {
        if (einrichtEcken.length >= 3) {
          onEinrichtBereich?.({ polygon: einrichtEcken, raumName: null });
          setEinrichtEcken([]);
        }
        return;
      }
      if (drawingFurniture && furnitureDraft.length >= 2) {
        onFurniturePlaceDrawn(activeSymbolKey, furnitureDraft);
        setFurnitureDraft([]);
      }
    }}
  >
    {marqueeSelection.length > 0 && <text x={box.minX + 40} y={box.minY + 90} fontSize="130" fontWeight="700" fill="#b45309">{marqueeSelection.length} points selected · arrow keys to move · Esc to clear</text>}
    {marqueeBox && <rect x={marqueeBox.x} y={marqueeBox.y} width={marqueeBox.w} height={marqueeBox.h} fill="rgba(37,99,235,0.12)" stroke="#2563eb" strokeWidth="10" strokeDasharray="40 20" />}
    {/* Rainer, 2026-09-17: "could you leave my images that i use to
        annotate the images also in the Möbel part?" -- the source photo
        the rooms were drawn against, faint behind the furniture canvas.
        Registered through the real Frame/RegisteredFrame corner transform
        (floor.imageCorners, from geometry_only()'s image_corners_mm) --
        the same maths that places rooms/walls/stairs, not a room-bounding-
        box guess. Rainer, follow-up: "scale is off but it is all from the
        same data how can it be off" -- the bbox guess put the photo at
        the wrong scale/offset whenever the image extended past the drawn
        rooms (garden, roof overhang); this reads the real corners instead.
        Falls back to the old bbox approximation only if a stale cached
        geometry response predates this field.
        No onError hiding: it mutates style.display directly on the DOM
        node, and since React reuses that same node across renders (stable
        position in the tree) and never manages `display` itself, one
        failed load early on left it hidden FOREVER even once a later
        render would have loaded fine (confirmed live). An SVG <image>
        with a 404/failed href already renders nothing by itself, so
        there is nothing to guard against. */}
    {(() => {
      const zeigeReferenz = Boolean(projectId && floor.name && floor.rooms.length > 0);
      // Rainer, 2026-10-30: "show hide background". Nur die Ansicht: der
      // Sichtbereich oben haengt bewusst nicht daran, der Plan springt nicht.
      const bildAn = zeigeReferenz && zeigeHintergrund;
      return <>
        {bildAn && (() => {
          const ecken = floor.imageCorners as [number, number][] | null;
          let x0: number, x1: number, y0: number, y1: number;
          if (ecken && ecken.length === 4) {
            const xs = ecken.map((p) => p[0]);
            const ys = ecken.map((p) => p[1]);
            x0 = Math.min(...xs); x1 = Math.max(...xs);
            y0 = Math.min(...ys); y1 = Math.max(...ys);
          } else {
            const pts = floor.rooms.flatMap((room: any) => room.polygon);
            const xs = pts.map((pt: any) => pt[0]);
            const ys = pts.map((pt: any) => pt[1]);
            const pad = 400;
            x0 = Math.min(...xs) - pad; x1 = Math.max(...xs) + pad;
            y0 = Math.min(...ys) - pad; y1 = Math.max(...ys) + pad;
          }
          return <ReferenzBild
            key={`${projectId}-${floor.name}`}
            projectId={projectId}
            floorName={floor.name}
            x={x0} y={y0} width={x1 - x0} height={y1 - y0}
            // Full opacity on the image itself now that the room fill
            // above it multiplies instead of alpha-blending: multiplying
            // room colour against an already-washed-out (low-opacity,
            // blended-toward-white) image barely tints it at all, since
            // multiply-by-near-white is close to a no-op. The image needs
            // real contrast for the multiply to have anything to work
            // with; the ROOM layer is what stays soft, not this one.
          />;
        })()}
        {floor.rooms.map((room: any) => {
          const label = roomLabelPoint(room, document.shared_stair_core);
          return <g key={room.id}>
          {/* Rainer, 2026-09-17: "why are the uploaded floorplans not
              visible on the möble tab?" -- they WERE drawn, just fully
              hidden: an opaque room fill painted on top of the reference
              image blocks it completely everywhere except the thin gaps
              between rooms. Rainer, follow-up: "well just make the rooms
              multiply thier colors" -- mix-blend-mode:multiply instead of
              lowering fillOpacity: the fill stays full-strength colour
              (doesn't wash out on its own) while still letting the
              photo's own lines/furniture show through underneath, rather
              than both layers going muddy-transparent together. Only
              while a reference image is actually behind it, so a project
              without one keeps its normal flat fill (multiply against
              nothing but the white canvas would just darken it for no
              reason). */}
          <polygon points={room.polygon.map((point: Point) => point.join(",")).join(" ")} fill={ROOM_COLORS[room.kind] || ROOM_COLORS.flex} style={bildAn ? { mixBlendMode: "multiply" } : undefined} stroke="none" />
      <text
        x={label[0]}
        y={label[1] - 80}
        textAnchor="middle"
        fontSize="210"
        fontWeight="700"
        style={{ paintOrder: "stroke", stroke: "#fff", strokeWidth: 45 }}
      >
        <tspan>{room.name}</tspan>
        <tspan
          x={label[0]}
          dy="250"
          fontSize="150"
          fontWeight="400"
          fill="#64748b"
        >ca. {Number(room.area_m2).toFixed(1)} mÂ²</tspan>
      </text>
      {showHandles && !overrideFloor && room.polygon.map((point: Point, index: number) => { const selected = marqueeSelection.some((sel) => sameSelection(sel, { type: "room", id: room.id, point: index })); return <circle key={index} cx={point[0]} cy={point[1]} r={selected ? 125 : 95} fill="#16a34a" stroke={selected ? "#f59e0b" : "#fff"} strokeWidth={selected ? 55 : 35} onPointerDown={(event) => begin(event, { type: "room", id: room.id, point: index })} />; })}
    </g>;
    })}
      </>;
    })()}
    {floor.walls.map((wall: any) => <g key={wall.id}>
      <line x1={wall.start[0]} y1={wall.start[1]} x2={wall.end[0]} y2={wall.end[1]} stroke="#1c1917" strokeWidth={wall.thickness} strokeLinecap="square" />
      {showHandles && !overrideFloor && [wall.start, wall.end].map((point: Point, index: number) => { const selected = marqueeSelection.some((sel) => sameSelection(sel, { type: "wall", id: wall.id, point: index as 0 | 1 })); const size = selected ? 240 : 180; return <rect key={index} x={point[0] - size / 2} y={point[1] - size / 2} width={size} height={size} fill="#2563eb" stroke={selected ? "#f59e0b" : "#fff"} strokeWidth={selected ? 50 : 30} onPointerDown={(event) => begin(event, { type: "wall", id: wall.id, point: index as 0 | 1 })} />; })}
    </g>)}
    {floor.openings.map((opening: any) => {
      const wall = floor.walls.find((candidate: any) => candidate.id === opening.wall_id);
      if (!wall) return null;
      const point = openingPoint(opening, wall);
      const [first, second] = openingEndpoints(opening, wall);
      return <g key={opening.id}>
        <line x1={first[0]} y1={first[1]} x2={second[0]} y2={second[1]} stroke="#fff" strokeWidth={wall.thickness + 55} />
        {opening.opening_type === "window" && <line x1={first[0]} y1={first[1]} x2={second[0]} y2={second[1]} stroke="#12aee2" strokeWidth="48" />}
        {opening.opening_type === "passage" && <line x1={first[0]} y1={first[1]} x2={second[0]} y2={second[1]} stroke={FLOORPLAN_RULES.doors.colours.openPassage} strokeWidth="42" />}
        {opening.opening_type === "door" && <line x1={first[0]} y1={first[1]} x2={second[0]} y2={second[1]} stroke={doorColour(opening)} strokeWidth="72" strokeLinecap="square" />}
        {showHandles && !overrideFloor && <circle cx={point[0]} cy={point[1]} r="105" fill={opening.opening_type === "window" ? "#06b6d4" : "#f97316"} stroke="#fff" strokeWidth="35" onPointerDown={(event) => begin(event, { type: "opening", id: opening.id })} />}
      </g>;
    })}
    {(() => {
      // Im Moebel-Embed (overrideFloor) kommt die Treppe aus der ZEICHNUNG
      // (geometry_only -> annotation_stair_core), im Korrektur-Editor aus dem
      // Dokument. Vorher stand hier IMMER document.shared_stair_core -- die
      // generierte Treppe des Korrektur-Kandidaten mitten in einer sonst
      // zeichnungstreuen Ansicht (onehalfstorey_029, 2026-08-22).
      const stairShown = overrideFloor
        ? (overrideFloor.stair
            ? { polygon: overrideFloor.stair.polygon, path: overrideFloor.stair.path }
            : null)
        : (document.shared_stair_core?.polygon
            ? { polygon: document.shared_stair_core.polygon,
                path: reviewStairPath(document.shared_stair_core) }
            : null);
      if (!stairShown?.polygon?.length) return null;
      const arrowPath = (stairShown.path && stairShown.path.length >= 2)
        ? [stairShown.path[0], stairShown.path[stairShown.path.length - 1]]
        : reviewStairPath({ polygon: stairShown.polygon });
      return <g>
      <polygon points={stairShown.polygon.map((point: Point) => point.join(",")).join(" ")} fill="#fafaf9" fillOpacity=".9" stroke="#57534e" strokeWidth="100" />
      {(stairShown.path || arrowPath).length >= 2 && (stairShown.path || arrowPath).slice(0, -1).map((p: Point, i: number) => {
        const q = (stairShown.path || arrowPath)[i + 1];
        return <line key={i} x1={p[0]} y1={p[1]} x2={q[0]} y2={q[1]} stroke="#1d5b4a" strokeWidth="45" />;
      })}
      <polygon points={stairArrow(arrowPath)} fill="#1d5b4a" />
      <text
        x={(polygonBox(stairShown.polygon).minX + polygonBox(stairShown.polygon).maxX) / 2}
        y={(polygonBox(stairShown.polygon).minY + polygonBox(stairShown.polygon).maxY) / 2}
        textAnchor="middle"
        fontSize="155"
        fontWeight="700"
        fill="#1d5b4a"
        style={{ paintOrder: "stroke", stroke: "#fff", strokeWidth: 38 }}
      >TREPPE â†‘</text>
      {showHandles && !overrideFloor && document.shared_stair_core?.polygon?.map((point: Point, index: number) => { const selected = marqueeSelection.some((sel) => sameSelection(sel, { type: "stair", point: index })); return <circle key={index} cx={point[0]} cy={point[1]} r={selected ? 130 : 100} fill="#7c3aed" stroke={selected ? "#f59e0b" : "#fff"} strokeWidth={selected ? 55 : 35} onPointerDown={(event) => begin(event, { type: "stair", point: index })} />; })}
    </g>;
    })()}
    {einrichtenAktiv && einrichtEcken.length > 0 && <g style={{ pointerEvents: "none" }}>
      <polyline points={einrichtEcken.map((p: Point) => p.join(",")).join(" ")}
        fill="none" stroke="#b45309" strokeWidth={60} strokeDasharray="220 140" />
      {einrichtEcken.map((p: Point, i: number) => <circle key={i} cx={p[0]} cy={p[1]} r={110}
        fill="#b45309" stroke="#fff" strokeWidth={35} />)}
    </g>}
    {einrichtenAktiv && (einrichtVorschau || einrichtBereich?.polygon) && <polygon
      points={(einrichtVorschau || einrichtBereich.polygon).map((p: Point) => p.join(",")).join(" ")}
      fill="rgba(217,119,6,0.10)" stroke="#b45309" strokeWidth={60} strokeDasharray="220 140"
      style={{ pointerEvents: "none" }} />}
    <CorrectionFurnitureLayer
      document={furnitureDocument}
      selectedId={selectedFurnitureId}
      selectedIds={moebelAuswahl}
      draft={furnitureDraft}
      draftKey={activeSymbolKey}
      onRectCornerGrab={(event: React.PointerEvent, item: any, corner: number) => {
        onFurnitureSelect(item.id);
        rectCorner.current = { id: item.id, points: item.points_mm, corner };
      }}
      selectedPoints={punktAuswahl}
      onPathMenu={(event: React.MouseEvent, item: any, punkt: number | null) => {
        onFurnitureSelect(item.id);
        // Ein Rechtsklick raeumt die Auswahl NICHT ab. Rainer, 2026-08-28:
        // "the second point gets deselected when i right click" -- er rief
        // dieselbe Regel wie der Linksklick, und die ersetzt ohne Shift die
        // Auswahl durch den einen Punkt.
        if (punkt !== null) onPunktRechtsklick(punkt);
        onPunktMenue({ x: event.clientX, y: event.clientY, id: item.id, punkt });
      }}
      onStampMenu={onStampMenu}
      onPathPointGrab={(event: React.PointerEvent, item: any, punkt: number) => {
        onFurnitureSelect(item.id);
        onPunktWaehlen(punkt, event.shiftKey);
        pathPointDrag.current = { id: item.id, punkt };
      }}
      onResizeGrab={(event: React.PointerEvent, item: any) => {
        onFurnitureSelect(item.id);
        furnitureResize.current = { id: item.id, centre: item.position_mm, rotationDeg: item.rotation_deg };
      }}
      onGrab={(event: React.PointerEvent, item: any) => {
        event.stopPropagation();
        // Strg/Shift+Klick: nur in die Gruppe nehmen oder herausnehmen.
        if (event.ctrlKey || event.metaKey || event.shiftKey) {
          onFurnitureSelect(item.id, true);
          return;
        }
        // Griff an ein Mitglied einer Gruppe: die ganze Gruppe zieht.
        if (moebelAuswahl.length > 1 && moebelAuswahl.includes(item.id)) {
          const originale = Object.fromEntries((furnitureDocument?.symbols || [])
            .filter((x: any) => moebelAuswahl.includes(x.id)).map((x: any) => [x.id, x]));
          gruppenZug.current = { start: coordinate(event), originale, erster: true };
          return;
        }
        onFurnitureSelect(item.id);
        if (!item.position_mm) {
          drawnDrag.current = { id: item.id, last: coordinate(event) };
          return;
        }
        const [x, y] = coordinate(event);
        furnitureDrag.current = { id: item.id, dx: x - item.position_mm[0], dy: y - item.position_mm[1] };
      }}
    />
  </svg>;
}

type CatalogSearchResult = {
  project_id: string;
  house_type: string;
  habitable_floor_count: number;
  has_basement: boolean;
  quality_status: string;
  approval_status: string;
  usage_scope: string;
  program_tags: string[];
  room_counts: Record<string, number>;
};

const HOUSE_TYPES = ["bungalow", "onehalfstorey", "twostorey", "twostorey_cellar", "other"];
const CATALOG_TAGS = ["bedrooms", "bathroom", "child_rooms", "office", "guest_wc", "utility_room", "dining", "living", "kitchen", "balcony", "garage", "carport", "dressing", "guest_room", "hobby_room", "pantry", "roof_terrace", "storage"];

const DEMO_PRESETS = [
  { id: "onehalfstorey-office", label: "1,5 Geschosse · Homeoffice", houseType: "onehalfstorey", tags: ["office", "guest_wc", "utility_room"] },
  { id: "bungalow-family", label: "Bungalow · Homeoffice + Kinderzimmer", houseType: "bungalow", tags: ["office", "guest_wc", "child_rooms"] },
  { id: "twostorey-garage", label: "Zweigeschosser · Garage", houseType: "twostorey", tags: ["garage"] },
] as const;

async function fetchCatalogSearch(houseType: string, tags: string[]): Promise<{ matched_count: number; results: CatalogSearchResult[] }> {
  const query = new URLSearchParams({ limit: "60" });
  if (houseType) query.set("houseType", houseType);
  if (tags.length) query.set("requiredTags", tags.join(","));
  const response = await fetch(`/api/floorplan-workbench/catalog-search?${query.toString()}`, { cache: "no-store" });
  const body = await response.json();
  if (!response.ok) throw new Error(body.error || "Catalogue search failed.");
  return body;
}

async function fetchReferenceCandidate(reference?: string, transform = "identity") {
  const query = new URLSearchParams({ transform });
  if (reference) query.set("reference", reference);
  const suffix = `?${query.toString()}`;
  const response = await fetch(`/api/floorplan-workbench/generate${suffix}`, { cache: "no-store" });
  const proof = await response.json();
  if (!response.ok) throw new Error(proof.error || "Reference generation failed.");
  const revisionsResponse = await fetch(
    `/api/floorplan-workbench/corrections?reference=${encodeURIComponent(proof.reference_layout_id)}`,
    { cache: "no-store" },
  );
  const revisions = await revisionsResponse.json();
  if (!revisionsResponse.ok) throw new Error(revisions.error || "Revision loading failed.");
  return { proof, revisions };
}


function correctionSourceFromProof(proof: any) {
  if (!proof.candidate) throw new Error("Canonical candidate missing.");
  return structuredClone(proof.candidate);
}

/**
 * Die Vorlage hinter dem Grundriss -- unter BEIDEN Namen gesucht.
 *
 * Rainer, 2026-10-08, an bungalow_040_25: "why cant i see my background for
 * tracing on the furniture part anymore?"
 *
 * Der Editor fragte stur `<geschoss>_original_preview.png` an. 50 der 108
 * Projekte legen die Vorlage ohne Geschoss-Praefix ab, schlicht als
 * `original_preview.png` -- dort kam 404 zurueck. Ein SVG <image> mit totem
 * href rendert einfach nichts: kein Bild, keine Meldung, keine Spur. Die
 * uebrigen 58 Projekte haben den Praefix und liefen immer, deshalb fiel es
 * lange nicht auf.
 *
 * Der Praefix-Name hat Vorrang (bei mehreren Geschossen ist er der einzig
 * richtige); erst wenn er nicht laedt, kommt der praefixlose dran. Umbenannt
 * wird nichts -- die 58 funktionierenden Projekte bleiben unberuehrt.
 *
 * Eigene Komponente statt onError am <image>: der alte Kommentar hier warnte
 * zu Recht davor, im Fehlerfall `style.display` am DOM-Knoten zu setzen --
 * React verwendet denselben Knoten weiter und ein frueher Fehlschlag blieb
 * fuer immer sichtbar. Hier liegt der Zustand in React, und der `key` aus
 * projectId+floor setzt ihn beim Hauswechsel von selbst zurueck.
 */
function ReferenzBild({ projectId, floorName, x, y, width, height }: {
  projectId: string; floorName: string;
  x: number; y: number; width: number; height: number;
}) {
  const namen = [`${floorName}_original_preview.png`, "original_preview.png"];
  const [versuch, setVersuch] = useState(0);
  if (versuch >= namen.length) return null;
  return <image
    href={`http://127.0.0.1:8765/projects/${encodeURIComponent(projectId)}/${namen[versuch]}`}
    x={x} y={y} width={width} height={height}
    // Volle Deckkraft: die Raumflaeche darueber multipliziert, statt zu
    // ueberblenden -- ein schon aufgehelltes Bild wuerde davon kaum getoent.
    opacity={1}
    preserveAspectRatio="none"
    style={{ pointerEvents: "none" }}
    onError={() => setVersuch((n) => n + 1)}
  />;
}


export default function FloorplanWorkbenchPage() {
  const [history, setHistory] = useState<any>(null);
  const [floorIndex, setFloorIndex] = useState(0);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [grid, setGrid] = useState<number>(CORRECTION_DEFAULTS.editSnapMm);
  const [showHandles, setShowHandles] = useState(false);
  const [activeSymbolKey, setActiveSymbolKey] = useState<string | null>(null);
  // MOEBEL-BEREICH-EINRICHTEN-001: Modus, markierter Bereich, Raumtyp.
  const [einrichtenAktiv, setEinrichtenAktiv] = useState(false);
  const [einrichtBereich, setEinrichtBereich] = useState<{ polygon: Point[]; raumName: string | null } | null>(null);
  const [einrichtRaumtyp, setEinrichtRaumtyp] = useState<string | null>(null);
  const [selectedFurnitureId, setSelectedFurnitureId] = useState<string | null>(null);
  // Weitere gewaehlte Moebel neben dem ersten (Strg/Shift+Klick). Die Gruppe
  // ist `moebelAuswahl` = das erste plus diese.
  const [moebelGruppe, setMoebelGruppe] = useState<string[]>([]);
  const moebelAuswahl = selectedFurnitureId
    ? [selectedFurnitureId, ...moebelGruppe.filter((id) => id !== selectedFurnitureId)]
    : [];
  // Gewaehlte Punktindizes am gerade gewaehlten gezeichneten Lauf.
  const [punktAuswahl, setPunktAuswahl] = useState<number[]>([]);
  // Rechtsklick am gezeichneten Lauf: ausrichten, und am einzelnen Punkt
  // zusaetzlich loeschen (Rainer, 2026-08-28: "right click delete one point?
  // Because when i doubleclick to end the creation many times there are 2
  // points created at the end").
  const [punktMenue, setPunktMenue] = useState<
    { x: number; y: number; id: string; punkt: number | null } | null>(null);
  // Rechtsklick auf ein gesetztes Symbol: bisher nur fuer den begehbaren
  // Glasschrank (Fluegelzahl, GLAS-SCHIEBETUER-001).
  const [symbolMenue, setSymbolMenue] = useState<{ x: number; y: number; id: string } | null>(null);
  const [furnitureRoomFilter, setFurnitureRoomFilter] = useState("");
  // One plan at a time in the same place: two stacked plans meant scrolling
  // between them to do one job.
  // Die Hausakte laedt diese Seite als Moebel-Schritt im iframe. Dort ist alles
  // ausser Plan und Palette Ballast -- Review-Kopf, Referenzsuche,
  // Geometriewerkzeuge, Rechtehinweise, 3D. Codex, 2026-08-20: "Diese Ansicht
  // rendert ausschliesslich: Geschossauswahl, Plan, Moebelpalette, Speichern,
  // gut sichtbares Weiter zu Bauen."
  const [planView, setPlanView] = useState<"geometry" | "furniture">("geometry");
  const [hintergrundAn, setHintergrundAn] = useState(true);
  // Zoom im Grundriss. null heisst "alles zeigen". Rainer, 2026-08-31:
  // "can we add a zoom to the furniture setting? it would be easier to
  // place the furniture." Ein Haus von 15 m auf 680 Bildpunkten sind rund
  // 19 mm je Punkt -- ein Wand-WC ist damit 19 Punkte breit.
  const [sicht, setSicht] = useState<{ zoom: number; cx: number; cy: number } | null>(null);
  const [embed, setEmbed] = useState(false);
  useEffect(() => {
    const modus = new URLSearchParams(window.location.search).get("mode");
    if (modus === "furniture-embed") {
      setEmbed(true);
      setPlanView("furniture");
    }
  }, []);
  const furnitureDrag = useRef<{ id: string; dx: number; dy: number } | null>(null);
  const furnitureReference = history?.source?.source_reference_id
    || history?.present?.source_reference_id || "";
  // Keyed by the CORRECTION floor id, because that is the geometry furniture
  // is now placed on and the id the corrected render plan looks it up by.
  // `groundfloor`/`upperfloor` came from the annotation-derived geometry the
  // editor no longer draws.
  const furnitureFloorId = history?.present?.floors?.[floorIndex]?.id || "";
  const furniture = useFurniture(furnitureReference, furnitureFloorId);

  // Pfeiltasten schieben die gewaehlten Punkte, Strg+Z nimmt zurueck --
  // dieselben Schrittweiten wie im Zeichner, damit die Hand nicht umlernt.
  useEffect(() => {
    function onKey(event: KeyboardEvent) {
      const ziel = event.target as HTMLElement | null;
      if (ziel && /input|select|textarea/i.test(ziel.tagName)) return;
      if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "z") {
        event.preventDefault();
        furniture.zurueck();
        setPunktAuswahl([]);
        return;
      }
      const richtung: Record<string, [number, number]> = {
        ArrowLeft: [-1, 0], ArrowRight: [1, 0], ArrowUp: [0, -1], ArrowDown: [0, 1],
      };
      if (event.key === "Escape" && moebelGruppe.length) { setMoebelGruppe([]); return; }
      const schritt = richtung[event.key];
      if (schritt && moebelAuswahl.length > 1) {
        event.preventDefault();
        const mm = punktSchrittMm(event);
        const originale = Object.fromEntries((furniture.document.symbols || [])
          .filter((x: any) => moebelAuswahl.includes(x.id)).map((x: any) => [x.id, x]));
        furniture.moveGroup(originale, [schritt[0] * mm, schritt[1] * mm], true);
        return;
      }
      if (!schritt || !selectedFurnitureId) return;
      const item = (furniture.document.symbols || []).find((x: any) => x.id === selectedFurnitureId);
      if (!item) return;
      const mm = punktSchrittMm(event);
      if (item.points_mm) {
        // Drawn symbols (Kuechenzeile etc.): nudging moves the SELECTED
        // points along the path, not the whole run.
        if (!punktAuswahl.length) return;
        event.preventDefault();
        furniture.setPoints(item.id,
          schiebePunkte(item.points_mm, punktAuswahl, schritt[0] * mm, schritt[1] * mm));
      } else if (item.position_mm) {
        // Stamp-placed symbols (bed, sofa, appliances, ...) have one position
        // and no sub-points to select -- selecting the item is enough.
        event.preventDefault();
        furniture.move(item.id,
          [item.position_mm[0] + schritt[0] * mm, item.position_mm[1] + schritt[1] * mm]);
      }
    }
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [furniture, selectedFurnitureId, punktAuswahl, moebelGruppe]);
  // Die Bau-Geometrie fuer den Moebel-Schritt. null = (noch) nicht geladen;
  // dann zeichnet der Editor wie bisher den Korrektur-Kandidaten und sagt
  // das im Statustext, statt stillschweigend im falschen Haus zu moeblieren.
  const [renderGeo, setRenderGeo] = useState<any>(null);
  useEffect(() => {
    // Im Moebel-Fenster (Embed) IMMER laden, nicht nur in der Moebel-Ansicht:
    // sonst zeigt der Umschalter auf "Geometrie" den Korrektur-Kandidaten,
    // also ein anderes Koordinatensystem -- Waende springen, Moebel stehen
    // daneben (Rainer, 2026-08-23: "if i switch off moebel to edit the
    // geometry then the walls get totally displaced and all of the furniture").
    if ((!embed && planView !== "furniture") || !furnitureReference) return;
    let stehengeblieben = false;
    fetch("/api/floorplan-workbench/corrections", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: "render_geometry", reference: furnitureReference }),
    }).then((r) => r.json()).then((d) => {
      if (!stehengeblieben) setRenderGeo(d?.ok === false ? { fehler: d.error } : d.geometry || null);
    }).catch((e) => { if (!stehengeblieben) setRenderGeo({ fehler: String(e) }); });
    return () => { stehengeblieben = true; };
  }, [planView, furnitureReference, embed]);
  // Rainer, 2026-09-18, twostorey_047: 21 of 21 placed items found reflected
  // into the wrong room -- the save API always re-stamped the CURRENT room
  // geometry's identity, even when this tab had loaded an OLDER one, so a
  // stale save looked freshly valid. `furniture.save()` needs to know which
  // identity THIS TAB is actually showing right now, not the one the API
  // recomputes at save time -- handed through a ref (see furniture.tsx)
  // rather than a save()-time argument, since onSave() is called with no
  // arguments several components away in the toolbar.
  useEffect(() => {
    furniture.setDisplayedGeometryIdentity(renderGeo?.floors?.[floorIndex]?.geometry_identity);
  }, [furniture, renderGeo, floorIndex]);
  // MOEBEL-EIN-SPEICHERN-001: "Speichern" schreibt alle Geschosse und braucht
  // dafuer ihre Namen und angezeigten Kennungen. Dieselbe floor-N-Rueckfallebene
  // wie unten bei leereRaeumeAllerGeschosse.
  const setAlleGeschosse = furniture.setAlleGeschosse;
  const korrekturGeschosse = history?.present?.floors;
  useEffect(() => {
    setAlleGeschosse(((renderGeo?.floors || []) as any[]).map((geschoss, i) => {
      const roh = geschoss?.floor_level || korrekturGeschosse?.[i]?.name || "";
      return {
        floorId: korrekturGeschosse?.[i]?.id || `floor-${i}`,
        identitaet: geschoss?.geometry_identity,
        name: ({ groundfloor: "Erdgeschoss", upperfloor: "Obergeschoss", basement: "Kellergeschoss", staffelgeschoss: "Staffelgeschoss", attic: "Dachgeschoss" } as Record<string, string>)[roh]
          || roh || `Geschoss ${i + 1}`,
      };
    }));
  }, [setAlleGeschosse, renderGeo, korrekturGeschosse]);
  // Geschoss-Zuordnung ueber die REIHENFOLGE: beide Seiten sortieren die
  // Geschosse gleich (floor-0 <-> erstes Level).
  const renderFloor = (() => {
    const fl = renderGeo?.floors?.[floorIndex];
    // EINE Geometrie im ganzen Moebel-Fenster: die der Zeichnung, aus der
    // auch gebaut wird. Der Umschalter blendet nur die Moebel ein und aus.
    if (!fl || (!embed && planView !== "furniture")) return null;
    return {
      id: furnitureFloorId,
      name: fl.floor_level,
      rooms: (fl.rooms || []).map((r: any) => ({
        id: r.id, name: r.name, kind: r.kind, polygon: r.polygon_mm, area_m2: r.area_m2,
      })),
      walls: fl.walls || [], openings: fl.openings || [],
      // Die GEZEICHNETE Treppe (annotation_stair_core), nicht die generierte
      // aus dem Korrektur-Dokument -- siehe geometry_only().
      stair: fl.stair || null,
      // Echte Frame/RegisteredFrame-Registrierung des Referenzfotos, aus
      // geometry_only() -- keine Bounding-Box-Naeherung mehr (Rainer,
      // 2026-09-17: "scale is off but it is all from the same data").
      imageCorners: fl.image_corners_mm || null,
    };
  })();
  // Codex-Review, 2026-09-18 (Koordinatenraeume): waehrend renderGeo noch
  // laedt oder fehlgeschlagen ist, zeichnet die Flaeche wie gehabt den
  // Korrektur-Kandidaten (siehe Fallback bei roomNames/rooms unten) -- ein
  // ANDERES Koordinatensystem als das, worin Moebel gespeichert werden. Ohne
  // diese Sperre blieb "Speichern" in genau diesem Fenster anklickbar und
  // haette Moebel unter dem Korrektur-Layout platziert, aber als Render-mm
  // abgespeichert. Die Stale-Save-Pruefung oben greift hier NICHT, weil es
  // noch gar keine geladene geometry_identity gibt, mit der sie vergleichen
  // koennte.
  const moebelGeometrieFehltNoch = (embed || planView === "furniture")
    && !!furnitureReference && !renderGeo?.floors?.[floorIndex];
  const [validation, setValidation] = useState<any>(null);
  const [preview, setPreview] = useState<any>(null);
  const [blenderPreview, setBlenderPreview] = useState<any>(null);
  const [proof, setProof] = useState<any>(null);
  const [reviewNote, setReviewNote] = useState("");
  const [comparedTo, setComparedTo] = useState<string | null>(null);
  const [massingView, setMassingView] = useState("garden");
  const [message, setMessage] = useState("Loading annotated referenceâ€¦");
  const [messageKind, setMessageKind] = useState<"info" | "success" | "error" | "warning">("info");
  const [messageAt, setMessageAt] = useState(0);
  const [searchHouseType, setSearchHouseType] = useState("");
  const [searchTags, setSearchTags] = useState<string[]>([]);
  const [searchResults, setSearchResults] = useState<CatalogSearchResult[] | null>(null);
  const [searchMatchedCount, setSearchMatchedCount] = useState<number | null>(null);
  const [searchMessage, setSearchMessage] = useState("");
  const [activePreset, setActivePreset] = useState<string | null>(null);

  function notify(text: string, kind: "info" | "success" | "error" | "warning" = "info") {
    setMessage(text);
    setMessageKind(kind);
    setMessageAt(Date.now());
  }

  useEffect(() => {
    const search = new URLSearchParams(window.location.search);
    const requestedReference = search.get("reference") || undefined;
    const requestedTransform = search.get("transform") || "identity";
    if (search.get("mode") === "furniture-embed" && requestedReference) {
      let cancelled = false;
      fetch("/api/floorplan-workbench/corrections", {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "render_geometry", reference: requestedReference }),
      }).then(async response => {
        const body = await response.json();
        if (!response.ok || !body.ok) throw new Error(body.error || "Furniture geometry unavailable.");
        const source = furnitureViewDocument(requestedReference, body.geometry);
        if (cancelled) return;
        setRenderGeo(body.geometry);
        setHistory(createEditorHistory(source));
        notify("Live annotation loaded for furniture placement.", "info");
      }).catch(error => { if (!cancelled) notify(String(error), "error"); });
      return () => { cancelled = true; };
    }
    fetchReferenceCandidate(requestedReference, requestedTransform).then(({ proof: loadedProof, revisions }) => {
      const source = correctionSourceFromProof(loadedProof);
      const initial = revisions.latest?.schema === source.schema ? revisions.latest : source;
      const editorHistory = createEditorHistory(source);
      editorHistory.present = structuredClone(initial);
      setHistory(editorHistory);
      setProof(loadedProof);
      notify(revisions.latest ? `Loaded ${revisions.revisions.at(-1)}` : "Source annotation loaded. No revision saved yet.", "info");
    }).catch((error) => notify(error instanceof Error ? error.message : String(error), "error"));
  }, []);

  async function selectReference(reference: string) {
    try {
      notify(`Loading ${reference}â€¦`, "info");
      const previous = proof?.reference_layout_id || null;
      const { proof: loadedProof, revisions } = await fetchReferenceCandidate(reference);
      const source = correctionSourceFromProof(loadedProof);
      const initial = revisions.latest?.schema === source.schema ? revisions.latest : source;
      const editorHistory = createEditorHistory(source);
      editorHistory.present = structuredClone(initial);
      setComparedTo(previous);
      setHistory(editorHistory);
      setProof(loadedProof);
      window.history.replaceState(null, "", `/floorplan-workbench?reference=${encodeURIComponent(reference)}`);
      setFloorIndex(0);
      setSelection(null);
      setValidation(null);
      setPreview(null);
      notify(revisions.latest ? `Loaded ${revisions.revisions.at(-1)}` : `${reference}: quality-passed source loaded.`, "info");
    } catch (error) {
      notify(error instanceof Error ? error.message : String(error), "error");
    }
  }

  async function runSearch(houseType: string, tags: string[]) {
    try {
      setSearchMessage("Searching catalogueâ€¦");
      const { matched_count, results } = await fetchCatalogSearch(houseType, tags);
      setSearchResults(results);
      setSearchMatchedCount(matched_count);
      setSearchMessage(matched_count
        ? `${matched_count} match${matched_count === 1 ? "" : "es"} in the catalogue${results.length < matched_count ? ` (showing ${results.length})` : ""}.`
        : "No catalogue matches for this combination.");
      return results;
    } catch (error) {
      setSearchMessage(error instanceof Error ? error.message : String(error));
      return [];
    }
  }

  function toggleSearchTag(tag: string) {
    setActivePreset(null);
    setSearchTags((current) => current.includes(tag) ? current.filter((item) => item !== tag) : [...current, tag]);
  }

  async function applyPreset(preset: (typeof DEMO_PRESETS)[number]) {
    setActivePreset(preset.id);
    setSearchHouseType(preset.houseType);
    setSearchTags([...preset.tags]);
    const results = await runSearch(preset.houseType, [...preset.tags]);
    if (results.length) await selectReference(results[0].project_id);
  }

  const document = history?.present;
  // Der Kasten, auf den sich der Zoom bezieht -- derselbe, den der Editor
  // zeichnet. `documentBounds` ist rein rechnend, also kein zweiter Weg.
  // Beim ersten Rendern gibt es noch kein Dokument -- `documentBounds` liest
  // dann `.floors` von undefined und die ganze Seite faellt mit 500 aus.
  const zoomKasten = useMemo(
    () => (document ? documentBounds(document, floorIndex)
                    : { minX: 0, minY: 0, width: 1, height: 1 }),
    [document, floorIndex]);

  function zoomStufe(richtung: number) {
    // Um die Bildmitte, wenn niemand zeigt. Das Rad zoomt um den Zeiger.
    setSicht((jetzt: { zoom: number; cx: number; cy: number } | null) => zoomUmZeiger(
      zoomKasten, jetzt,
      (jetzt?.zoom || ZOOM_MIN) * (richtung > 0 ? ZOOM_SCHRITT : 1 / ZOOM_SCHRITT),
      { x: 0.5, y: 0.5 }));
  }
  const selected = useMemo(() => {
    if (!document || !selection) return null;
    const floor = document.floors[floorIndex];
    if (selection.type === "room") return { item: floor.rooms.find((room: any) => room.id === selection.id), coordinates: floor.rooms.find((room: any) => room.id === selection.id)?.polygon[selection.point] };
    if (selection.type === "wall") {
      const item = floor.walls.find((wall: any) => wall.id === selection.id);
      return { item, coordinates: item?.[selection.point ? "end" : "start"] };
    }
    if (selection.type === "opening") return { item: floor.openings.find((opening: any) => opening.id === selection.id) };
    return { item: document.shared_stair_core, coordinates: document.shared_stair_core.polygon[selection.point] };
  }, [document, selection, floorIndex]);

  function commitMutation(mutator: (copy: any) => void) {
    const next = structuredClone(history.present);
    mutator(next);
    setHistory(commitEditorHistory(history, next));
  }
  function setCoordinate(axis: 0 | 1, value: number) {
    if (!selection) return;
    commitMutation((next) => {
      const floor = next.floors[floorIndex];
      if (selection.type === "room") floor.rooms.find((room: any) => room.id === selection.id).polygon[selection.point][axis] = snapCoordinate(value, grid);
      if (selection.type === "wall") floor.walls.find((wall: any) => wall.id === selection.id)[selection.point ? "end" : "start"][axis] = snapCoordinate(value, grid);
      if (selection.type === "stair") next.shared_stair_core.polygon[selection.point][axis] = snapCoordinate(value, grid);
    });
  }
  async function action(actionName: string, options: Record<string, unknown> = {}) {
    const response = await fetch("/api/floorplan-workbench/corrections", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ action: actionName, document: history.present, ...options }),
    });
    const responseText = await response.text();
    let body: any;
    try {
      body = responseText ? JSON.parse(responseText) : { error: `Workbench returned an empty response (HTTP ${response.status}).` };
    } catch {
      body = { error: `Workbench returned an invalid response (HTTP ${response.status}).` };
    }
    setValidation(body.validation || null);
    if (body.document) setHistory((current: any) => ({ ...current, present: body.document }));
    if (body.preview) setPreview(body.preview);
    if (body.png_base64) setBlenderPreview(body);
    if (body.ok && body.document) {
      setHistory((current: any) => ({
        source: current.source,
        past: [],
        present: body.document,
        future: [],
      }));
    }
    if (actionName === "export" && body.ok) {
      const imported = body.import_result?.summary?.imported || [];
      // Match by reference only, not the exact revision folder name: the
      // import is idempotent by geometry_hash, so if this plan was exported
      // before with identical geometry, the batch importer can legitimately
      // report back an earlier revision number for the same plan_id.
      const thisOne = imported.find((item: any) => item.reference === history.present?.source_reference_id);
      if (body.import_result?.ok && thisOne) notify(`Exported successfully — live in the catalogue as ${thisOne.plan_id}.`, "success");
      else if (body.import_result?.ok) notify(`Exported. Import ran (${imported.length} plan${imported.length === 1 ? "" : "s"} in catalogue) but didn't report this one — check catalog.generated.mjs.`, "warning");
      else notify(`Exported to ${body.export_directory}, but the automatic import failed: ${body.import_result?.error || "unknown error"}. Run the import script manually.`, "error");
    } else if (actionName === "validate") {
      // The validate endpoint has no top-level "ok" flag — success/failure
      // is expressed entirely through validation.valid.
      notify(
        body.validation?.valid ? "Validation passed — 0 errors." : `Validation failed — ${body.validation?.errors?.length ?? 0} error(s) below.`,
        body.validation?.valid ? "success" : "error",
      );
    } else if (!body.ok) {
      notify(body.error || `${actionName} failed.`, "error");
    } else if (actionName === "approve") {
      notify(`Approved locally.`, "success");
    } else if (actionName === "reject") {
      notify(`Rejected and saved locally.`, "warning");
    } else if (actionName === "save_draft") {
      notify(`Draft saved.`, "success");
    } else {
      notify(body.export_directory || body.path || `${actionName} complete`, "info");
    }
  }

  async function reviewCandidate(decision: "better" | "worse" | "reject") {
    const response = await fetch("/api/floorplan-workbench/reviews", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        source_reference_id: document.source_reference_id,
        compared_to: comparedTo,
        decision,
        note: reviewNote,
        geometry_hash: document.geometry_hash,
      }),
    });
    const responseText = await response.text();
    let body: any;
    try {
      body = responseText ? JSON.parse(responseText) : { error: `Workbench returned an empty response (HTTP ${response.status}).` };
    } catch {
      body = { error: `Workbench returned an invalid response (HTTP ${response.status}).` };
    }
    notify(body.error || `${decision}: ${document.source_reference_id} saved locally.`, body.error ? "error" : "success");
    if (response.ok) {
      setReviewNote("");
      const candidateList = proof?.reference_candidates || [];
      const index = proof?.reference_candidate?.index ?? 0;
      if (candidateList.length > 1) {
        await selectReference(candidateList[(index + 1) % candidateList.length].project_id);
      }
    }
  }

  if (!document) return <main className="p-8">{message}</main>;
  const candidates = proof?.reference_candidates || [];
  const candidateIndex = proof?.reference_candidate?.index ?? 0;
  const candidate = proof?.reference_candidate;
  const bannerStyles: Record<string, string> = {
    success: "bg-emerald-600 text-white",
    error: "bg-red-600 text-white",
    warning: "bg-amber-500 text-black",
    info: "bg-slate-800 text-white",
  };
  const bannerIcon: Record<string, string> = { success: "✅", error: "❌", warning: "⚠️", info: "ℹ️" };
  const EMBED_CSS = `
    .wb-embed { height:100dvh; overflow:hidden; display:flex; flex-direction:column;
                padding:10px 12px; margin:0; max-width:none; }
    /* Alles ausser dem Plan-Abschnitt bleibt draussen -- im Moebel-Schritt ist
       nichts davon gemeint, und jeder Knopf mehr ist ein Umweg.
       AUSSER dem Speichern. Rainer, 2026-08-30, zum dritten Mal derselbe
       Abbruch: "die RAEUME dieses Geschosses wurden umgezeichnet, seit diese
       Moebel gesetzt wurden". Der Handgriff lautet "einmal speichern" -- und
       genau der Knopf fiel hier mit heraus. Im Browser nachgemessen: 52
       sichtbare Bedienelemente, alle aus der Palette, "Save draft" nicht
       darunter. Der Schritt liess sich also gar nicht abschliessen. */
    .wb-embed > *:not(.wb-plan):not(.wb-aktionen) { display:none !important; }
    .wb-embed .wb-plan { flex:1 1 auto; min-height:0; display:grid;
                         grid-template-columns:1fr 330px; gap:12px; }
    /* Rainer, 2026-09-19: "the doulbe scrollbar is still in the moebel part"
       -- beide Spalten bekamen unterschiedslos overflow:auto. Die linke
       Spalte ist die Zeichenflaeche mit ihrem EIGENEN Zoom/Pan (sicht,
       zoomStufe oben) -- ein zusaetzlicher Seiten-Scrollbalken daneben ist
       nur die zweite, ueberfluessige Bedienung fuer dieselbe Sache. Nur die
       RECHTE Spalte (die Moebelpalette, eine tatsaechlich lange Liste) soll
       fuer sich scrollen. min-height:0 bleibt auf beiden -- das ist die
       CSS-Grid-Untergrenze, die das Schrumpfen unter die Inhaltsgroesse
       ueberhaupt erst erlaubt, unabhaengig vom Scroll-Verhalten. */
    .wb-embed .wb-plan > :first-child { min-height:0; overflow:hidden; }
    .wb-embed .wb-plan > :last-child { min-height:0; overflow:auto; }
    /* Nur Speichern. Validate, Approve, Reject und Export gehoeren in die
       volle Ansicht -- hier waere jeder davon ein Umweg oder ein Unfall. */
    .wb-embed .wb-aktionen { flex:0 0 auto; margin-top:10px; padding:10px 14px;
                             border-radius:14px; }
    .wb-embed .wb-aktionen button:not(.wb-speichern) { display:none !important; }
  `;

  return <main className={embed ? "wb-embed" : "mx-auto max-w-[1500px] space-y-6 p-5"}>
    {embed && <style dangerouslySetInnerHTML={{ __html: EMBED_CSS }} />}
    {message && <div
      key={messageAt}
      className={`sticky top-2 z-50 flex items-start gap-3 rounded-2xl px-5 py-4 text-base font-semibold shadow-lg ring-2 ring-black/10 ${bannerStyles[messageKind]}`}
    >
      <span className="text-xl leading-none">{bannerIcon[messageKind]}</span>
      <span className="break-words">{message}</span>
    </div>}
    <header className="rounded-3xl bg-amber-100 p-6 ring-2 ring-amber-600">
      <p className="font-black tracking-widest text-amber-950">INTERNAL REVIEW â€“ NOT FOR CUSTOMER DELIVERY</p>
      <h1 className="mt-2 text-3xl font-semibold">Manual floorplan correction Â· {document.source_reference_id}</h1>
      {document.source_reference_id ? <a href={"http://127.0.0.1:8765/annotate.html?project=" + encodeURIComponent(document.source_reference_id)} target="_blank" rel="noreferrer" title="Annotator (eigene App auf Port 8765) - dasselbe Projekt" className="ml-3 rounded-full bg-stone-200 px-3 py-1 align-middle text-xs font-semibold text-stone-800 hover:bg-stone-300">Im Annotator &#8599;</a> : null}
      <p className="mt-2">The same cleaned millimetre geometry drives the editor, JPEG and 3D guide. Source annotation remains read-only.</p>
      <p className="mt-1 text-sm">Geometry hash: <span className="break-all font-mono text-xs">{document.geometry_hash}</span></p>
      <p className="mt-1 text-xs">Transform: {proof?.transform || "identity"} · revision {document.revision} · approval {document.status} · Rulebook: {FLOORPLAN_RULEBOOK_VERSION}</p>
      <div className="mt-3 flex flex-wrap gap-2">
        <span className="rounded-full bg-violet-700 px-4 py-2 text-sm font-semibold text-white">Correction editor</span>
        <a href="/floorplan-workbench/overview" className="rounded-full bg-white px-4 py-2 text-sm font-semibold">Overview of everything produced</a>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">{["identity", "mirror_horizontal", "mirror_vertical"].map((transform) => <a key={transform} href={`/floorplan-workbench?reference=${encodeURIComponent(document.source_reference_id)}&transform=${transform}`} className={`rounded-full px-3 py-2 text-sm ${proof?.transform === transform ? "bg-violet-700 text-white" : "bg-white"}`}>{transform}</a>)}</div>
      <div className="mt-4 flex flex-wrap items-center gap-2 rounded-2xl bg-white/70 p-3 text-sm">
        <button
          disabled={candidates.length < 2}
          onClick={() => selectReference(candidates[(candidateIndex - 1 + candidates.length) % candidates.length].project_id)}
          className="rounded-full bg-slate-900 px-4 py-2 text-white disabled:opacity-40"
        >â† Previous reference</button>
        <strong>{candidateIndex + 1} / {candidates.length}</strong>
        <button
          disabled={candidates.length < 2}
          onClick={() => selectReference(candidates[(candidateIndex + 1) % candidates.length].project_id)}
          className="rounded-full bg-slate-900 px-4 py-2 text-white disabled:opacity-40"
        >Next reference â†’</button>
        <span className="rounded-full bg-emerald-100 px-3 py-1 font-semibold text-emerald-900">Quality: {candidate?.quality_status || "unknown"}</span>
        <span className="rounded-full bg-stone-200 px-3 py-1">Source: {candidate?.package_status}</span>
        <span className="rounded-full bg-amber-200 px-3 py-1">Rights: {candidate?.usage_scope}</span>
        {candidate?.stair_review_required && <span className="rounded-full bg-red-100 px-3 py-1 font-semibold text-red-900">Stair alignment requires human review</span>}
      </div>
      <div className="mt-3 grid gap-2 md:grid-cols-[1fr_auto_auto_auto]">
        <input value={reviewNote} onChange={(event) => setReviewNote(event.target.value)} placeholder="Why is this reference better or worse? (optional)" className="rounded-full border border-amber-400 bg-white px-4 py-2" />
        <button onClick={() => reviewCandidate("better")} className="rounded-full bg-emerald-700 px-4 py-2 font-semibold text-white">Better</button>
        <button onClick={() => reviewCandidate("worse")} className="rounded-full bg-amber-600 px-4 py-2 font-semibold text-white">Worse</button>
        <button onClick={() => reviewCandidate("reject")} className="rounded-full bg-red-700 px-4 py-2 font-semibold text-white">Reject</button>
      </div>
    </header>
    <section className="rounded-3xl bg-white p-5 shadow-sm">
      <h2 className="text-xl font-semibold">Find a matching approved reference</h2>
      <p className="mt-1 text-sm text-stone-600">Filters search the {searchMatchedCount === null ? "310-project" : `${searchMatchedCount}-of-310`} catalogue only; loading a result still goes through the same quality/rights gate as direct navigation.</p>
      <div className="mt-3 flex flex-wrap gap-2">
        {DEMO_PRESETS.map((preset) => <button
          key={preset.id}
          onClick={() => applyPreset(preset)}
          className={`rounded-full px-4 py-2 text-sm ${activePreset === preset.id ? "bg-emerald-700 text-white" : "bg-stone-200"}`}
        >{preset.label}</button>)}
      </div>
      <div className="mt-4 flex flex-wrap items-center gap-3">
        <label className="text-sm">House type
          <select
            value={searchHouseType}
            onChange={(event) => { setActivePreset(null); setSearchHouseType(event.target.value); }}
            className="ml-2 rounded border p-2"
          >
            <option value="">Any</option>
            {HOUSE_TYPES.map((type) => <option key={type} value={type}>{type}</option>)}
          </select>
        </label>
        <button onClick={() => runSearch(searchHouseType, searchTags)} className="rounded-full bg-slate-900 px-4 py-2 text-sm text-white">Search catalogue</button>
      </div>
      <div className="mt-3 flex flex-wrap gap-2">
        {CATALOG_TAGS.map((tag) => <button
          key={tag}
          onClick={() => toggleSearchTag(tag)}
          className={`rounded-full px-3 py-1 text-xs ${searchTags.includes(tag) ? "bg-blue-700 text-white" : "bg-stone-100"}`}
        >{tag}</button>)}
      </div>
      {searchMessage && <p className="mt-3 text-sm text-stone-700">{searchMessage}</p>}
      {searchResults && searchResults.length > 0 && <div className="mt-3 flex flex-wrap gap-2">
        {searchResults.slice(0, 24).map((result) => <button
          key={result.project_id}
          onClick={() => selectReference(result.project_id)}
          className={`rounded-full border px-3 py-2 text-xs ${document?.source_reference_id === result.project_id ? "border-emerald-700 bg-emerald-50" : "border-stone-300 bg-white"}`}
          title={`Matched: ${result.house_type}${result.program_tags.length ? " · " + result.program_tags.join(", ") : ""}`}
        >{result.project_id}</button>)}
      </div>}
    </section>
    <section className="wb-plan grid gap-5 xl:grid-cols-[1fr_330px]">
      <div className="space-y-3">
        <div className="flex flex-wrap gap-2">
          {document.floors.map((floor: any, index: number) => <button key={floor.id} onClick={() => { setFloorIndex(index); setSelection(null); }} className={`rounded-full px-4 py-2 ${index === floorIndex ? "bg-slate-900 text-white" : "bg-white"}`}>{floor.name}</button>)}
          {/* In der Moebel-Ansicht zeigt der Plan die Geometrie der ZEICHNUNG
              (geometry_only), die Griffe wuerden aber das Korrektur-Dokument
              verschieben -- man zog an einem Griff und nichts bewegte sich
              (Rainer, 2026-08-23: "the edit in furniture mode isn't working").
              Geometrie wird im Zeichnen-Schritt geaendert, hier nicht. */}
          <button
            onClick={() => { setShowHandles((value) => !value); setSelection(null); }}
            disabled={planView === "furniture"}
            title={planView === "furniture"
              ? "Geometrie wird im Zeichnen-Schritt geändert, nicht in der Möbel-Ansicht"
              : undefined}
            className={`rounded-full px-4 py-2 ${planView === "furniture"
              ? "bg-white text-slate-400 cursor-not-allowed"
              : showHandles ? "bg-blue-700 text-white" : "bg-white"}`}
          >{showHandles && planView !== "furniture" ? "Hide edit handles" : "Edit geometry"}</button>
          {/* Zoom. Rainer, 2026-08-31: "can we add a zoom to the furniture
              setting?" Strg+Rad zoomt um den Zeiger; die Knoepfe zoomen um
              die Bildmitte, fuer alle, die kein Rad haben. */}
          <span className="ml-2 inline-flex items-center gap-1 rounded-full border bg-white px-2 py-1">
            <button
              type="button"
              title="Verkleinern"
              disabled={!sicht}
              onClick={() => zoomStufe(-1)}
              className="px-2 text-lg leading-none disabled:opacity-30"
            >&minus;</button>
            <span className="w-12 text-center text-xs tabular-nums text-stone-600">
              {Math.round((sicht?.zoom || ZOOM_MIN) * 100)}%
            </span>
            <button
              type="button"
              title="Vergroessern (oder Strg + Mausrad)"
              disabled={(sicht?.zoom || ZOOM_MIN) >= ZOOM_MAX}
              onClick={() => zoomStufe(1)}
              className="px-2 text-lg leading-none disabled:opacity-30"
            >+</button>
            <button
              type="button"
              title="Ganzen Grundriss zeigen"
              disabled={!sicht}
              onClick={() => setSicht(null)}
              className="ml-1 rounded px-2 py-0.5 text-xs hover:bg-stone-100 disabled:opacity-30"
            >Einpassen</button>
          </span>
          <button
            type="button"
            aria-pressed={!hintergrundAn}
            onClick={() => setHintergrundAn((an) => !an)}
            className="rounded-full bg-white px-4 py-2"
          >{hintergrundAn ? "Hintergrund ausblenden" : "Hintergrund einblenden"}</button>
          <button
            onClick={() => setPlanView((view: "geometry" | "furniture") => view === "furniture" ? "geometry" : "furniture")}
            className={`rounded-full px-4 py-2 ${planView === "furniture" ? "bg-amber-700 text-white" : "bg-white"}`}
          >Möbel</button>
          <label className="ml-auto rounded-full bg-white px-4 py-2">Snap <input type="number" min="10" step="10" value={grid} onChange={(event) => setGrid(Number(event.target.value))} className="w-20 border-b text-right" /> mm</label>
        </div>
        <GeometryEditor
          zeigeHintergrund={hintergrundAn}
          sicht={sicht}
          setSicht={setSicht}
          history={history} setHistory={setHistory} floorIndex={floorIndex}
          selection={selection} setSelection={setSelection} grid={grid} showHandles={showHandles}
          furnitureDocument={furniture.document}
          overrideFloor={renderFloor}
          projectId={document.source_reference_id}
          activeSymbolKey={activeSymbolKey}
          selectedFurnitureId={selectedFurnitureId}
          onFurniturePlace={(point: [number, number]) => { if (!moebelGeometrieFehltNoch && activeSymbolKey) furniture.place(activeSymbolKey, point); }}
          onFurnitureSelect={(id: string, dazu = false) => {
            setActiveSymbolKey(null);
            if (dazu && selectedFurnitureId) {
              // Strg/Shift+Klick: in die Gruppe oder heraus.
              setPunktAuswahl([]);
              if (id === selectedFurnitureId) {
                const rest = moebelGruppe.filter((x) => x !== id);
                setSelectedFurnitureId(rest[0] || null);
                setMoebelGruppe(rest.slice(1));
              } else {
                setMoebelGruppe((alt) => alt.includes(id) ? alt.filter((x) => x !== id) : [...alt, id]);
              }
              return;
            }
            if (id !== selectedFurnitureId) setPunktAuswahl([]);
            setSelectedFurnitureId(id);
            // Ein Klick auf ein Mitglied der Gruppe laesst die Gruppe stehen
            // (damit sie sich ziehen laesst), sonst beginnt eine neue.
            if (!moebelAuswahl.includes(id)) setMoebelGruppe([]);
          }}
          moebelAuswahl={moebelAuswahl}
          onFurnitureMoveGroup={(originale: any, delta: [number, number], erster: boolean) => {
            if (!moebelGeometrieFehltNoch) furniture.moveGroup(originale, delta, erster);
          }}
          // Codex-Review, 2026-09-18: die fruehere Fassung sperrte nur den
          // Speichern-Knopf. Waehrend renderGeo noch laedt, blieb Platzieren/
          // Verschieben/Umformen aber weiter moeglich -- eine WAEHREND dieses
          // Fensters gezogene Aenderung blieb im Dokument stehen, und sobald
          // die Geometrie fertig geladen war, entsperrte sich Speichern
          // wieder und nahm die laengst (gegen die falsche/Fallback-Ansicht)
          // gezogene Aenderung klaglos mit. Jede Mutation jetzt selbst
          // gesperrt, nicht nur das Speichern.
          onFurnitureMove={(id: string, point: [number, number]) => { if (!moebelGeometrieFehltNoch) furniture.move(id, point); }}
          onFurniturePlaceDrawn={(key: string, points: [number, number][]) => { if (!moebelGeometrieFehltNoch) furniture.placeDrawn(key, points); }}
          einrichtenAktiv={einrichtenAktiv}
          einrichtBereich={einrichtBereich}
          onEinrichtBereich={(bereich: any) => {
            setEinrichtBereich(bereich);
            const typ = bereich?.raumName ? raumtypAusName(bereich.raumName) : null;
            if (typ) setEinrichtRaumtyp(typ);
          }}
          onFurnitureResize={(id: string, width: number, depth: number) => { if (!moebelGeometrieFehltNoch) furniture.resize(id, width, depth); }}
          onFurnitureSetPoints={(id: string, points: [number, number][]) => { if (!moebelGeometrieFehltNoch) furniture.setPoints(id, points); }}
          onFurnitureMoveDrawn={(id: string, delta: [number, number]) => { if (!moebelGeometrieFehltNoch) furniture.moveDrawn(id, delta); }}
          punktAuswahl={punktAuswahl}
          onPunktWaehlen={(punkt: number, dazu: boolean) => setPunktAuswahl((alt) =>
            dazu ? (alt.includes(punkt) ? alt.filter((i) => i !== punkt) : [...alt, punkt]) : [punkt])}
          onPunktRechtsklick={(punkt: number) => setPunktAuswahl((alt) =>
            alt.includes(punkt) ? alt : [punkt])}
          onPunktMenue={setPunktMenue}
          onStampMenu={(event: React.MouseEvent, item: any) => {
            if (item.symbol !== "glasschiebetuer") return;
            setSymbolMenue({ x: event.clientX, y: event.clientY, id: item.id });
          }}
        />
      </div>
      {symbolMenue && (() => {
        const item = (furniture.document.symbols || []).find((x: any) => x.id === symbolMenue.id);
        if (!item) return null;
        const jetzt = [1, 2, 3].includes(item.fluegel) ? item.fluegel : 2;
        return <>
          <div className="fixed inset-0 z-40" onPointerDown={() => setSymbolMenue(null)} />
          <div className="fixed z-50 min-w-[180px] rounded-md border border-stone-300 bg-white p-1 text-sm text-stone-800 shadow-lg"
            style={{ left: symbolMenue.x, top: symbolMenue.y }}>
            <div className="px-3 py-1 text-[11px] text-stone-500">Glas-Schiebetüren</div>
            {[1, 2, 3].map((n) => <button
              key={n}
              type="button"
              className="block w-full rounded px-3 py-1.5 text-left hover:bg-emerald-50"
              onPointerDown={(event) => {
                event.preventDefault(); event.stopPropagation();
                setSymbolMenue(null);
                furniture.setFluegel(item.id, n);
              }}
            >{n === jetzt ? "✓ " : ""}{n} Flügel</button>)}
          </div>
        </>;
      })()}
      {punktMenue && (() => {
        const item = (furniture.document.symbols || []).find((x: any) => x.id === punktMenue.id);
        if (!item?.points_mm) return null;
        // Ausrichten bezieht sich auf die Auswahl -- und ohne Auswahl auf den
        // ganzen Lauf. Rainer, 2026-08-28: "why no align waagrecht and
        // senkrecht? Im just trying to make it easier for the Bauen part."
        // Der erste Anlauf zeigte die Befehle nur bei zwei gewaehlten Punkten
        // und antwortete sonst mit einem Hinweis -- ein Menue, das erklaert
        // statt zu tun. Der haeufigste Fall ist ohnehin "die ganze Zeile soll
        // gerade sein".
        const eintraege: [string, boolean, () => void][] = [];
        const ziel = punktAuswahl.length > 1
          ? punktAuswahl
          : item.points_mm.map((_: any, i: number) => i);
        const worauf = punktAuswahl.length > 1
          ? `${punktAuswahl.length} Punkte`
          : `alle ${item.points_mm.length}`;
        eintraege.push([`Waagerecht ausrichten (${worauf})`, ziel.length > 1, () =>
          furniture.setPoints(item.id, richtePunkteAus(item.points_mm, ziel, 1))]);
        eintraege.push([`Senkrecht ausrichten (${worauf})`, ziel.length > 1, () =>
          furniture.setPoints(item.id, richtePunkteAus(item.points_mm, ziel, 0))]);
        if (punktMenue.punkt !== null) {
          eintraege.push([
            item.points_mm.length > 2 ? "Diesen Punkt löschen" : "Punkt löschen (mindestens zwei nötig)",
            item.points_mm.length > 2,
            () => {
              furniture.setPoints(item.id, loeschePunkt(item.points_mm, punktMenue.punkt as number));
              setPunktAuswahl([]);
            },
          ]);
        }
        return <>
          <div className="fixed inset-0 z-40" onPointerDown={() => setPunktMenue(null)} />
          <div className="fixed z-50 min-w-[210px] rounded-md border border-stone-300 bg-white p-1 text-sm text-stone-800 shadow-lg"
            style={{ left: punktMenue.x, top: punktMenue.y }}>
            <div className="px-3 py-1 text-[11px] text-stone-500">
              {item.points_mm.length} Punkte{punktAuswahl.length ? ` · ${punktAuswahl.length} gewählt` : ""}
            </div>
            {eintraege.map(([text, aktiv, tun], index) => <button
              key={index}
              type="button"
              disabled={!aktiv}
              className="block w-full rounded px-3 py-1.5 text-left hover:bg-emerald-50 disabled:text-stone-400 disabled:hover:bg-transparent"
              onPointerDown={(event) => { event.preventDefault(); event.stopPropagation(); setPunktMenue(null); tun(); }}
            >{text}</button>)}
          </div>
        </>;
      })()}
      <aside className="space-y-4 rounded-3xl bg-white p-5 shadow-sm">
        {/* moebel-alles-einrichten-v1 (Rainer, 2026-10-23: "the room names are
            there why not just populate automatically?"): jeder Raum dieses
            Geschosses nach seinem Namen, wie "Bereich einrichten" mit dem
            ganzen Raum als Bereich. Gespeichert wird erst mit "Speichern". */}
        <button
          type="button"
          className="w-full rounded-xl border border-amber-300 bg-amber-50 px-3 py-2 text-sm font-semibold text-amber-900 hover:bg-amber-100"
          onClick={() => {
            if (moebelGeometrieFehltNoch) {
              furniture.placeMany([], "Baugeometrie lädt noch — Einrichten gesperrt.");
              return;
            }
            const fl = renderFloor || document.floors?.[floorIndex];
            const symbole = furniture.document.symbols || [];
            const oeffnungen = (fl?.openings || []).map((o: any) => {
              const wall = (fl?.walls || []).find((w: any) => w.id === o.wall_id);
              if (!wall) return null;
              const [a, b] = openingEndpoints(o, wall);
              return { a, b, typ: o.opening_type };
            }).filter(Boolean);
            const vorhandene = symbole.map((item: any) => {
              if (item.points_mm?.length) return { ...rechteckVon(item), symbol: item.symbol, points_mm: item.points_mm };
              const b = symbolBoundsMm(item);
              return b ? { x0: b.x, y0: b.y, x1: b.x + b.width, y1: b.y + b.height, symbol: item.symbol } : null;
            }).filter(Boolean);
            const raumKanten = (fl?.rooms || []).flatMap((raum: any) => {
              const pg = raum.polygon || raum.polygon_mm || [];
              return pg.map((a: Point, i: number) => [a, pg[(i + 1) % pg.length]]);
            });
            const raeume = (fl?.rooms || []).map((raum: any) => ({
              id: raum.id, name: raum.name || raum.label, kind: raum.kind,
              polygon_mm: raum.polygon || raum.polygon_mm || [],
            }));
            // Die Treppe ist ein Hindernis: keine Garderobe auf die Stufen.
            const treppe = fl?.stair?.polygon || [];
            const hindernisse = treppe.length >= 3 ? [{
              x0: Math.min(...treppe.map((p: Point) => p[0])), y0: Math.min(...treppe.map((p: Point) => p[1])),
              x1: Math.max(...treppe.map((p: Point) => p[0])), y1: Math.max(...treppe.map((p: Point) => p[1])),
            }] : [];
            const e: any = richteAlleRaeumeEin({ raeume, oeffnungen, vorhandene, raumKanten, hindernisse } as any);
            const teile: string[] = [];
            if (e.eingerichtet.length) teile.push(`Eingerichtet: ${e.eingerichtet.join(", ")}.`);
            if (e.uebersprungen.length) teile.push(`Ausgelassen: ${e.uebersprungen.map((u: any) => `${u.name} (${u.grund})`).join("; ")}.`);
            if (e.weggelassen.length) teile.push(`Nicht untergebracht: ${e.weggelassen.join(", ")}.`);
            furniture.placeMany(e.moebel, `${e.moebel.length} Möbel vorgeschlagen. ${teile.join(" ")} Anpassen oder „Zurück“ — noch nicht gespeichert.`);
          }}
        >✦ Alle Räume einrichten</button>
        <BereichEinrichten
          aktiv={einrichtenAktiv}
          onAktiv={(an: boolean) => { setEinrichtenAktiv(an); setActiveSymbolKey(null); setEinrichtBereich(null); }}
          bereich={einrichtBereich}
          raumtyp={einrichtRaumtyp}
          onRaumtyp={setEinrichtRaumtyp}
          raumtypen={RAUMTYPEN}
          onZurueck={() => { furniture.zurueck(); setPunktAuswahl([]); }}
          zurueckMoeglich={furniture.kannZurueck()}
          onVerwerfen={() => { setEinrichtenAktiv(false); setEinrichtBereich(null); }}
          onEinrichten={() => {
            if (!einrichtBereich || !einrichtRaumtyp) return;
            if (moebelGeometrieFehltNoch) {
              furniture.placeMany([], "Baugeometrie lädt noch — Einrichten gesperrt.");
              return;
            }
            const fl = renderFloor || document.floors?.[floorIndex];
            const poly = einrichtBereich.polygon;
            const symbole = furniture.document.symbols || [];
            // Rainer: stehen schon Moebel im Bereich, vorher fragen.
            const schonDa = symbole.filter((item: any) => {
              const m = mitteVon(item);
              return m && punktImPolygon(m[0], m[1], poly);
            }).length;
            if (schonDa && !window.confirm(
              `Im Bereich stehen schon ${schonDa} Möbel.

Trotzdem zusätzlich einrichten?`)) return;
            const oeffnungen = (fl?.openings || []).map((o: any) => {
              const wall = (fl?.walls || []).find((w: any) => w.id === o.wall_id);
              if (!wall) return null;
              const [a, b] = openingEndpoints(o, wall);
              return { a, b, typ: o.opening_type };
            }).filter(Boolean);
            const vorhandene = symbole.map((item: any) => {
              if (item.points_mm?.length) return { ...rechteckVon(item), symbol: item.symbol, points_mm: item.points_mm };
              const b = symbolBoundsMm(item);
              return b ? { x0: b.x, y0: b.y, x1: b.x + b.width, y1: b.y + b.height, symbol: item.symbol } : null;
            }).filter(Boolean);
            // Echte Waende = Kanten der gezeichneten Raeume. Ein selbst
            // gezeichneter Bereich hat auch offene Kanten (nur Luft).
            const raumKanten = (fl?.rooms || []).flatMap((raum: any) => {
              const pg = raum.polygon || raum.polygon_mm || [];
              return pg.map((a: Point, i: number) => [a, pg[(i + 1) % pg.length]]);
            });
            const raumPolygone = (fl?.rooms || []).map((raum: any) => raum.polygon || raum.polygon_mm || []);
            const ergebnis = richteBereichEin({ polygon: poly, oeffnungen, vorhandene, raumKanten, raumPolygone } as any, einrichtRaumtyp);
            const fehlt = ergebnis.weggelassen.length ? ` Nicht untergebracht: ${ergebnis.weggelassen.join(", ")}.` : "";
            furniture.placeMany(ergebnis.moebel, ergebnis.moebel.length
              ? `${ergebnis.moebel.length} Möbel vorgeschlagen.${fehlt} Anpassen oder „Zurück“ — noch nicht gespeichert.`
              : `Nichts untergebracht.${fehlt}`);
            setEinrichtBereich(null);
          }}
        />
        {/vorgeschlagen|untergebracht|gesperrt/.test(`${furniture.status || ""}`) ? (
          <p role="status" className="rounded-xl border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">{furniture.status}</p>
        ) : null}
        <FurniturePalette
          activeKey={activeSymbolKey}
          onPick={(key: string | null) => { setActiveSymbolKey(key); setSelectedFurnitureId(null); setPunktAuswahl([]); }}
          selected={(furniture.document.symbols || []).find((item: any) => item.id === selectedFurnitureId) || null}
          onRotate={(delta: number) => {
            if (moebelAuswahl.length > 1) {
              const fehler = furniture.rotateGroup(moebelAuswahl, delta);
              if (fehler) window.alert(fehler);
              return;
            }
            if (selectedFurnitureId) furniture.rotate(selectedFurnitureId, delta);
          }}
          onMirror={() => selectedFurnitureId && furniture.mirror(selectedFurnitureId)}
          onRemove={() => {
            if (moebelAuswahl.length > 1) { furniture.removeGroup(moebelAuswahl); setSelectedFurnitureId(null); setMoebelGruppe([]); return; }
            if (selectedFurnitureId) { furniture.remove(selectedFurnitureId); setSelectedFurnitureId(null); }
          }}
          gruppenGroesse={moebelAuswahl.length || 1}
          onSave={furniture.save}
          onSendToRender={furniture.sendToRender}
          dirty={furniture.dirty}
          status={furniture.status}
          geometryReady={!moebelGeometrieFehltNoch}
          geometryWarning={moebelGeometrieFehltNoch
            ? (renderGeo?.fehler
                ? `Baugeometrie nicht geladen (${renderGeo.fehler}) — Speichern gesperrt, um nicht im falschen Koordinatensystem abzuspeichern.`
                : "Baugeometrie lädt noch — Speichern gesperrt, um nicht im falschen Koordinatensystem abzuspeichern.")
            : null}
          roomFilter={furnitureRoomFilter}
          onRoomFilter={setFurnitureRoomFilter}
          roomNames={((renderFloor || document.floors?.[floorIndex])?.rooms || []).map((room: any) => room.name)}
          count={(furniture.document.symbols || []).length}
          // DASSELBE Geschoss wie die Zeichenflaeche (Zeile 303:
          // `overrideFloor || document.floors[floorIndex]`). Rainer,
          // 2026-08-29: das Panel meldete elf Moebel "ausserhalb der Raeume"
          // bei einem fertigen Haus -- alle elf lagen in einem gezeichneten
          // Raum. Es mass gegen das Korrekturdokument (x bis 10600), die
          // Zeichenflaeche gegen das Rendergeschoss (x bis 15234).
          rooms={(renderFloor || document.floors?.[floorIndex])?.rooms || []}
          symbols={furniture.document.symbols || []}
          // MOEBEL-LEERER-RAUM-001: alle Geschosse, in DERSELBEN Geometrie wie
          // die Zeichenflaeche (renderGeo, polygon_mm). Das aktuelle Geschoss
          // mit dem ungespeicherten Stand, die anderen wie gespeichert.
          leereRaeumeAllerGeschosse={renderGeo?.floors ? async () => {
            const geschosse = renderGeo.floors as any[];
            const namen: string[] = [];
            for (let i = 0; i < geschosse.length; i += 1) {
              // Im Moebel-Fenster der Hausakte gibt es oft keinen Korrektur-
              // Kandidaten (history) -- dann war floorId leer und JEDES
              // Geschoss wurde stillschweigend uebersprungen: keine Warnung,
              // nie. Rainer, 2026-10-16: "they were not there before and no
              // warning came". Die Moebeldateien heissen floor-0, floor-1, ...
              const floorId = history?.present?.floors?.[i]?.id || `floor-${i}`;
              const symbole = i === floorIndex
                ? (furniture.document.symbols || [])
                : await ladeMoebel(furnitureReference, floorId);
              const roh = history?.present?.floors?.[i]?.name || geschosse[i]?.floor_level || "";
              const name = ({ groundfloor: "EG", upperfloor: "OG", basement: "KG", staffelgeschoss: "SG", attic: "DG" } as Record<string, string>)[roh]
                || roh || `Geschoss ${i + 1}`;
              for (const raum of leereRaeume(symbole, geschosse[i]?.rooms || [])) {
                namen.push(geschosse.length > 1 ? `${name}: ${raum.name}` : raum.name);
              }
            }
            return namen;
          } : undefined}
          punktAuswahl={punktAuswahl}
          onPunkteAusrichten={(achse: 0 | 1) => {
            const item = (furniture.document.symbols || []).find((x: any) => x.id === selectedFurnitureId);
            if (!item?.points_mm || punktAuswahl.length < 2) return;
            furniture.setPoints(item.id, richtePunkteAus(item.points_mm, punktAuswahl, achse));
          }}
          onZurueck={() => { furniture.zurueck(); setPunktAuswahl([]); }}
          zurueckMoeglich={furniture.kannZurueck()}
          onSelect={(id: string) => { setSelectedFurnitureId(id); setPunktAuswahl([]); }}
          onRemoveById={(id: string) => {
            furniture.remove(id);
            if (selectedFurnitureId === id) setSelectedFurnitureId(null);
          }}
        />
        {/* Der Erklaertext ist weg. Rainer, 2026-08-30: "get rid of that
            text i would rather see more furniture" -- vier Zeilen Anleitung
            standen dauerhaft ueber der Moebelliste, obwohl sie nur beim
            ERSTEN Mal etwas sagen. Die Ueberschrift erscheint jetzt nur,
            wenn wirklich etwas ausgewaehlt ist; ohne Auswahl gibt es unter
            ihr ohnehin nichts zu sehen. */}
        {selection && <>
          <hr className="border-stone-200" />
          <h2 className="text-xl font-semibold">Selected geometry</h2>
        </>}
        {selected?.coordinates && <div className="grid grid-cols-2 gap-3">
          <label className="text-sm">X (mm)<input type="number" value={selected.coordinates[0]} onChange={(event) => setCoordinate(0, Number(event.target.value))} className="mt-1 w-full rounded border p-2" /></label>
          <label className="text-sm">Y (mm)<input type="number" value={selected.coordinates[1]} onChange={(event) => setCoordinate(1, Number(event.target.value))} className="mt-1 w-full rounded border p-2" /></label>
        </div>}
        {selection?.type === "opening" && selected?.item && <>
          <label className="block text-sm">Wall<select value={selected.item.wall_id} onChange={(event) => commitMutation((next) => { next.floors[floorIndex].openings.find((item: any) => item.id === selection.id).wall_id = event.target.value; })} className="mt-1 w-full rounded border p-2">{document.floors[floorIndex].walls.map((wall: any) => <option key={wall.id}>{wall.id}</option>)}</select></label>
          <label className="block text-sm">Position along wall<input type="number" min="0" max="1" step=".01" value={selected.item.position} onChange={(event) => commitMutation((next) => { next.floors[floorIndex].openings.find((item: any) => item.id === selection.id).position = Number(event.target.value); })} className="mt-1 w-full rounded border p-2" /></label>
          <label className="block text-sm">Opening width (mm)<input type="number" min="300" step="10" value={selected.item.width} onChange={(event) => commitMutation((next) => { next.floors[floorIndex].openings.find((item: any) => item.id === selection.id).width = Number(event.target.value); })} className="mt-1 w-full rounded border p-2" /></label>
          {selected.item.opening_type === "window" && <label className="block text-sm">Window height (mm)<input type="number" min="300" step="10" value={selected.item.height_mm || FLOORPLAN_RULES.windows.defaultHeightMm} onChange={(event) => commitMutation((next) => { next.floors[floorIndex].openings.find((item: any) => item.id === selection.id).height_mm = Number(event.target.value); })} className="mt-1 w-full rounded border p-2" /></label>}
        </>}
        {/* Die Farblegende gehoert zur Geometrie. Im Moebel-Schritt sagt sie
            nichts und nimmt sieben Zeilen weg. */}
        {planView !== "furniture" && <div className="space-y-2 border-t pt-4 text-xs">
          <p className="font-semibold">Closed opening legend</p>
          <p><span className="mr-2 inline-block h-2.5 w-6 bg-emerald-700" />Entrance 1100 mm</p>
          <p><span className="mr-2 inline-block h-2.5 w-6 bg-cyan-600" />Glazed terrace door 1800 mm</p>
          <p><span className="mr-2 inline-block h-2.5 w-6 bg-blue-600" />Internal door 880 mm</p>
          <p><span className="mr-2 inline-block h-2.5 w-6 bg-amber-600" />Small-WC door 760 mm</p>
          <p><span className="mr-2 inline-block h-2.5 w-6 bg-cyan-500" />Window</p>
        </div>}
        {/* Das Treppen-Regelwerk ebenso: es gehoert zur Geometrie. */}
        {planView !== "furniture" && <div className="space-y-1 border-t pt-4 text-xs text-stone-600">
          <p className="font-semibold text-stone-900">Stair rulebook</p>
          <p>900 mm usable width Â· arrow always upward Â· identical core on both floors.</p>
          <p>Bastian forms: straight, quarter-turn, double-quarter-turn. Walking zone: middle 20% of usable width.</p>
          <p>No tread lines until a valid straight or fan-shaped tread layout exists.</p>
          <a className="text-blue-700 underline" href={FLOORPLAN_RULES.stairs.reference.url} target="_blank" rel="noreferrer">Official System Bastian reference</a>
        </div>}
        <div className="grid grid-cols-2 gap-2 border-t pt-4">
          <button disabled={!history.past.length} onClick={() => setHistory(undoEditorHistory(history))} className="rounded bg-stone-200 p-2 disabled:opacity-40">Undo</button>
          <button disabled={!history.future.length} onClick={() => setHistory(redoEditorHistory(history))} className="rounded bg-stone-200 p-2 disabled:opacity-40">Redo</button>
          <button onClick={() => setHistory(resetEditorHistory(history))} className="col-span-2 rounded bg-amber-200 p-2">Reset to immutable source</button>
        </div>
        <p className="text-xs break-words text-stone-600">{message}</p>
      </aside>
    </section>
    {!embed && <><section className="grid gap-5 lg:grid-cols-2">
      <article className="rounded-3xl bg-white p-5"><h2 className="text-xl font-semibold">Corrected safe JPEG</h2>{preview ? <><img src={`data:image/jpeg;base64,${preview.file_base64}`} alt="Corrected raster floorplan" className="mt-3 w-full rounded border" /><p className="mt-2 break-all text-xs">JPEG SHA-256 {preview.sha256} Â· geometry {preview.geometry_hash}</p></> : <p className="mt-3 text-sm">Select Validate to render from the corrected canonical JSON.</p>}</article>
      <article className="rounded-3xl bg-white p-5">
        <div className="flex flex-wrap items-center justify-between gap-2">
          <h2 className="text-xl font-semibold">Corrected deterministic 3D guide</h2>
          <button onClick={() => action("approve")} className="rounded-full bg-emerald-700 px-4 py-2 text-sm font-semibold text-white">Approve this plan locally</button>
        </div>
        <div className="mt-3">{blenderPreview?.render_view === massingView ? <img src={`data:image/png;base64,${blenderPreview.png_base64}`} alt={`Deterministic Blender ${massingView} preview`} className="w-full rounded-2xl border" /> : <Massing document={document} view={massingView} />}</div>
        <button onClick={() => action("render_blender", { view: massingView })} className="mt-3 rounded-full bg-blue-700 px-4 py-2 text-sm font-semibold text-white">Render {MASSING_VIEWS.find((view) => view.id === massingView)?.label} in Blender</button>
        <div className="mt-3 flex flex-wrap gap-2">
          {MASSING_VIEWS.map((view) => <button key={view.id} onClick={() => { setMassingView(view.id); notify(`${view.label} selected — render this view to update Blender.`, "info"); }} className={`rounded-full px-3 py-2 text-sm ${massingView === view.id ? "bg-slate-900 text-white" : "bg-stone-200"}`}>{view.label}{view.id === "garden" ? " Â· Schokoladenseite" : ""}</button>)}
        </div>
        <p className="mt-2 text-xs">Click a side to rotate the same geometry. Windows and doors are projected in their wall planes; approval still respects geometry and rights gates.</p>
      </article>
    </section>
    <section className="rounded-3xl bg-white p-6">
      <h2 className="text-xl font-semibold">Rights and approval gate</h2>
      <div className="mt-4 grid gap-4 md:grid-cols-3">
        <label>Source status<input value={document.rights.source_status || "not_restricted"} readOnly className="mt-1 w-full rounded border bg-stone-100 p-2" /></label>
        <label>Usage scope<select value={document.rights.usage_scope} onChange={(event) => commitMutation((next) => { next.rights.usage_scope = event.target.value; next.rights.wordpress_eligible = false; })} className="mt-1 w-full rounded border p-2"><option value="internal_reference_only">internal_reference_only</option><option value="commercial_generator">commercial_generator</option></select></label>
        <label>Explicit rights decision<select value={document.rights.decision} onChange={(event) => commitMutation((next) => { next.rights.decision = event.target.value; next.rights.wordpress_eligible = false; })} className="mt-1 w-full rounded border p-2"><option value="undecided">Undecided â€” WordPress blocked</option><option value="internal_review_confirmed">Internal review only confirmed</option><option value="commercially_cleared">Commercial rights independently cleared</option></select></label>
      </div>
      {document.provenance?.transformation === "generic_layout_reconstruction" && <label className="mt-4 flex items-start gap-3 rounded-2xl bg-amber-50 p-4 text-sm ring-1 ring-amber-300"><input type="checkbox" className="mt-1" checked={document.rights.commercial_approval_attested === true} onChange={(event) => commitMutation((next) => { const approved = event.target.checked; next.rights.commercial_approval_attested = approved; next.rights.usage_scope = approved ? "commercial_generator" : "internal_reference_only"; next.rights.decision = approved ? "generic_layout_reconstructed" : "undecided"; next.rights.wordpress_eligible = false; next.wordpress_eligible = false; })} /><span>I approve this corrected output as a reconstructed generic functional layout. The original image and internal source snapshot must not be included in the exported dataset package.</span></label>}
      <p className="mt-3 text-sm">Geometry approval and commercial-output approval are separate. WordPress eligibility is enabled only after geometry validation, local approval and the applicable explicit output decision. Exported packages contain the cleaned canonical plan and JPEG, never the original reference asset.</p>
    </section>
    {validation && <section className={`rounded-3xl p-5 ${validation.valid ? "bg-emerald-100" : "bg-red-100"}`}><h2 className="font-semibold">Hard validation: {validation.valid ? "PASS" : "BLOCKED"}</h2><p className="mt-2 text-sm">{validation.errors.join(" Â· ") || "Source preserved; openings wall-linked; stair shared and â‰¥ 900 mm; hashes match."}</p><p className="mt-1 text-xs">{validation.warnings.join(" Â· ")}</p></section>}
    <section className="wb-aktionen flex flex-wrap gap-3 rounded-3xl bg-slate-900 p-5 text-white">
      <button onClick={() => action("save_draft")} className="wb-speichern rounded-full bg-sky-600 px-5 py-3">Save draft</button>
      <button onClick={() => action("validate")} className="rounded-full bg-violet-600 px-5 py-3">Validate + re-render</button>
      <button onClick={() => action("approve")} className="rounded-full bg-emerald-600 px-5 py-3">Approve locally</button>
      <button onClick={() => action("reject")} className="rounded-full bg-red-600 px-5 py-3">Reject</button>
      <button onClick={() => action("export")} className="rounded-full bg-amber-500 px-5 py-3 text-black">Export approved package</button>
    </section>
    </>}
  </main>;
}

