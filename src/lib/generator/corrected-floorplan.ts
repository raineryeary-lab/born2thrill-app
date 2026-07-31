import sharp from "sharp";
import {
  selectApprovedFloorplan,
} from "./approved-floorplan-catalog";
import type {
  HouseBrief,
  PlanVariant,
  PlannedRoom,
  StairGeometry,
} from "./floorplan";

type Point = [number, number];

type CorrectionRoom = {
  id: string;
  name: string;
  kind: PlannedRoom["kind"];
  polygon: Point[];
  area_m2: number;
};

type CorrectionWall = {
  id: string;
  start: Point;
  end: Point;
  thickness: number;
  wall_type: "exterior" | "partition";
  room_ids: string[];
};

type CorrectionOpening = {
  id: string;
  opening_type: "door" | "window" | "passage";
  wall_id: string;
  position: number;
  width: number;
  role: string;
  connects: string[];
  traversable: boolean;
};

type CorrectionFloor = {
  id: string;
  name: string;
  level: number;
  footprint: Point[];
  rooms: CorrectionRoom[];
  walls: CorrectionWall[];
  openings: CorrectionOpening[];
  stair_core_id: string | null;
};

type CorrectionDocument = {
  schema: string;
  revision: number;
  plan_id: string;
  source_reference_id?: string;
  provenance: {
    creation_mode: string;
    source_assets_included: false;
    internal_source_record_retained_locally?: boolean;
  };
  rights: {
    usage_scope: "internal_reference_only" | "commercial_generator";
    decision: string;
    wordpress_eligible: boolean;
  };
  building: {
    coordinate_unit: "mm";
    footprint_width_mm: number;
    footprint_depth_mm: number;
    storey_type: HouseBrief["storeyType"];
  };
  floors: CorrectionFloor[];
  shared_stair_core: {
    id: string;
    polygon: Point[];
    path: Point[];
    plan_type: string;
    usable_width_mm: number;
    geometry: StairGeometry;
    direction: "up";
    representation: string;
    tread_geometry_valid: boolean;
    floor_ids: string[];
  } | null;
  geometry_hash: string;
  status: string;
  wordpress_eligible: boolean;
};

const JPEG_WIDTH = 1800;
const MAX_JPEG_BYTES = 3 * 1024 * 1024;

const ROOM_COLORS: Record<PlannedRoom["kind"], string> = {
  living: "#d9f7e5",
  sleeping: "#f5f1e8",
  wet: "#dcecff",
  service: "#fff1bd",
  flex: "#f4f1ec",
  circulation: "#ece9e2",
};

export const CORRECTED_FLOORPLAN_GENERATOR_VERSION =
  "approved-mm-catalog-jpeg-v2";

function documentReferenceId(document: CorrectionDocument) {
  return document.plan_id || document.source_reference_id || "approved-plan";
}

function polygonBounds(polygon: Point[]) {
  const xs = polygon.map(([x]) => x);
  const ys = polygon.map(([, y]) => y);
  return {
    minX: Math.min(...xs),
    minY: Math.min(...ys),
    maxX: Math.max(...xs),
    maxY: Math.max(...ys),
  };
}

function pointInPolygon([x, y]: Point, polygon: Point[]) {
  let inside = false;
  for (
    let index = 0, previous = polygon.length - 1;
    index < polygon.length;
    previous = index, index += 1
  ) {
    const [xi, yi] = polygon[index];
    const [xj, yj] = polygon[previous];
    const crosses = (yi > y) !== (yj > y)
      && x < ((xj - xi) * (y - yi)) / (yj - yi) + xi;
    if (crosses) inside = !inside;
  }
  return inside;
}

function distanceToSegment(point: Point, start: Point, end: Point) {
  const dx = end[0] - start[0];
  const dy = end[1] - start[1];
  const lengthSquared = dx * dx + dy * dy;
  const ratio = lengthSquared === 0
    ? 0
    : Math.max(
        0,
        Math.min(
          1,
          ((point[0] - start[0]) * dx + (point[1] - start[1]) * dy)
            / lengthSquared,
        ),
      );
  return Math.hypot(
    point[0] - (start[0] + ratio * dx),
    point[1] - (start[1] + ratio * dy),
  );
}

function polygonClearance(point: Point, polygon: Point[]) {
  return Math.min(
    ...polygon.map((start, index) =>
      distanceToSegment(point, start, polygon[(index + 1) % polygon.length])
    ),
  );
}

function roomLabelPoint(room: CorrectionRoom, stair: Point[] | null): Point {
  const box = polygonBounds(room.polygon);
  const center: Point = [
    (box.minX + box.maxX) / 2,
    (box.minY + box.maxY) / 2,
  ];
  let best = center;
  let bestScore = Number.NEGATIVE_INFINITY;
  const columns = 17;
  const rows = 17;
  for (let column = 1; column < columns; column += 1) {
    for (let row = 1; row < rows; row += 1) {
      const candidate: Point = [
        box.minX + ((box.maxX - box.minX) * column) / columns,
        box.minY + ((box.maxY - box.minY) * row) / rows,
      ];
      if (!pointInPolygon(candidate, room.polygon)) continue;
      if (stair && pointInPolygon(candidate, stair)) continue;
      const roomClearance = polygonClearance(candidate, room.polygon);
      const stairClearance = stair
        ? Math.min(...stair.map((start, index) =>
            distanceToSegment(
              candidate,
              start,
              stair[(index + 1) % stair.length],
            )
          ))
        : roomClearance;
      const centerPenalty = Math.hypot(
        candidate[0] - center[0],
        candidate[1] - center[1],
      ) * 0.06;
      const score = Math.min(roomClearance, stairClearance) - centerPenalty;
      if (score > bestScore) {
        best = candidate;
        bestScore = score;
      }
    }
  }
  return best;
}

function pointAttribute(points: Point[]) {
  return points.map(([x, y]) => `${x},${y}`).join(" ");
}

function escapeXml(value: unknown) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

function openingEndpoints(opening: CorrectionOpening, wall: CorrectionWall) {
  const dx = wall.end[0] - wall.start[0];
  const dy = wall.end[1] - wall.start[1];
  const length = Math.max(1, Math.hypot(dx, dy));
  const half = opening.width / length / 2;
  return [opening.position - half, opening.position + half].map((ratio) => [
    wall.start[0] + dx * Math.max(0, Math.min(1, ratio)),
    wall.start[1] + dy * Math.max(0, Math.min(1, ratio)),
  ] as Point);
}

function doorColour(opening: CorrectionOpening) {
  if (opening.role === "main_entrance") return "#166534";
  if (opening.role === "terrace_door") return "#0e7490";
  return "#d97706";
}

function displayFloorName(
  document: CorrectionDocument,
  floor: CorrectionFloor,
) {
  if (floor.level === 0) return "Erdgeschoss";
  if (document.building.storey_type === "1_5_storey") return "Dachgeschoss";
  return floor.name || "Obergeschoss";
}

export function renderCorrectedFloorplanSvg(
  document: CorrectionDocument,
  options: { requestId?: string; mandatoryLabel?: string } = {},
) {
  const width = 1600;
  const height = 900;
  const panelWidth = 700;
  const panelGap = 70;
  const startX = 70;
  const stair = document.shared_stair_core;
  const floorMarkup = document.floors.map((floor, floorIndex) => {
    const box = polygonBounds(floor.footprint);
    const scale = Math.min(
      panelWidth / Math.max(box.maxX - box.minX, 1),
      610 / Math.max(box.maxY - box.minY, 1),
    );
    const originX = startX + floorIndex * (panelWidth + panelGap);
    const offsetX =
      originX + (panelWidth - (box.maxX - box.minX) * scale) / 2;
    const offsetY = 130 + (610 - (box.maxY - box.minY) * scale) / 2;
    const point = ([x, y]: Point): Point => [
      offsetX + (x - box.minX) * scale,
      offsetY + (y - box.minY) * scale,
    ];
    const roomFills = floor.rooms.map((room) => {
      const polygon = room.polygon.map(point);
      return `<polygon points="${pointAttribute(polygon)}" fill="${
        ROOM_COLORS[room.kind] || ROOM_COLORS.flex
      }" stroke="none"/>`;
    }).join("");
    const walls = floor.walls.map((wall) => {
      const start = point(wall.start);
      const end = point(wall.end);
      return `<line x1="${start[0]}" y1="${start[1]}" x2="${end[0]}" y2="${
        end[1]
      }" stroke="#1c1917" stroke-width="${Math.max(
        3,
        wall.thickness * scale,
      )}" stroke-linecap="square"/>`;
    }).join("");
    const openings = floor.openings.map((opening) => {
      const wall = floor.walls.find(
        (candidate) => candidate.id === opening.wall_id,
      );
      if (!wall) return "";
      const [first, second] = openingEndpoints(opening, wall).map(point);
      const common =
        `x1="${first[0]}" y1="${first[1]}" x2="${second[0]}" y2="${second[1]}"`;
      const gap = `<line ${common} stroke="#fff" stroke-width="${Math.max(
        7,
        wall.thickness * scale + 4,
      )}"/>`;
      if (opening.opening_type === "window") {
        return `${gap}<line ${common} stroke="#12aee2" stroke-width="4"/>`;
      }
      if (opening.opening_type === "passage") {
        return `${gap}<line ${common} stroke="#059669" stroke-width="5"/>`;
      }
      return `${gap}<line ${common} stroke="${doorColour(
        opening,
      )}" stroke-width="6" stroke-linecap="square"/>`;
    }).join("");
    const stairPolygon = stair?.polygon?.map(point) ?? [];
    let stairMarkup = "";
    if (stairPolygon.length >= 4) {
      const stairBox = polygonBounds(stairPolygon);
      const arrowX = (stairBox.minX + stairBox.maxX) / 2;
      const arrowStartY = stairBox.maxY - (stairBox.maxY - stairBox.minY) * 0.18;
      const arrowEndY = stairBox.minY + (stairBox.maxY - stairBox.minY) * 0.18;
      stairMarkup = `
        <polygon points="${pointAttribute(stairPolygon)}" fill="#fafaf9"
          stroke="#57534e" stroke-width="${Math.max(3, 100 * scale)}"/>
        <line x1="${arrowX}" y1="${arrowStartY}" x2="${arrowX}" y2="${arrowEndY}"
          stroke="#1d5b4a" stroke-width="3"/>
        <polygon points="${arrowX},${arrowEndY} ${arrowX - 8},${
          arrowEndY + 12
        } ${arrowX + 8},${arrowEndY + 12}" fill="#1d5b4a"/>
        <text x="${arrowX}" y="${
          (stairBox.minY + stairBox.maxY) / 2
        }" text-anchor="middle" class="stair-label">TREPPE ↑</text>`;
    }
    const labels = floor.rooms.map((room) => {
      const center = point(roomLabelPoint(room, stair?.polygon ?? null));
      return `<text x="${center[0]}" y="${center[1] - 4}" text-anchor="middle"
          class="room-label">${escapeXml(room.name)}
        <tspan x="${center[0]}" dy="20" class="area-label">ca. ${Number(
          room.area_m2,
        ).toFixed(1)} m²</tspan>
      </text>`;
    }).join("");
    return `
      <text x="${originX}" y="78" class="floor-title">${escapeXml(
        displayFloorName(document, floor),
      )}</text>
      ${roomFills}
      ${walls}
      ${openings}
      ${stairMarkup}
      ${labels}`;
  }).join("");
  const commerciallyEligible = document.wordpress_eligible === true
    && document.rights.wordpress_eligible === true
    && document.rights.usage_scope === "commercial_generator";
  const footer = commerciallyEligible
    ? options.mandatoryLabel
      || "Geprüfter Grundrissvorschlag – keine genehmigungsfähige Architekturplanung."
    : "INTERNAL REVIEW – NOT FOR CUSTOMER DELIVERY";
  const requestId = options.requestId ? ` · Anfrage ${options.requestId}` : "";
  return `<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}"
      viewBox="0 0 ${width} ${height}">
    <rect width="100%" height="100%" fill="#ffffff"/>
    <style>
      text { font-family: "DejaVu Sans", sans-serif; fill: #1c1917; }
      .floor-title { font-size: 28px; font-weight: 700; }
      .room-label { font-size: 16px; font-weight: 700; paint-order: stroke;
        stroke: #fff; stroke-width: 4px; stroke-linejoin: round; }
      .area-label { font-size: 12px; font-weight: 400; fill: #64748b; }
      .stair-label { font-size: 12px; font-weight: 700; fill: #1d5b4a;
        paint-order: stroke; stroke: #fff; stroke-width: 3px; }
      .footer { font-size: 17px; font-weight: 700; fill: ${
        commerciallyEligible ? "#57534e" : "#7c2d12"
      }; }
      .reference { font-size: 12px; fill: #78716c; }
    </style>
    ${floorMarkup}
    <line x1="70" y1="790" x2="1530" y2="790" stroke="#d6d3d1"/>
    <text x="70" y="830" class="footer">${escapeXml(footer)}</text>
    <text x="70" y="865" class="reference">Referenz: ${escapeXml(
      documentReferenceId(document),
    )} · Revision ${document.revision} · Geometrie ${document.geometry_hash}${escapeXml(
      requestId,
    )}</text>
  </svg>`;
}

function floorArea(floor: CorrectionFloor | undefined) {
  if (!floor) return 0;
  return floor.rooms.reduce(
    (sum, room) => sum + Number(room.area_m2 || 0),
    0,
  );
}

function documentToVariant(
  document: CorrectionDocument,
  brief: HouseBrief,
): PlanVariant {
  const floors = document.floors.map((floor) => {
    const box = polygonBounds(floor.footprint);
    const rooms: PlannedRoom[] = floor.rooms.map((room) => {
      const roomBox = polygonBounds(room.polygon);
      const centerX = (roomBox.minX + roomBox.maxX) / 2;
      const centerY = (roomBox.minY + roomBox.maxY) / 2;
      return {
        id: room.id,
        name: room.name,
        kind: room.kind,
        x: roomBox.minX,
        y: roomBox.minY,
        width: roomBox.maxX - roomBox.minX,
        height: roomBox.maxY - roomBox.minY,
        area: room.area_m2,
        side: centerX < (box.minX + box.maxX) / 2 ? "left" : "right",
        zone: room.kind === "circulation"
          || room.kind === "wet"
          || room.kind === "service"
          ? "core"
          : centerY < (box.minY + box.maxY) / 2
            ? "street"
            : "garden",
        polygon: room.polygon.map(([x, y]) => ({ x, y })),
      };
    });
    return {
      floor: floor.level,
      name: displayFloorName(document, floor),
      rooms,
      hasStair: Boolean(document.shared_stair_core),
      stair: document.shared_stair_core?.geometry ?? null,
      layoutMode: "wall-stair" as const,
      stairPath: document.shared_stair_core?.path.map(([x, y]) => ({ x, y })),
      stairType: "straight" as const,
      referenceFootprint: {
        x: box.minX,
        y: box.minY,
        width: box.maxX - box.minX,
        height: box.maxY - box.minY,
      },
      referenceFootprintPolygon: floor.footprint.map(([x, y]) => ({ x, y })),
      referenceLayoutId: documentReferenceId(document),
    };
  });
  const stairBox = document.shared_stair_core
    ? polygonBounds(document.shared_stair_core.polygon)
    : null;
  return {
    id: `${documentReferenceId(document)}-revision-${document.revision}`,
    name: "Korrigierte Referenz",
    description:
      "Manuell korrigierte, millimetergenaue Referenz mit verknüpften Wänden, Öffnungen und gemeinsamem Treppenkern.",
    floors,
    storeyType: document.building.storey_type,
    stairCore: document.shared_stair_core && stairBox
      ? {
          id: document.shared_stair_core.id,
          footprint: {
            x: stairBox.minX,
            y: stairBox.minY,
            width: stairBox.maxX - stairBox.minX,
            height: stairBox.maxY - stairBox.minY,
          },
          path: document.shared_stair_core.path.map(([x, y]) => ({ x, y })),
          geometry: document.shared_stair_core.geometry,
        }
      : null,
    canonicalGeometrySha256: document.geometry_hash,
    score: 100,
    checks: [
      {
        label: "Manuell korrigierte Millimetergeometrie ist intern freigegeben",
        passed: true,
      },
      {
        label: "Rechtefreigabe für Kundenversand ist dokumentiert",
        passed: document.wordpress_eligible,
      },
    ],
    metrics: {
      footprintWidthM: document.building.footprint_width_mm / 1000,
      footprintDepthM: document.building.footprint_depth_mm / 1000,
      plannedAreaM2: brief.area,
      referenceProfile:
        `${documentReferenceId(document)} / Korrektur ${document.revision}`,
      groundFloorAreaM2: floorArea(document.floors[0]),
      upperFloorAreaM2: floorArea(document.floors[1]),
      referenceLayoutId: documentReferenceId(document),
      storeyType: document.building.storey_type,
    },
  };
}

export function correctedFloorplanForBrief(brief: HouseBrief) {
  const record = selectApprovedFloorplan(brief);
  if (!record) return null;
  const document = record.document as CorrectionDocument;
  const wordpressEligible = document.wordpress_eligible === true
    && document.rights.wordpress_eligible === true
    && document.rights.usage_scope === "commercial_generator";
  return {
    document,
    variant: documentToVariant(document, brief),
    wordpressEligible,
    distributionScope: wordpressEligible
      ? "commercial_generator"
      : "internal_review_only",
  } as const;
}

export async function renderCorrectedFloorplanArtifacts(
  document: CorrectionDocument,
  options: { requestId?: string; mandatoryLabel?: string } = {},
) {
  const svg = Buffer.from(renderCorrectedFloorplanSvg(document, options), "utf8");
  const jpeg = await sharp(svg, {
    density: 192,
    limitInputPixels: 32_000_000,
  })
    .flatten({ background: "#ffffff" })
    .resize({ width: JPEG_WIDTH, fit: "inside" })
    .jpeg({
      quality: 90,
      chromaSubsampling: "4:4:4",
      progressive: true,
      mozjpeg: true,
    })
    .toBuffer();
  const guide = await sharp(svg, {
    density: 192,
    limitInputPixels: 32_000_000,
  })
    .flatten({ background: "#ffffff" })
    .resize(1024, 1024, { fit: "contain", background: "#ffffff" })
    .png()
    .toBuffer();
  if (
    jpeg.length < 100
    || jpeg.length > MAX_JPEG_BYTES
    || jpeg[0] !== 0xff
    || jpeg[1] !== 0xd8
    || jpeg[2] !== 0xff
    || guide.length < 100
    || guide[0] !== 0x89
    || guide.subarray(1, 4).toString("ascii") !== "PNG"
  ) {
    throw new Error("Die korrigierten Grundriss-Artefakte sind ungültig.");
  }
  return { jpeg, guide };
}
