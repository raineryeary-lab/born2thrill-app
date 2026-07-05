import { readFile } from "node:fs/promises";
import path from "node:path";

import {
  FloorplanTrainingSample,
  RawTrainingElement,
  RawTrainingRoom,
  isTrainingElementType,
  normalizePointList,
  optionalNumber,
  optionalString,
} from "./schema";

type SimplifierAnnotations = {
  rooms?: RawTrainingRoom[];
  room_polygons?: RawTrainingRoom[];
  elements?: RawTrainingElement[];
  markers?: RawTrainingElement[];
  doors?: RawTrainingElement[];
  windows?: RawTrainingElement[];
  stairs?: RawTrainingElement[];
};

function asArray<T>(value: T[] | undefined): T[] {
  return Array.isArray(value) ? value : [];
}

async function readJsonFile<T>(filePath: string): Promise<T> {
  const raw = await readFile(filePath, "utf8");
  return JSON.parse(raw) as T;
}

function normalizeRoom(room: RawTrainingRoom) {
  const polygon = normalizePointList(room.polygon ?? room.points);
  if (polygon.length < 3) return null;

  return {
    label:
      optionalString(room.combined_label)
      ?? optionalString(room.combinedRoomLabel)
      ?? optionalString(room.label)
      ?? optionalString(room.room_label)
      ?? "Unbenannter Raum",
    polygon,
    area_m2: optionalNumber(room.area_m2 ?? room.areaM2),
    area_ratio: optionalNumber(room.area_ratio ?? room.areaRatio),
    source_id: optionalString(room.room_id ?? room.roomId ?? room.id),
  };
}

function normalizeElement(element: RawTrainingElement, fallbackType?: "door" | "window" | "stairs") {
  const type = isTrainingElementType(element.type) ? element.type : fallbackType;
  if (!type) return null;

  const points = normalizePointList(element.points ?? element.polygon);
  if (points.length < 2) return null;

  return {
    type,
    points,
    label: optionalString(element.label),
    source_id: optionalString(element.room_id ?? element.roomId ?? element.id),
  };
}

function imagePathForPackage(projectPath: string) {
  return path.join(projectPath, "original_preview.png");
}

export async function import_our_simplifier_package(projectPath: string): Promise<FloorplanTrainingSample> {
  const annotationsPath = path.join(projectPath, "annotations.json");
  const annotations = await readJsonFile<SimplifierAnnotations>(annotationsPath);

  const rawRooms = [...asArray(annotations.rooms), ...asArray(annotations.room_polygons)];
  const rooms = rawRooms
    .map((room) => normalizeRoom(room))
    .filter((room): room is NonNullable<typeof room> => room !== null);

  const rawElements: Array<[RawTrainingElement, "door" | "window" | "stairs" | undefined]> = [
    ...asArray(annotations.elements).map((element): [RawTrainingElement, undefined] => [element, undefined]),
    ...asArray(annotations.markers).map((element): [RawTrainingElement, undefined] => [element, undefined]),
    ...asArray(annotations.doors).map((element): [RawTrainingElement, "door"] => [element, "door"]),
    ...asArray(annotations.windows).map((element): [RawTrainingElement, "window"] => [element, "window"]),
    ...asArray(annotations.stairs).map((element): [RawTrainingElement, "stairs"] => [element, "stairs"]),
  ];

  const elements = rawElements
    .map(([element, fallbackType]) => normalizeElement(element, fallbackType))
    .filter((element): element is NonNullable<typeof element> => element !== null);

  return {
    image: imagePathForPackage(projectPath),
    rooms,
    elements,
    source: {
      adapter: "our-simplifier",
      path: projectPath,
    },
  };
}

