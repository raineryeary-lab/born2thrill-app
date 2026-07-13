import { copyFile, mkdir, readFile, writeFile } from "node:fs/promises";
import path from "node:path";

const DEFAULT_SOURCE = "/Users/raineryeary/Documents/Codex/2026-06-23/fl/work/floorplan-simplifier/exports/floorplan-generator/simplifier-v1";
const SOURCE_README = "/Users/raineryeary/Documents/Codex/2026-06-23/fl/work/floorplan-simplifier/exports/floorplan-generator/README.md";
const TARGET = path.resolve("data/simplifier-v1");

const expected = {
  project_count: 15,
  floor_count: 29,
  room_count: 162,
  element_count: 367,
};

function assertEqual(name, actual, wanted) {
  if (actual !== wanted) {
    throw new Error(`${name} mismatch: expected ${wanted}, got ${actual}`);
  }
}

function countDataset(dataset) {
  const projects = Array.isArray(dataset.projects) ? dataset.projects : [];
  const floors = projects.flatMap((project) => Array.isArray(project.floors) ? project.floors : []);
  const rooms = floors.flatMap((floor) => [
    ...(Array.isArray(floor.annotations) ? floor.annotations : []),
    ...(Array.isArray(floor.rooms) ? floor.rooms : []),
  ]);
  const elements = floors.flatMap((floor) => Array.isArray(floor.elements) ? floor.elements : []);

  return {
    project_count: projects.length,
    floor_count: floors.length,
    room_count: rooms.length,
    element_count: elements.length,
  };
}

function validateDataset(dataset) {
  if (dataset.source_schema !== "simplifier-annotations-v1") {
    throw new Error(`Unsupported source_schema: ${dataset.source_schema}`);
  }

  const counts = countDataset(dataset);
  for (const [name, wanted] of Object.entries(expected)) {
    assertEqual(name, counts[name], wanted);
  }

  const cellarProject = dataset.projects.find((project) => project.project_id === "other_1_5_story_with_cellar");
  if (!cellarProject) {
    throw new Error("Missing cellar reference project other_1_5_story_with_cellar");
  }
  if (cellarProject.house_type !== "other") {
    throw new Error(`Cellar reference house_type must stay "other", got ${cellarProject.house_type}`);
  }

  const floorLevels = (cellarProject.floors ?? []).map((floor) => floor.floor_level);
  if (!floorLevels.includes("basement")) {
    throw new Error("Cellar reference project must include a basement floor_level");
  }

  return counts;
}

async function readJson(filePath) {
  return JSON.parse(await readFile(filePath, "utf8"));
}

async function main() {
  const source = path.resolve(process.argv[2] ?? DEFAULT_SOURCE);
  const datasetPath = path.join(source, "dataset.json");
  const knowledgePath = path.join(source, "knowledge.json");
  const manifestPath = path.join(source, "manifest.json");

  const dataset = await readJson(datasetPath);
  const manifest = await readJson(manifestPath);
  const counts = validateDataset(dataset);

  for (const [name, wanted] of Object.entries(expected)) {
    assertEqual(`manifest.${name}`, manifest[name], wanted);
  }

  await mkdir(TARGET, { recursive: true });
  await copyFile(datasetPath, path.join(TARGET, "dataset.json"));
  await copyFile(knowledgePath, path.join(TARGET, "knowledge.json"));
  await copyFile(manifestPath, path.join(TARGET, "manifest.json"));

  try {
    await copyFile(SOURCE_README, path.join(TARGET, "README.md"));
  } catch {
    await writeFile(path.join(TARGET, "README.md"), "# Simplifier v1 handoff\n\nPrivacy-safe local Floorplan Simplifier handoff.\n");
  }

  console.log(`Imported Simplifier handoff into ${TARGET}`);
  console.log(`Validated ${counts.project_count} projects, ${counts.floor_count} floors, ${counts.room_count} rooms, ${counts.element_count} elements.`);
  console.log("Cellar reference preserved as house_type=other; has_cellar is derived from floor_level=basement.");
}

main().catch((error) => {
  console.error(error.message);
  process.exit(1);
});
