"use client";
/* eslint-disable @typescript-eslint/no-explicit-any, @next/next/no-img-element, react-hooks/refs */

import { useEffect, useMemo, useRef, useState } from "react";
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
  history,
  setHistory,
  floorIndex,
  selection,
  setSelection,
  grid,
  showHandles,
}: any) {
  const document = history.present;
  const floor = document.floors[floorIndex];
  const box = documentBounds(document, floorIndex);
  const svgRef = useRef<SVGSVGElement>(null);
  const dragSource = useRef<any>(null);
  const marqueeDrag = useRef<{ start: Point } | null>(null);
  const [marqueeBox, setMarqueeBox] = useState<{ x: number; y: number; w: number; h: number } | null>(null);
  const [marqueeSelection, setMarqueeSelection] = useState<Selection[]>([]);

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
    viewBox={`${box.minX} ${box.minY} ${box.width} ${box.height}`}
    className="h-[680px] w-full touch-none rounded-2xl border bg-white"
    onPointerDown={startMarquee}
    onPointerMove={(event) => { if (dragSource.current) { update(coordinate(event)); } else { updateMarquee(event); } }}
    onPointerUp={() => { finish(); finishMarquee(); }}
  >
    {marqueeSelection.length > 0 && <text x={box.minX + 40} y={box.minY + 90} fontSize="130" fontWeight="700" fill="#b45309">{marqueeSelection.length} points selected · arrow keys to move · Esc to clear</text>}
    {marqueeBox && <rect x={marqueeBox.x} y={marqueeBox.y} width={marqueeBox.w} height={marqueeBox.h} fill="rgba(37,99,235,0.12)" stroke="#2563eb" strokeWidth="10" strokeDasharray="40 20" />}
    {floor.rooms.map((room: any) => {
      const label = roomLabelPoint(room, document.shared_stair_core);
      return <g key={room.id}>
      <polygon points={room.polygon.map((point: Point) => point.join(",")).join(" ")} fill={ROOM_COLORS[room.kind] || ROOM_COLORS.flex} stroke="none" />
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
      {showHandles && room.polygon.map((point: Point, index: number) => { const selected = marqueeSelection.some((sel) => sameSelection(sel, { type: "room", id: room.id, point: index })); return <circle key={index} cx={point[0]} cy={point[1]} r={selected ? 125 : 95} fill="#16a34a" stroke={selected ? "#f59e0b" : "#fff"} strokeWidth={selected ? 55 : 35} onPointerDown={(event) => begin(event, { type: "room", id: room.id, point: index })} />; })}
    </g>;
    })}
    {floor.walls.map((wall: any) => <g key={wall.id}>
      <line x1={wall.start[0]} y1={wall.start[1]} x2={wall.end[0]} y2={wall.end[1]} stroke="#1c1917" strokeWidth={wall.thickness} strokeLinecap="square" />
      {showHandles && [wall.start, wall.end].map((point: Point, index: number) => { const selected = marqueeSelection.some((sel) => sameSelection(sel, { type: "wall", id: wall.id, point: index as 0 | 1 })); const size = selected ? 240 : 180; return <rect key={index} x={point[0] - size / 2} y={point[1] - size / 2} width={size} height={size} fill="#2563eb" stroke={selected ? "#f59e0b" : "#fff"} strokeWidth={selected ? 50 : 30} onPointerDown={(event) => begin(event, { type: "wall", id: wall.id, point: index as 0 | 1 })} />; })}
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
        {showHandles && <circle cx={point[0]} cy={point[1]} r="105" fill={opening.opening_type === "window" ? "#06b6d4" : "#f97316"} stroke="#fff" strokeWidth="35" onPointerDown={(event) => begin(event, { type: "opening", id: opening.id })} />}
      </g>;
    })}
    {document.shared_stair_core?.polygon && <g>
      <polygon points={document.shared_stair_core.polygon.map((point: Point) => point.join(",")).join(" ")} fill="#fafaf9" fillOpacity=".9" stroke="#57534e" strokeWidth="100" />
      <line x1={reviewStairPath(document.shared_stair_core)[0][0]} y1={reviewStairPath(document.shared_stair_core)[0][1]} x2={reviewStairPath(document.shared_stair_core)[1][0]} y2={reviewStairPath(document.shared_stair_core)[1][1]} stroke="#1d5b4a" strokeWidth="45" />
      <polygon points={stairArrow(reviewStairPath(document.shared_stair_core))} fill="#1d5b4a" />
      <text
        x={(polygonBox(document.shared_stair_core.polygon).minX + polygonBox(document.shared_stair_core.polygon).maxX) / 2}
        y={(polygonBox(document.shared_stair_core.polygon).minY + polygonBox(document.shared_stair_core.polygon).maxY) / 2}
        textAnchor="middle"
        fontSize="155"
        fontWeight="700"
        fill="#1d5b4a"
        style={{ paintOrder: "stroke", stroke: "#fff", strokeWidth: 38 }}
      >TREPPE â†‘</text>
      {showHandles && document.shared_stair_core.polygon.map((point: Point, index: number) => { const selected = marqueeSelection.some((sel) => sameSelection(sel, { type: "stair", point: index })); return <circle key={index} cx={point[0]} cy={point[1]} r={selected ? 130 : 100} fill="#7c3aed" stroke={selected ? "#f59e0b" : "#fff"} strokeWidth={selected ? 55 : 35} onPointerDown={(event) => begin(event, { type: "stair", point: index })} />; })}
    </g>}
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
export default function FloorplanWorkbenchPage() {
  const [history, setHistory] = useState<any>(null);
  const [floorIndex, setFloorIndex] = useState(0);
  const [selection, setSelection] = useState<Selection | null>(null);
  const [grid, setGrid] = useState<number>(CORRECTION_DEFAULTS.editSnapMm);
  const [showHandles, setShowHandles] = useState(false);
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
  return <main className="mx-auto max-w-[1500px] space-y-6 p-5">
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
      <p className="mt-2">The same cleaned millimetre geometry drives the editor, JPEG and 3D guide. Source annotation remains read-only.</p>
      <p className="mt-1 text-sm">Geometry hash: <span className="break-all font-mono text-xs">{document.geometry_hash}</span></p>
      <p className="mt-1 text-xs">Transform: {proof?.transform || "identity"} · revision {document.revision} · approval {document.status} · Rulebook: {FLOORPLAN_RULEBOOK_VERSION}</p>
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
    <section className="grid gap-5 xl:grid-cols-[1fr_330px]">
      <div className="space-y-3">
        <div className="flex flex-wrap gap-2">
          {document.floors.map((floor: any, index: number) => <button key={floor.id} onClick={() => { setFloorIndex(index); setSelection(null); }} className={`rounded-full px-4 py-2 ${index === floorIndex ? "bg-slate-900 text-white" : "bg-white"}`}>{floor.name}</button>)}
          <button onClick={() => { setShowHandles((value) => !value); setSelection(null); }} className={`rounded-full px-4 py-2 ${showHandles ? "bg-blue-700 text-white" : "bg-white"}`}>{showHandles ? "Hide edit handles" : "Edit geometry"}</button>
          <label className="ml-auto rounded-full bg-white px-4 py-2">Snap <input type="number" min="10" step="10" value={grid} onChange={(event) => setGrid(Number(event.target.value))} className="w-20 border-b text-right" /> mm</label>
        </div>
        <GeometryEditor history={history} setHistory={setHistory} floorIndex={floorIndex} selection={selection} setSelection={setSelection} grid={grid} showHandles={showHandles} />
      </div>
      <aside className="space-y-4 rounded-3xl bg-white p-5 shadow-sm">
        <h2 className="text-xl font-semibold">Selected geometry</h2>
        {!selection && <p className="text-sm text-stone-600">The clean view is the default. Select â€œEdit geometryâ€ to show room points, wall endpoints, wall-linked openings and the shared stair core. Drag on empty space (not on a handle) to draw a selection box around several points at once, then use the arrow keys to move all of them together; Shift+arrow moves in bigger steps, Esc clears the selection.</p>}
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
        <div className="space-y-2 border-t pt-4 text-xs">
          <p className="font-semibold">Closed opening legend</p>
          <p><span className="mr-2 inline-block h-2.5 w-6 bg-emerald-700" />Entrance 1100 mm</p>
          <p><span className="mr-2 inline-block h-2.5 w-6 bg-cyan-600" />Glazed terrace door 1800 mm</p>
          <p><span className="mr-2 inline-block h-2.5 w-6 bg-blue-600" />Internal door 880 mm</p>
          <p><span className="mr-2 inline-block h-2.5 w-6 bg-amber-600" />Small-WC door 760 mm</p>
          <p><span className="mr-2 inline-block h-2.5 w-6 bg-cyan-500" />Window</p>
        </div>
        <div className="space-y-1 border-t pt-4 text-xs text-stone-600">
          <p className="font-semibold text-stone-900">Stair rulebook</p>
          <p>900 mm usable width Â· arrow always upward Â· identical core on both floors.</p>
          <p>Bastian forms: straight, quarter-turn, double-quarter-turn. Walking zone: middle 20% of usable width.</p>
          <p>No tread lines until a valid straight or fan-shaped tread layout exists.</p>
          <a className="text-blue-700 underline" href={FLOORPLAN_RULES.stairs.reference.url} target="_blank" rel="noreferrer">Official System Bastian reference</a>
        </div>
        <div className="grid grid-cols-2 gap-2 border-t pt-4">
          <button disabled={!history.past.length} onClick={() => setHistory(undoEditorHistory(history))} className="rounded bg-stone-200 p-2 disabled:opacity-40">Undo</button>
          <button disabled={!history.future.length} onClick={() => setHistory(redoEditorHistory(history))} className="rounded bg-stone-200 p-2 disabled:opacity-40">Redo</button>
          <button onClick={() => setHistory(resetEditorHistory(history))} className="col-span-2 rounded bg-amber-200 p-2">Reset to immutable source</button>
        </div>
        <p className="text-xs break-words text-stone-600">{message}</p>
      </aside>
    </section>
    <section className="grid gap-5 lg:grid-cols-2">
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
    <section className="flex flex-wrap gap-3 rounded-3xl bg-slate-900 p-5 text-white">
      <button onClick={() => action("save_draft")} className="rounded-full bg-sky-600 px-5 py-3">Save draft</button>
      <button onClick={() => action("validate")} className="rounded-full bg-violet-600 px-5 py-3">Validate + re-render</button>
      <button onClick={() => action("approve")} className="rounded-full bg-emerald-600 px-5 py-3">Approve locally</button>
      <button onClick={() => action("reject")} className="rounded-full bg-red-600 px-5 py-3">Reject</button>
      <button onClick={() => action("export")} className="rounded-full bg-amber-500 px-5 py-3 text-black">Export approved package</button>
    </section>
  </main>;
}



