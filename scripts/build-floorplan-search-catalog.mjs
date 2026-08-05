import { readFile, writeFile } from "node:fs/promises";
import { pathToFileURL } from "node:url";

const KNOWN_ROOM_IDS = new Set([
  "abstell", "ankleide", "bad", "balkon", "buero", "carport", "diele", "du_wc",
  "eltern", "elternbad", "essen", "essen_kochen", "flur", "garage", "garage_carport",
  "gast", "hobbyraum", "hwr_htr", "keller", "kind", "kinderbad", "kochen", "kueche",
  "kueche_essen", "luftraum", "speisekammer", "treppe", "wc", "wohnen",
  "wohnen_essen", "wohnen_essen_kochen", "zimmer",
]);

const STANDARD_ELEMENT_TYPES = ["door", "opening", "window", "stairs", "balcony", "roof_terrace"];

function countBy(values) {
  const counts = {};
  for (const value of values) counts[value] = (counts[value] ?? 0) + 1;
  return Object.fromEntries(Object.entries(counts).sort(([left], [right]) => left.localeCompare(right)));
}

function expandedRoomIds(room) {
  const sourceIds = room.room_ids?.length ? room.room_ids : [room.room_id];
  const expanded = new Set(sourceIds.filter(Boolean));
  const joined = sourceIds.join("_").toLowerCase();
  if (joined.includes("wohnen")) expanded.add("wohnen");
  if (joined.includes("essen")) expanded.add("essen");
  if (joined.includes("koch") || joined.includes("kueche")) expanded.add("kueche");
  if (joined.includes("du_wc")) expanded.add("wc");
  return [...expanded].sort();
}

function elementCounts(elements) {
  const raw = countBy(elements.map((element) => element.type || "unknown"));
  const complete = {};
  for (const type of STANDARD_ELEMENT_TYPES) complete[type] = raw[type] ?? 0;
  for (const [type, count] of Object.entries(raw)) if (!(type in complete)) complete[type] = count;
  return complete;
}

function programTags(roomCounts, elements) {
  const tags = new Set();
  const add = (condition, tag) => { if (condition) tags.add(tag); };
  add((roomCounts.wohnen ?? 0) > 0, "living");
  add((roomCounts.essen ?? 0) > 0, "dining");
  add((roomCounts.kueche ?? 0) > 0, "kitchen");
  add((roomCounts.eltern ?? 0) + (roomCounts.kind ?? 0) + (roomCounts.gast ?? 0) + (roomCounts.zimmer ?? 0) > 0, "bedrooms");
  add((roomCounts.kind ?? 0) > 0, "child_rooms");
  add((roomCounts.gast ?? 0) > 0, "guest_room");
  add((roomCounts.bad ?? 0) + (roomCounts.kinderbad ?? 0) + (roomCounts.elternbad ?? 0) > 0, "bathroom");
  add((roomCounts.wc ?? 0) + (roomCounts.du_wc ?? 0) > 0, "guest_wc");
  add((roomCounts.buero ?? 0) > 0, "office");
  add((roomCounts.hwr_htr ?? 0) > 0, "utility_room");
  add((roomCounts.speisekammer ?? 0) > 0, "pantry");
  add((roomCounts.ankleide ?? 0) > 0, "dressing");
  add((roomCounts.hobbyraum ?? 0) > 0, "hobby_room");
  add((roomCounts.abstell ?? 0) > 0, "storage");
  add((roomCounts.garage ?? 0) + (roomCounts.garage_carport ?? 0) > 0, "garage");
  add((roomCounts.carport ?? 0) + (roomCounts.garage_carport ?? 0) > 0, "carport");
  add((roomCounts.balkon ?? 0) + (elements.balcony ?? 0) > 0, "balcony");
  add((elements.roof_terrace ?? 0) > 0, "roof_terrace");
  return [...tags].sort();
}

function samePoints(left, right) {
  return Array.isArray(left) && Array.isArray(right)
    && left.length === right.length
    && left.every((point, index) => point?.[0] === right[index]?.[0] && point?.[1] === right[index]?.[1]);
}

function floorSummary(floor) {
  const rooms = Array.isArray(floor.rooms) ? floor.rooms : [];
  const elements = Array.isArray(floor.elements) ? floor.elements : [];
  const sourceRoomCounts = countBy(rooms.map((room) => room.room_id || "unknown"));
  const roomCounts = countBy(rooms.flatMap(expandedRoomIds));
  const areas = {};
  for (const room of rooms) {
    for (const roomId of expandedRoomIds(room)) {
      areas[roomId] = Number(((areas[roomId] ?? 0) + (Number.isFinite(room.area_ratio) ? room.area_ratio : 0)).toFixed(6));
    }
  }
  const counts = elementCounts(elements);
  return {
    floor_level: floor.floor_level,
    room_polygon_count: rooms.length,
    source_room_counts: sourceRoomCounts,
    room_counts: roomCounts,
    room_ids: Object.keys(roomCounts).sort(),
    program_tags: programTags(roomCounts, counts),
    relative_marked_area_by_room: Object.fromEntries(Object.entries(areas).sort(([left], [right]) => left.localeCompare(right))),
    total_marked_area_ratio: Number(rooms.reduce((sum, room) => sum + (Number.isFinite(room.area_ratio) ? room.area_ratio : 0), 0).toFixed(6)),
    element_count: elements.length,
    element_counts: counts,
  };
}

function projectDiscrepancies(project, floors) {
  const issues = [];
  for (const [index, floor] of (project.floors ?? []).entries()) {
    if (!(floor.rooms?.length)) issues.push({ code: "empty_floor", floor_level: floor.floor_level, floor_index: index });
    for (const room of floor.rooms ?? []) {
      const sourceIds = room.room_ids?.length ? room.room_ids : [room.room_id];
      for (const roomId of sourceIds) {
        if (!KNOWN_ROOM_IDS.has(roomId)) issues.push({ code: "unknown_room_id", floor_level: floor.floor_level, room_id: roomId, source_id: room.id });
      }
      if (/[???]/u.test(room.label ?? "")) {
        issues.push({ code: "mojibake_label", floor_level: floor.floor_level, label: room.label, source_id: room.id });
      }
    }
  }
  const habitable = (project.floors ?? []).filter((floor) => floor.floor_level !== "basement");
  if (habitable.length > 1) {
    const stairs = habitable.map((floor) => (floor.elements ?? []).filter((element) => element.type === "stairs"));
    const aligned = stairs.every((items) => items.length === 1)
      && stairs.slice(1).every((items) => samePoints(items[0].points, stairs[0][0].points));
    if (!aligned) issues.push({ code: "stair_mismatch", floor_levels: habitable.map((floor) => floor.floor_level) });
  }
  if (!project.quality_status) issues.push({ code: "missing_quality_status" });
  if (!project.source_rights_status || !project.usage_scope) issues.push({ code: "missing_rights_metadata" });
  if (floors.length !== (project.floors ?? []).length) issues.push({ code: "floor_summary_mismatch" });
  return issues;
}

function projectRecord(project) {
  const floors = (project.floors ?? []).map(floorSummary);
  const allRooms = (project.floors ?? []).flatMap((floor) => floor.rooms ?? []);
  const allElements = (project.floors ?? []).flatMap((floor) => floor.elements ?? []);
  const sourceRoomCounts = countBy(allRooms.map((room) => room.room_id || "unknown"));
  const roomCounts = countBy(allRooms.flatMap(expandedRoomIds));
  const elements = elementCounts(allElements);
  const discrepancies = projectDiscrepancies(project, floors);
  const count = (id) => roomCounts[id] ?? 0;
  const sourceCount = (id) => sourceRoomCounts[id] ?? 0;
  return {
    project_id: project.project_id,
    house_type: project.house_type,
    schema_version: project.schema_version ?? "",
    package_status: project.package_status ?? "",
    quality_status: project.quality_status ?? "",
    approval_status: project.approval_status ?? "",
    usage_scope: project.usage_scope ?? "",
    source_kind: project.source_kind ?? "",
    source_rights_status: project.source_rights_status ?? "",
    reconstruction_only: project.reconstruction_only === true,
    commercial_generator_eligible: project.commercial_generator_eligible === true,
    annotation_sha256: project.annotation_sha256 ?? "",
    floor_count: floors.length,
    habitable_floor_count: floors.filter((floor) => floor.floor_level !== "basement").length,
    floor_levels: floors.map((floor) => floor.floor_level),
    has_basement: floors.some((floor) => floor.floor_level === "basement"),
    room_polygon_count: allRooms.length,
    source_room_counts: sourceRoomCounts,
    room_counts: roomCounts,
    derived_counts: {
      bedroom: count("eltern") + count("kind") + count("gast") + count("zimmer"),
      primary_bedroom: count("eltern"),
      child_room: count("kind"),
      guest_room: count("gast"),
      flex_room: count("zimmer"),
      bathroom: count("bad") + count("kinderbad") + count("elternbad"),
      guest_wc: sourceCount("wc") + sourceCount("du_wc"),
      office: count("buero"),
      utility_room: count("hwr_htr"),
      pantry: count("speisekammer"),
      dressing: count("ankleide"),
      hobby_room: count("hobbyraum"),
      storage: count("abstell"),
      garage: count("garage") + count("garage_carport"),
      carport: count("carport") + count("garage_carport"),
      balcony: count("balkon") + elements.balcony,
      terrace: 0,
      roof_terrace: elements.roof_terrace,
    },
    program_tags: programTags(roomCounts, elements),
    element_count: allElements.length,
    element_counts: elements,
    metric_area: {
      status: "unavailable",
      reason: "No authoritative metric scale is present in the Simplifier v2 export.",
    },
    floors,
    discrepancy_count: discrepancies.length,
    discrepancies,
  };
}

export function buildSearchCatalog(dataset, manifest) {
  const records = [...(dataset.projects ?? [])]
    .map(projectRecord)
    .sort((left, right) => left.project_id.localeCompare(right.project_id));
  const totals = {
    projects: records.length,
    floors: records.reduce((sum, record) => sum + record.floor_count, 0),
    rooms: records.reduce((sum, record) => sum + record.room_polygon_count, 0),
    elements: records.reduce((sum, record) => sum + record.element_count, 0),
  };
  const expected = {
    projects: manifest.project_count,
    floors: manifest.floor_count,
    rooms: manifest.room_count,
    elements: manifest.element_count,
  };
  for (const key of Object.keys(expected)) {
    if (totals[key] !== expected[key]) throw new Error(`Manifest mismatch for ${key}: expected ${expected[key]}, received ${totals[key]}`);
  }
  const discrepancies = records.flatMap((record) =>
    record.discrepancies.map((issue) => ({ project_id: record.project_id, ...issue }))
  );
  return {
    schema: "zf-floorplan-search-catalog-v1",
    source_dataset_version: dataset.dataset_version ?? "",
    source_schema: dataset.source_schema ?? "",
    totals,
    statistics: {
      house_types: countBy(records.map((record) => record.house_type)),
      floor_levels: countBy(records.flatMap((record) => record.floor_levels)),
      quality_statuses: countBy(records.map((record) => record.quality_status || "missing")),
      approval_statuses: countBy(records.map((record) => record.approval_status || "missing")),
      usage_scopes: countBy(records.map((record) => record.usage_scope || "missing")),
      rights_statuses: countBy(records.map((record) => record.source_rights_status || "missing")),
      commercial_generator_eligible: records.filter((record) => record.commercial_generator_eligible).length,
      discrepancy_count: discrepancies.length,
    },
    discrepancies,
    records,
  };
}

export function filterCatalogRecords(records, filters = {}) {
  const minima = filters.minimum_room_counts ?? {};
  const requiredTags = filters.required_tags ?? [];
  return records.filter((record) => {
    if (filters.project_id && record.project_id !== filters.project_id) return false;
    if (filters.house_type && record.house_type !== filters.house_type) return false;
    if (filters.habitable_floor_count != null && record.habitable_floor_count !== filters.habitable_floor_count) return false;
    if (filters.quality_status && record.quality_status !== filters.quality_status) return false;
    if (filters.has_basement != null && record.has_basement !== filters.has_basement) return false;
    if (filters.usage_scope) {
      if (record.usage_scope !== filters.usage_scope) return false;
      if (filters.usage_scope === "commercial_generator" && (
        !record.commercial_generator_eligible
        || record.reconstruction_only
        || record.source_rights_status === "restricted_reference"
      )) return false;
    }
    if (!requiredTags.every((tag) => record.program_tags.includes(tag))) return false;
    return Object.entries(minima).every(([roomId, minimum]) => (record.room_counts[roomId] ?? 0) >= minimum);
  });
}

export function stableJson(value) {
  return `${JSON.stringify(value, null, 2)}\n`;
}

async function runCli() {
  const datasetUrl = new URL("../data/simplifier-v2/dataset.json", import.meta.url);
  const manifestUrl = new URL("../data/simplifier-v2/manifest.json", import.meta.url);
  const outputUrl = new URL("../data/simplifier-v2/search-catalog.json", import.meta.url);
  const [dataset, manifest] = await Promise.all([
    readFile(datasetUrl, "utf8").then(JSON.parse),
    readFile(manifestUrl, "utf8").then(JSON.parse),
  ]);
  const output = stableJson(buildSearchCatalog(dataset, manifest));
  if (process.argv.includes("--check")) {
    const current = await readFile(outputUrl, "utf8").catch(() => "");
    if (current !== output) throw new Error("search-catalog.json is missing or stale; run the catalogue builder.");
    console.log("search-catalog.json is current.");
    return;
  }
  await writeFile(outputUrl, output, "utf8");
  console.log(`Wrote ${outputUrl.pathname} with ${manifest.project_count} projects.`);
}

if (import.meta.url === pathToFileURL(process.argv[1] ?? "").href) {
  await runCli();
}
