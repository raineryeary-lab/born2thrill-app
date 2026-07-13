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
  optionalStringArray,
} from "./schema";

type SimplifierAnnotations = {
  project_id?: unknown;
  house_type?: unknown;
  package_status?: unknown;
  schema_version?: unknown;
  annotations?: RawTrainingRoom[];
  rooms?: RawTrainingRoom[];
  room_polygons?: RawTrainingRoom[];
  elements?: RawTrainingElement[];
  markers?: RawTrainingElement[];
  doors?: RawTrainingElement[];
  windows?: RawTrainingElement[];
  stairs?: RawTrainingElement[];
};

type SimplifierDatasetFloor = {
  floor_level?: unknown;
  rooms?: RawTrainingRoom[];
  annotations?: RawTrainingRoom[];
  elements?: RawTrainingElement[];
};

type SimplifierDatasetProject = {
  project_id?: unknown;
  house_type?: unknown;
  package_status?: unknown;
  schema_version?: unknown;
  floors?: SimplifierDatasetFloor[];
};

type SimplifierDataset = {
  dataset_version?: unknown;
  source_schema?: unknown;
  projects?: SimplifierDatasetProject[];
};

function asArray<T>(value: T[] | undefined): T[] {
  return Array.isArray(value) ? value : [];
}

async function readJsonFile<T>(filePath: string): Promise<T> {
  const raw = await readFile(filePath, "utf8");
  return JSON.parse(raw) as T;
}

function floorLevelFor(value: unknown, fallback?: string) {
  return optionalString(value) ?? fallback;
}

function roomIdsFor(room: RawTrainingRoom) {
  const roomIds = optionalStringArray(room.room_ids);
  if (roomIds) return roomIds;

  const singleRoomId = optionalString(room.room_id ?? room.roomId);
  return singleRoomId ? [singleRoomId] : undefined;
}

function normalizeRoom(room: RawTrainingRoom, fallbackFloorLevel?: string) {
  const polygon = normalizePointList(room.polygon ?? room.points);
  if (polygon.length < 3) return null;

  const room_id = optionalString(room.room_id ?? room.roomId);

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
    floor_level: floorLevelFor(room.floor_level ?? room.floorLevel, fallbackFloorLevel),
    room_id,
    room_ids: roomIdsFor(room),
    source_id: optionalString(room.id ?? room.room_id ?? room.roomId),
  };
}

function normalizeElement(
  element: RawTrainingElement,
  fallbackType?: "door" | "window" | "stairs",
  fallbackFloorLevel?: string,
) {
  const type = isTrainingElementType(element.type) ? element.type : fallbackType;
  if (!type) return null;

  const points = normalizePointList(element.points ?? element.polygon);
  if (points.length < 2) return null;

  return {
    type,
    points,
    label: optionalString(element.label),
    floor_level: floorLevelFor(element.floor_level ?? element.floorLevel, fallbackFloorLevel),
    room_id: optionalString(element.room_id ?? element.roomId),
    room_ids: optionalStringArray(element.room_ids),
    source_id: optionalString(element.id ?? element.room_id ?? element.roomId),
  };
}

function imagePathForPackage(projectPath: string) {
  return path.join(projectPath, "original_preview.png");
}

function groupByFloorLevel<T extends { floor_level?: string }>(items: T[]) {
  return items.reduce((groups, item) => {
    const floorLevel = item.floor_level ?? "unknown";
    const existing = groups.get(floorLevel) ?? [];
    existing.push(item);
    groups.set(floorLevel, existing);
    return groups;
  }, new Map<string, T[]>());
}

function hasCellar(floorLevels: Iterable<string>) {
  return Array.from(floorLevels).some((floorLevel) => floorLevel === "basement");
}

function sampleForFloor(params: {
  image: string;
  projectPath: string;
  projectId?: string;
  houseType?: string;
  packageStatus?: string;
  schemaVersion?: string;
  datasetVersion?: string;
  floorLevel: string;
  hasCellar: boolean;
  rooms: ReturnType<typeof normalizeRoom>[];
  elements: ReturnType<typeof normalizeElement>[];
}): FloorplanTrainingSample {
  return {
    image: params.image,
    project_id: params.projectId,
    house_type: params.houseType,
    package_status: params.packageStatus,
    floor_level: params.floorLevel,
    has_cellar: params.hasCellar,
    rooms: params.rooms.filter((room): room is NonNullable<typeof room> => room !== null),
    elements: params.elements.filter((element): element is NonNullable<typeof element> => element !== null),
    source: {
      adapter: "our-simplifier",
      path: params.projectPath,
      schema_version: params.schemaVersion,
      dataset_version: params.datasetVersion,
    },
  };
}

export async function import_our_simplifier_package_floors(projectPath: string): Promise<FloorplanTrainingSample[]> {
  const annotationsPath = path.join(projectPath, "annotations.json");
  const annotations = await readJsonFile<SimplifierAnnotations>(annotationsPath);
  const projectId = optionalString(annotations.project_id);
  const houseType = optionalString(annotations.house_type);
  const packageStatus = optionalString(annotations.package_status);
  const schemaVersion = optionalString(annotations.schema_version);

  const rawRooms = [
    ...asArray(annotations.annotations),
    ...asArray(annotations.rooms),
    ...asArray(annotations.room_polygons),
  ];
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

  const roomsByFloor = groupByFloorLevel(rooms);
  const elementsByFloor = groupByFloorLevel(elements);
  const floorLevels = new Set([...roomsByFloor.keys(), ...elementsByFloor.keys()]);
  const cellar = hasCellar(floorLevels);

  return Array.from(floorLevels).map((floorLevel) => sampleForFloor({
    image: imagePathForPackage(projectPath),
    projectPath,
    projectId,
    houseType,
    packageStatus,
    schemaVersion,
    floorLevel,
    hasCellar: cellar,
    rooms: roomsByFloor.get(floorLevel) ?? [],
    elements: elementsByFloor.get(floorLevel) ?? [],
  }));
}

export async function import_our_simplifier_package(projectPath: string): Promise<FloorplanTrainingSample> {
  const samples = await import_our_simplifier_package_floors(projectPath);
  const firstSample = samples[0];
  if (!firstSample) {
    throw new Error(`No Simplifier training floors found in ${projectPath}`);
  }

  return firstSample;
}

export async function import_our_simplifier_dataset(datasetPath: string): Promise<FloorplanTrainingSample[]> {
  const dataset = await readJsonFile<SimplifierDataset>(datasetPath);
  const datasetVersion = optionalString(dataset.dataset_version);
  const sourceSchema = optionalString(dataset.source_schema);

  return asArray(dataset.projects).flatMap((project) => {
    const projectId = optionalString(project.project_id);
    const houseType = optionalString(project.house_type);
    const packageStatus = optionalString(project.package_status);
    const schemaVersion = optionalString(project.schema_version) ?? sourceSchema;
    const floors = asArray(project.floors);
    const floorLevels = floors
      .map((floor) => optionalString(floor.floor_level))
      .filter((floorLevel): floorLevel is string => Boolean(floorLevel));
    const cellar = hasCellar(floorLevels);

    return floors.map((floor) => {
      const floorLevel = optionalString(floor.floor_level) ?? "unknown";
      const rooms = [
        ...asArray(floor.annotations),
        ...asArray(floor.rooms),
      ].map((room) => normalizeRoom(room, floorLevel));
      const elements = asArray(floor.elements).map((element) => normalizeElement(element, undefined, floorLevel));

      return sampleForFloor({
        image: "privacy-safe:no-preview",
        projectPath: datasetPath,
        projectId,
        houseType,
        packageStatus,
        schemaVersion,
        datasetVersion,
        floorLevel,
        hasCellar: cellar,
        rooms,
        elements,
      });
    });
  });
}
