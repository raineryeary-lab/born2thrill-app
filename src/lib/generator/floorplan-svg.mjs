const COLORS = {
  living: "#d9f7e5",
  sleeping: "#f5f1e8",
  wet: "#dcecff",
  service: "#fff1bd",
  flex: "#f4f1ec",
  circulation: "#ece9e2",
};

const CRITICAL_CHECK_PATTERN = /reale, annotierte|referenzlayout|raumprogramm|trepp|kollision|raumgeometr|türen|fenster/i;

const SOURCE_STAIR_REVIEW_CHECK_PATTERN =
  /^Quellreferenz [A-Za-z0-9._-]+: EG-\/OG-Treppenkern muss vor Kundennutzung gemeinsam bestätigt werden$/u;
const ROOM_PROGRAM_REVIEW_CHECK =
  "Angefordertes Raumprogramm ist in der Referenz vollständig vorhanden";

function number(value) {
  return Number.isFinite(value) ? Number(value.toFixed(2)) : 0;
}

function escapeXml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&apos;");
}

function pointsAttribute(points) {
  return points.map((point) => `${number(point.x)},${number(point.y)}`).join(" ");
}

function roomPoints(room) {
  if (Array.isArray(room.polygon) && room.polygon.length >= 3) return room.polygon;
  return [
    { x: room.x, y: room.y },
    { x: room.x + room.width, y: room.y },
    { x: room.x + room.width, y: room.y + room.height },
    { x: room.x, y: room.y + room.height },
  ];
}

function bounds(points) {
  const xs = points.map((point) => point.x);
  const ys = points.map((point) => point.y);
  return {
    x: Math.min(...xs),
    y: Math.min(...ys),
    width: Math.max(...xs) - Math.min(...xs),
    height: Math.max(...ys) - Math.min(...ys),
  };
}

function snapAxis(values, tolerance = 10) {
  const groups = [];
  [...values].sort((left, right) => left - right).forEach((value) => {
    const group = groups.find((candidate) => {
      const center = candidate.reduce((sum, item) => sum + item, 0) / candidate.length;
      return Math.abs(center - value) <= tolerance;
    });
    if (group) group.push(value);
    else groups.push([value]);
  });
  const centers = groups.map((group) =>
    group.reduce((sum, value) => sum + value, 0) / group.length
  );
  return (value) => centers.reduce(
    (best, center) => Math.abs(center - value) < Math.abs(best - value) ? center : best,
    centers[0] ?? value,
  );
}

function normalizedFloor(plan) {
  const original = plan.rooms.map((room) => ({ room, points: roomPoints(room) }));
  const snapX = snapAxis(original.flatMap((entry) => entry.points.map((point) => point.x)));
  const snapY = snapAxis(original.flatMap((entry) => entry.points.map((point) => point.y)));
  const rooms = original.map(({ room, points }) => ({
    room,
    points: points.map((point) => ({ x: snapX(point.x), y: snapY(point.y) })),
  }));
  const allPoints = rooms.flatMap((entry) => entry.points);
  const footprint = plan.referenceFootprint ?? bounds(allPoints);
  const footprintPolygon = Array.isArray(plan.referenceFootprintPolygon)
    && plan.referenceFootprintPolygon.length >= 3
    ? plan.referenceFootprintPolygon
    : [
        { x: footprint.x, y: footprint.y },
        { x: footprint.x + footprint.width, y: footprint.y },
        { x: footprint.x + footprint.width, y: footprint.y + footprint.height },
        { x: footprint.x, y: footprint.y + footprint.height },
      ];
  const floorArea = plan.rooms.reduce((sum, room) => sum + Number(room.area || 0), 0);
  const pixelArea = rooms.reduce((sum, entry) => {
    const box = bounds(entry.points);
    return sum + box.width * box.height;
  }, 0);
  const pixelsPerMeter = Math.sqrt(pixelArea / Math.max(floorArea, 1));
  return {
    rooms,
    footprint,
    footprintPolygon,
    innerWallPx: Math.max(2.5, Math.min(5, pixelsPerMeter * 0.1)),
    outerWallPx: Math.max(8, Math.min(15, pixelsPerMeter * 0.35)),
  };
}

function stairMarkup(plan) {
  const path = Array.isArray(plan.stairPath) ? plan.stairPath : [];
  if (path.length < 2) return "";
  const width = Math.max(28, Number(plan.stairWidthPx) || 42);
  const end = path.at(-1);
  const previous = path.at(-2);
  const dx = end.x - previous.x;
  const dy = end.y - previous.y;
  const length = Math.max(1, Math.hypot(dx, dy));
  const ux = dx / length;
  const uy = dy / length;
  const nx = -uy;
  const ny = ux;
  const arrowSize = 10;
  const baseX = end.x - ux * arrowSize;
  const baseY = end.y - uy * arrowSize;
  const arrow = [
    end,
    { x: baseX + nx * arrowSize * 0.55, y: baseY + ny * arrowSize * 0.55 },
    { x: baseX - nx * arrowSize * 0.55, y: baseY - ny * arrowSize * 0.55 },
  ];
  return `
    <g class="stairs">
      <polyline points="${pointsAttribute(path)}" fill="none" stroke="#57534e" stroke-width="${number(width + 4)}" stroke-linejoin="miter" stroke-linecap="butt"/>
      <polyline points="${pointsAttribute(path)}" fill="none" stroke="#fafaf9" stroke-width="${number(width)}" stroke-linejoin="miter" stroke-linecap="butt"/>
      <polyline points="${pointsAttribute(path)}" fill="none" stroke="#1d5b4a" stroke-width="3" stroke-linejoin="miter" stroke-linecap="butt"/>
      <polygon points="${pointsAttribute(arrow)}" fill="#1d5b4a"/>
    </g>`;
}

function openingMarkup(element, wallWidth) {
  if (!Array.isArray(element.points) || element.points.length < 2) return "";
  const start = element.points[0];
  const end = element.points[1];
  const length = Math.hypot(end.x - start.x, end.y - start.y);
  if (length < 2) return "";
  const common = `x1="${number(start.x)}" y1="${number(start.y)}" x2="${number(end.x)}" y2="${number(end.y)}"`;
  if (element.type === "window") {
    return `<g><line ${common} stroke="#fff" stroke-width="${number(wallWidth + 3)}"/><line ${common} stroke="#12aee2" stroke-width="4"/></g>`;
  }
  if (element.type !== "door") return "";
  const dx = (end.x - start.x) / length;
  const dy = (end.y - start.y) / length;
  const leaf = { x: start.x - dy * length, y: start.y + dx * length };
  return `<g>
    <line ${common} stroke="#fff" stroke-width="${number(wallWidth + 3)}"/>
    <line x1="${number(start.x)}" y1="${number(start.y)}" x2="${number(leaf.x)}" y2="${number(leaf.y)}" stroke="#57534e" stroke-width="2"/>
    <path d="M ${number(end.x)} ${number(end.y)} Q ${number(leaf.x)} ${number(leaf.y)} ${number(start.x)} ${number(start.y)}" fill="none" stroke="#a8a29e" stroke-width="1.3"/>
  </g>`;
}

function floorMarkup(plan, originX, originY, targetWidth, targetHeight) {
  const geometry = normalizedFloor(plan);
  const source = geometry.footprint;
  const scale = Math.min(
    targetWidth / Math.max(source.width, 1),
    targetHeight / Math.max(source.height, 1),
  );
  const offsetX = originX + (targetWidth - source.width * scale) / 2 - source.x * scale;
  const offsetY = originY + (targetHeight - source.height * scale) / 2 - source.y * scale;
  const transform = `translate(${number(offsetX)} ${number(offsetY)}) scale(${number(scale)})`;
  const roomFills = geometry.rooms.map(({ room, points }) =>
    `<polygon points="${pointsAttribute(points)}" fill="${COLORS[room.kind] ?? COLORS.flex}"/>`
  ).join("");
  const innerWalls = geometry.rooms.map(({ points }) =>
    `<polygon points="${pointsAttribute(points)}" fill="none" stroke="#57534e" stroke-width="${number(geometry.innerWallPx)}" stroke-linejoin="miter"/>`
  ).join("");
  const labels = geometry.rooms.map(({ room, points }) => {
    const box = bounds(points);
    const centerX = box.x + box.width / 2;
    const centerY = box.y + box.height / 2;
    const label = escapeXml(room.name);
    const area = Number.isFinite(Number(room.area)) ? `${Math.round(Number(room.area))} m²` : "";
    return `<text x="${number(centerX)}" y="${number(centerY - 2)}" text-anchor="middle" class="room-label">
      <tspan x="${number(centerX)}">${label}</tspan>
      <tspan x="${number(centerX)}" dy="18" class="area-label">${escapeXml(area)}</tspan>
    </text>`;
  }).join("");
  const openings = (plan.referenceElements ?? []).map((element) =>
    openingMarkup(element, geometry.outerWallPx)
  ).join("");
  return `
    <g transform="${transform}">
      ${roomFills}
      ${innerWalls}
      <polygon points="${pointsAttribute(geometry.footprintPolygon)}"
        fill="none" stroke="#1c1917" stroke-width="${number(geometry.outerWallPx)}" stroke-linejoin="miter"/>
      ${openings}
      ${stairMarkup(plan)}
      ${labels}
    </g>`;
}

export function renderFloorplanSvg(variant, options = {}) {
  const floors = Array.isArray(variant?.floors) ? variant.floors.slice(0, 2) : [];
  if (!floors.length) throw new Error("Der ausgewählte Grundriss enthält keine Etagen.");
  const width = 1600;
  const height = 900;
  const panelWidth = floors.length === 1 ? 1040 : 740;
  const startX = floors.length === 1 ? 280 : 45;
  const gap = floors.length === 1 ? 0 : 70;
  const floorTop = 120;
  const floorHeight = 650;
  const floorSections = floors.map((floor, index) => {
    const x = startX + index * (panelWidth + gap);
    return `
      <text x="${number(x)}" y="78" class="floor-title">${escapeXml(floor.name)}</text>
      <text x="${number(x)}" y="105" class="north">N ↑</text>
      ${floorMarkup(floor, x, floorTop, panelWidth, floorHeight)}`;
  }).join("");
  const reference = escapeXml(variant.metrics?.referenceLayoutId || "Referenzauswahl");
  const requestId = escapeXml(options.requestId || "");
  const mandatory = escapeXml(
    options.mandatoryLabel || "Schematischer Konzeptvorschlag – keine Architekturplanung.",
  );
  return `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="${width}" height="${height}" viewBox="0 0 ${width} ${height}">
  <rect width="1600" height="900" fill="#f8f7f4"/>
  <style>
    text { font-family: Arial, Helvetica, sans-serif; fill: #1c1917; }
    .floor-title { font-size: 28px; font-weight: 700; }
    .north { font-size: 15px; fill: #64748b; }
    .room-label { font-size: 15px; font-weight: 700; paint-order: stroke; stroke: #fff; stroke-width: 4px; stroke-linejoin: round; }
    .area-label { font-size: 12px; font-weight: 400; fill: #64748b; }
    .footer { font-size: 15px; fill: #57534e; }
    .reference { font-size: 12px; fill: #78716c; }
  </style>
  ${floorSections}
  <line x1="45" y1="805" x2="1555" y2="805" stroke="#d6d3d1"/>
  <text x="45" y="840" class="footer">${mandatory}</text>
  <text x="45" y="870" class="reference">Referenz: ${reference}${requestId ? ` · Anfrage: ${requestId}` : ""}</text>
</svg>`;
}

export function assertSafeGeneratedSvg(svg) {
  const lower = String(svg).toLowerCase();
  const withoutStandardNamespace = lower.replace(
    'xmlns="http://www.w3.org/2000/svg"',
    "",
  );
  if (!lower.includes("<svg") || lower.length < 500 || lower.length > 1_500_000) {
    throw new Error("Der erzeugte Grundriss ist unvollständig.");
  }
  for (const forbidden of [
    "<script",
    "<foreignobject",
    "<iframe",
    "<!doctype",
    "<!entity",
    "javascript:",
    "onload=",
    "onerror=",
  ]) {
    if (lower.includes(forbidden)) {
      throw new Error("Der erzeugte Grundriss enthält nicht erlaubte SVG-Inhalte.");
    }
  }
  if (
    /\son[a-z][a-z0-9:.-]*\s*=|(?:href|xlink:href)\s*=|url\s*\(|@import|<\?xml-stylesheet|<\s*(?:a|animate|animatemotion|animatetransform|audio|embed|feimage|image|link|object|set|use|video)\b/i.test(lower)
  ) {
    throw new Error("Der erzeugte Grundriss enthält nicht erlaubte SVG-Inhalte.");
  }
  if (withoutStandardNamespace.includes("http://") || withoutStandardNamespace.includes("https://")) {
    throw new Error("Der erzeugte Grundriss enthält nicht erlaubte SVG-Inhalte.");
  }
  return svg;
}

export function floorplanQuality(variant) {
  const failedChecks = Array.isArray(variant?.checks)
    ? variant.checks.filter((check) => !check.passed).map((check) => String(check.label))
    : [];
  return {
    failedChecks,
    criticalFailures: failedChecks.filter((label) => CRITICAL_CHECK_PATTERN.test(label)),
  };
}

export function customerFacingQualityPassed(quality) {
  return Array.isArray(quality?.criticalFailures)
    && quality.criticalFailures.length === 0;
}

export function candidateMayEnterManualReview(quality) {
  return Array.isArray(quality?.criticalFailures)
    && quality.criticalFailures.every((label) =>
      String(label) === ROOM_PROGRAM_REVIEW_CHECK
      || SOURCE_STAIR_REVIEW_CHECK_PATTERN.test(String(label))
    );
}

export function selectQualityVariant(variants) {
  return [...variants].sort((left, right) => {
    const leftQuality = floorplanQuality(left);
    const rightQuality = floorplanQuality(right);
    return leftQuality.criticalFailures.length - rightQuality.criticalFailures.length
      || leftQuality.failedChecks.length - rightQuality.failedChecks.length
      || Number(right.score || 0) - Number(left.score || 0);
  })[0] ?? null;
}
