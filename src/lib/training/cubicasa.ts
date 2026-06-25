import { readFile } from "node:fs/promises";
import path from "node:path";

import { FloorplanTrainingSample, TrainingElement, TrainingPoint, TrainingRoom } from "./schema";

type SvgNode = {
  tag: string;
  attributes: Record<string, string>;
};

const ROOM_HINTS = [
  "space",
  "room",
  "living",
  "kitchen",
  "bedroom",
  "bath",
  "wc",
  "closet",
  "hall",
  "garage",
  "sauna",
  "laundry",
  "utility",
  "storage",
];

function parseAttributes(raw: string): Record<string, string> {
  const attributes: Record<string, string> = {};
  const attributePattern = /([\w:-]+)\s*=\s*["']([^"']*)["']/g;
  let match: RegExpExecArray | null;

  while ((match = attributePattern.exec(raw)) !== null) {
    attributes[match[1]] = match[2];
  }

  return attributes;
}

function parseSvgNodes(svg: string): SvgNode[] {
  const nodes: SvgNode[] = [];
  const nodePattern = /<\s*(polygon|polyline|line|rect|path)\b([^>]*)>/gi;
  let match: RegExpExecArray | null;

  while ((match = nodePattern.exec(svg)) !== null) {
    nodes.push({
      tag: match[1].toLowerCase(),
      attributes: parseAttributes(match[2]),
    });
  }

  return nodes;
}

function parsePoints(value?: string): TrainingPoint[] {
  if (!value) return [];

  const numbers = value
    .trim()
    .split(/[\s,]+/)
    .map((item) => Number(item))
    .filter((item) => Number.isFinite(item));

  const points: TrainingPoint[] = [];
  for (let index = 0; index < numbers.length - 1; index += 2) {
    points.push([numbers[index], numbers[index + 1]]);
  }

  return points;
}

function pointsFromRect(attributes: Record<string, string>): TrainingPoint[] {
  const x = Number(attributes.x ?? 0);
  const y = Number(attributes.y ?? 0);
  const width = Number(attributes.width);
  const height = Number(attributes.height);
  if (![x, y, width, height].every((item) => Number.isFinite(item)) || width <= 0 || height <= 0) return [];

  return [
    [x, y],
    [x + width, y],
    [x + width, y + height],
    [x, y + height],
  ];
}

function pointsFromLine(attributes: Record<string, string>): TrainingPoint[] {
  const x1 = Number(attributes.x1);
  const y1 = Number(attributes.y1);
  const x2 = Number(attributes.x2);
  const y2 = Number(attributes.y2);
  if (![x1, y1, x2, y2].every((item) => Number.isFinite(item))) return [];

  return [[x1, y1], [x2, y2]];
}

function pointsFromPathData(value?: string): TrainingPoint[] {
  if (!value) return [];

  const tokens = value.match(/[a-zA-Z]|-?\d*\.?\d+(?:e[-+]?\d+)?/g) ?? [];
  const points: TrainingPoint[] = [];
  let cursor: TrainingPoint = [0, 0];
  let command = "";
  let index = 0;

  while (index < tokens.length) {
    const token = tokens[index];
    if (/^[a-zA-Z]$/.test(token)) {
      command = token;
      index += 1;
      continue;
    }

    if (["M", "L", "m", "l"].includes(command) && index + 1 < tokens.length) {
      const x = Number(tokens[index]);
      const y = Number(tokens[index + 1]);
      if (Number.isFinite(x) && Number.isFinite(y)) {
        cursor = command === command.toLowerCase() ? [cursor[0] + x, cursor[1] + y] : [x, y];
        points.push(cursor);
      }
      index += 2;
      continue;
    }

    if (["H", "h"].includes(command)) {
      const x = Number(tokens[index]);
      if (Number.isFinite(x)) {
        cursor = command === "h" ? [cursor[0] + x, cursor[1]] : [x, cursor[1]];
        points.push(cursor);
      }
      index += 1;
      continue;
    }

    if (["V", "v"].includes(command)) {
      const y = Number(tokens[index]);
      if (Number.isFinite(y)) {
        cursor = command === "v" ? [cursor[0], cursor[1] + y] : [cursor[0], y];
        points.push(cursor);
      }
      index += 1;
      continue;
    }

    index += 1;
  }

  return points;
}

function pointsForNode(node: SvgNode): TrainingPoint[] {
  if (node.tag === "polygon" || node.tag === "polyline") return parsePoints(node.attributes.points);
  if (node.tag === "rect") return pointsFromRect(node.attributes);
  if (node.tag === "line") return pointsFromLine(node.attributes);
  if (node.tag === "path") return pointsFromPathData(node.attributes.d);
  return [];
}

function semanticText(attributes: Record<string, string>): string {
  return [
    attributes.id,
    attributes.class,
    attributes["data-name"],
    attributes["data-type"],
    attributes.type,
    attributes.label,
  ]
    .filter(Boolean)
    .join(" ")
    .toLowerCase();
}

function roomLabel(attributes: Record<string, string>): string {
  return attributes["data-name"] || attributes.label || attributes.id || attributes.class || "Unbenannter CubiCasa-Raum";
}

function classifyElement(text: string): TrainingElement["type"] | null {
  if (text.includes("door")) return "door";
  if (text.includes("window")) return "window";
  if (text.includes("stair")) return "stairs";
  return null;
}

function isRoomLike(text: string) {
  return ROOM_HINTS.some((hint) => text.includes(hint));
}

function imagePathForSample(samplePath: string) {
  return path.join(samplePath, "F1_scaled.png");
}

export async function import_cubicasa_sample(samplePath: string): Promise<FloorplanTrainingSample> {
  const svgPath = path.join(samplePath, "model.svg");
  const svg = await readFile(svgPath, "utf8");
  const nodes = parseSvgNodes(svg);
  const rooms: TrainingRoom[] = [];
  const elements: TrainingElement[] = [];

  for (const node of nodes) {
    const points = pointsForNode(node);
    if (points.length < 2) continue;

    const text = semanticText(node.attributes);
    const elementType = classifyElement(text);
    if (elementType) {
      elements.push({
        type: elementType,
        points,
        label: roomLabel(node.attributes),
        source_id: node.attributes.id,
      });
      continue;
    }

    if (points.length >= 3 && isRoomLike(text)) {
      rooms.push({
        label: roomLabel(node.attributes),
        polygon: points,
        source_id: node.attributes.id,
      });
    }
  }

  return {
    image: imagePathForSample(samplePath),
    rooms,
    elements,
    source: {
      adapter: "cubicasa5k",
      path: samplePath,
    },
  };
}

