import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";
import { pathToFileURL } from "node:url";

const DEFAULT_SOURCE = "/Users/raineryeary/Documents/Codex/2026-06-23/fl/work/floorplan-simplifier/exports/floorplan-generator/simplifier-v1";
const DEFAULT_TARGET = path.resolve("data/simplifier-v1");
const DATASET_VERSION = "floorplan-generator-simplifier-v1";
const SOURCE_SCHEMA = "simplifier-annotations-v1";
const KNOWLEDGE_VERSION = "simplifier-knowledge-v1";
const COUNT_FIELDS = ["project_count", "floor_count", "room_count", "element_count"];

function assertEqual(name, actual, wanted) {
  if (actual !== wanted) {
    throw new Error(`${name} mismatch: expected ${wanted}, got ${actual}`);
  }
}

function increment(record, key) {
  record[key] = (record[key] ?? 0) + 1;
}

function sortedRecord(record) {
  return Object.fromEntries(Object.entries(record).sort(([left], [right]) => left.localeCompare(right)));
}

function assertCountRecord(name, value) {
  if (!value || typeof value !== "object" || Array.isArray(value)) {
    throw new Error(`${name} must be an object of non-negative integer counts.`);
  }
  for (const [key, count] of Object.entries(value)) {
    if (!key || !Number.isInteger(count) || count < 0) {
      throw new Error(`${name}.${key || "<empty>"} must be a non-negative integer.`);
    }
  }
}

function assertSameCountRecord(name, actual, wanted) {
  assertCountRecord(name, actual);
  assertCountRecord(`${name}.expected`, wanted);
  const actualJson = JSON.stringify(sortedRecord(actual));
  const wantedJson = JSON.stringify(sortedRecord(wanted));
  if (actualJson !== wantedJson) {
    throw new Error(`${name} mismatch: expected ${wantedJson}, got ${actualJson}`);
  }
}

function normalizedPoint(value) {
  if (!Array.isArray(value) || value.length < 2) return null;
  const x = Number(value[0]);
  const y = Number(value[1]);
  if (!Number.isFinite(x) || !Number.isFinite(y)) return null;
  return [x, y];
}

function polygonArea(points) {
  let total = 0;
  for (let index = 0; index < points.length; index += 1) {
    const next = (index + 1) % points.length;
    total += points[index][0] * points[next][1] - points[next][0] * points[index][1];
  }
  return Math.abs(total) / 2;
}

function validateStructure(dataset) {
  const projects = Array.isArray(dataset.projects) ? dataset.projects : [];
  for (const [projectIndex, project] of projects.entries()) {
    const projectName = project.project_id || `projects[${projectIndex}]`;
    if (!Array.isArray(project.floors) || project.floors.length < 1) {
      throw new Error(`${projectName} must contain at least one floor.`);
    }

    for (const [floorIndex, floor] of project.floors.entries()) {
      const floorName = `${projectName}.floors[${floorIndex}]`;
      if (typeof floor.floor_level !== "string" || !floor.floor_level.trim()) {
        throw new Error(`${floorName}.floor_level must be a non-empty string.`);
      }

      const rooms = [
        ...(Array.isArray(floor.annotations) ? floor.annotations : []),
        ...(Array.isArray(floor.rooms) ? floor.rooms : []),
      ];
      const roomIds = new Set();
      let validRoomCount = 0;
      for (const [roomIndex, room] of rooms.entries()) {
        const roomName = `${floorName}.rooms[${roomIndex}]`;
        const polygon = Array.isArray(room.polygon) ? room.polygon.map(normalizedPoint).filter(Boolean) : [];
        if (polygon.length < 3 || polygonArea(polygon) <= 0) continue;
        validRoomCount += 1;
        for (const id of [room.id, room.room_id, ...(Array.isArray(room.room_ids) ? room.room_ids : [])]) {
          if (typeof id === "string" && id.trim()) roomIds.add(id);
        }
      }
      if (rooms.length && validRoomCount < 1) {
        throw new Error(`${floorName} must contain at least one valid room polygon.`);
      }

      const elements = Array.isArray(floor.elements) ? floor.elements : [];
      for (const [elementIndex, element] of elements.entries()) {
        const elementName = `${floorName}.elements[${elementIndex}]`;
        if (typeof element.type !== "string" || !element.type.trim()) {
          throw new Error(`${elementName}.type must be a non-empty string.`);
        }
        const points = Array.isArray(element.points) ? element.points.map(normalizedPoint).filter(Boolean) : [];
        if (points.length < 2) throw new Error(`${elementName}.points must contain at least two finite points.`);

        const refs = [element.room_id, ...(Array.isArray(element.room_ids) ? element.room_ids : [])]
          .filter((value) => typeof value === "string" && value.trim());
        for (const ref of refs) {
          if (!rooms.length) throw new Error(`${elementName} cannot reference rooms on an incomplete floor.`);
          if (!roomIds.has(ref)) throw new Error(`${elementName} references unknown room ${ref}.`);
        }
      }
    }
  }
}

export function countDataset(dataset) {
  const projects = Array.isArray(dataset.projects) ? dataset.projects : [];
  const floors = projects.flatMap((project) => Array.isArray(project.floors) ? project.floors : []);
  const rooms = floors.flatMap((floor) => [
    ...(Array.isArray(floor.annotations) ? floor.annotations : []),
    ...(Array.isArray(floor.rooms) ? floor.rooms : []),
  ]);
  const elements = floors.flatMap((floor) => Array.isArray(floor.elements) ? floor.elements : []);
  const houseTypes = {};
  const floorLevels = {};

  for (const project of projects) {
    increment(houseTypes, String(project.house_type || "other"));
  }
  for (const floor of floors) {
    increment(floorLevels, String(floor.floor_level || "groundfloor"));
  }

  return {
    project_count: projects.length,
    floor_count: floors.length,
    room_count: rooms.length,
    element_count: elements.length,
    house_types: sortedRecord(houseTypes),
    floor_levels: sortedRecord(floorLevels),
  };
}

export function validateDataset(dataset, manifest, knowledge) {
  assertEqual("dataset_version", dataset.dataset_version, DATASET_VERSION);
  assertEqual("source_schema", dataset.source_schema, SOURCE_SCHEMA);
  assertEqual("manifest.dataset_version", manifest.dataset_version, DATASET_VERSION);
  assertEqual("knowledge.knowledge_version", knowledge.knowledge_version, KNOWLEDGE_VERSION);

  if (dataset.privacy?.local_only !== true) {
    throw new Error("privacy.local_only must be exactly true.");
  }
  if (dataset.privacy?.contains_raw_floorplans !== false) {
    throw new Error("privacy.contains_raw_floorplans must be exactly false.");
  }
  if (dataset.privacy?.contains_customer_names_or_addresses !== false) {
    throw new Error("privacy.contains_customer_names_or_addresses must be exactly false.");
  }

  validateStructure(dataset);

  const counts = countDataset(dataset);
  if (counts.project_count < 1 || counts.floor_count < 1 || counts.room_count < 1) {
    throw new Error("Simplifier dataset must contain at least one project, floor, and room.");
  }
  if (counts.floor_count < counts.project_count) {
    throw new Error("Simplifier dataset cannot contain fewer floors than projects.");
  }

  for (const name of COUNT_FIELDS) {
    assertEqual(`manifest.${name}`, manifest[name], counts[name]);
    assertEqual(`knowledge.basis.${name}`, knowledge.basis?.[name], counts[name]);
  }
  assertSameCountRecord("manifest.house_types", manifest.house_types, counts.house_types);
  assertSameCountRecord("manifest.floor_levels", manifest.floor_levels, counts.floor_levels);
  assertSameCountRecord("knowledge.basis.house_types", knowledge.basis?.house_types, counts.house_types);
  assertSameCountRecord("knowledge.basis.floor_levels", knowledge.basis?.floor_levels, counts.floor_levels);
  assertCountRecord("knowledge.element_counts", knowledge.element_counts);

  return counts;
}

async function readJson(filePath) {
  return JSON.parse(await readFile(filePath, "utf8"));
}

export async function importSimplifierHandoff(sourcePath = DEFAULT_SOURCE, targetPath = DEFAULT_TARGET) {
  const source = path.resolve(sourcePath);
  const target = path.resolve(targetPath);
  const datasetPath = path.join(source, "dataset.json");
  const knowledgePath = path.join(source, "knowledge.json");
  const manifestPath = path.join(source, "manifest.json");

  const dataset = await readJson(datasetPath);
  const knowledge = await readJson(knowledgePath);
  const manifest = await readJson(manifestPath);
  const counts = validateDataset(dataset, manifest, knowledge);

  await mkdir(target, { recursive: true });
  await copyFile(datasetPath, path.join(target, "dataset.json"));
  await copyFile(knowledgePath, path.join(target, "knowledge.json"));
  await copyFile(manifestPath, path.join(target, "manifest.json"));

  const sourceReadme = path.resolve(source, "..", "README.md");
  try {
    await copyFile(sourceReadme, path.join(target, "README.md"));
  } catch {
    await writeFile(path.join(target, "README.md"), "# Simplifier v1 handoff\n\nPrivacy-safe local Floorplan Simplifier handoff.\n");
  }

  return { counts, target };
}

async function main() {
  const source = process.argv[2] ?? DEFAULT_SOURCE;
  const target = process.argv[3] ?? DEFAULT_TARGET;
  const { counts, target: resolvedTarget } = await importSimplifierHandoff(source, target);
  const basementFloors = counts.floor_levels.basement ?? 0;

  console.log(`Imported Simplifier handoff into ${resolvedTarget}`);
  console.log(`Validated ${counts.project_count} projects, ${counts.floor_count} floors, ${counts.room_count} rooms, ${counts.element_count} elements.`);
  console.log(`Preserved ${basementFloors} basement floor(s) via floor_level=basement.`);
}

const isMain = process.argv[1]
  && import.meta.url === pathToFileURL(path.resolve(process.argv[1])).href;

if (isMain) {
  main().catch((error) => {
    console.error(error.message);
    process.exit(1);
  });
}
