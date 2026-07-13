export type TrainingPoint = [number, number];

export type TrainingRoom = {
  label: string;
  polygon: TrainingPoint[];
  area_m2?: number;
  area_ratio?: number;
  floor_level?: string;
  room_id?: string;
  room_ids?: string[];
  source_id?: string;
};

export type TrainingElementType = "door" | "window" | "stairs";

export type TrainingElement = {
  type: TrainingElementType;
  points: TrainingPoint[];
  label?: string;
  floor_level?: string;
  room_id?: string;
  room_ids?: string[];
  source_id?: string;
};

export type FloorplanTrainingSample = {
  image: string;
  project_id?: string;
  house_type?: string;
  package_status?: string;
  floor_level?: string;
  has_cellar?: boolean;
  rooms: TrainingRoom[];
  elements: TrainingElement[];
  source: {
    adapter: "our-simplifier" | "cubicasa5k";
    path: string;
    schema_version?: string;
    dataset_version?: string;
  };
};

export type RawTrainingRoom = {
  label?: unknown;
  combined_label?: unknown;
  combinedRoomLabel?: unknown;
  room_label?: unknown;
  polygon?: unknown;
  points?: unknown;
  room_id?: unknown;
  room_ids?: unknown;
  roomId?: unknown;
  id?: unknown;
  floor_level?: unknown;
  floorLevel?: unknown;
  area_m2?: unknown;
  areaM2?: unknown;
  area_ratio?: unknown;
  areaRatio?: unknown;
};

export type RawTrainingElement = {
  type?: unknown;
  label?: unknown;
  points?: unknown;
  polygon?: unknown;
  room_id?: unknown;
  room_ids?: unknown;
  roomId?: unknown;
  id?: unknown;
  floor_level?: unknown;
  floorLevel?: unknown;
};

export function isTrainingElementType(value: unknown): value is TrainingElementType {
  return value === "door" || value === "window" || value === "stairs";
}

export function normalizePoint(value: unknown): TrainingPoint | null {
  if (Array.isArray(value) && value.length >= 2) {
    const x = Number(value[0]);
    const y = Number(value[1]);
    return Number.isFinite(x) && Number.isFinite(y) ? [x, y] : null;
  }

  if (value && typeof value === "object") {
    const record = value as Record<string, unknown>;
    const x = Number(record.x);
    const y = Number(record.y);
    return Number.isFinite(x) && Number.isFinite(y) ? [x, y] : null;
  }

  return null;
}

export function normalizePointList(value: unknown): TrainingPoint[] {
  if (!Array.isArray(value)) return [];

  return value
    .map((point) => normalizePoint(point))
    .filter((point): point is TrainingPoint => point !== null);
}

export function optionalNumber(value: unknown): number | undefined {
  const number = Number(value);
  return Number.isFinite(number) ? number : undefined;
}

export function optionalString(value: unknown): string | undefined {
  return typeof value === "string" && value.trim() ? value.trim() : undefined;
}

export function optionalStringArray(value: unknown): string[] | undefined {
  if (!Array.isArray(value)) return undefined;

  const values = value
    .map((entry) => optionalString(entry))
    .filter((entry): entry is string => Boolean(entry));

  return values.length ? values : undefined;
}
