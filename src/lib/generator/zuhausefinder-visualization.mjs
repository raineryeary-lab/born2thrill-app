import { createHash } from "node:crypto";
import { validateZuhausefinderBrief } from "./zuhausefinder-brief.mjs";

export const REFERENCE_GENERATOR_VERSION = "reference-generator-v1";
export const VISUALIZATION_CONTEXT_VERSION = "dmh-visualization-context-v1";
export const PLAN_GUIDE_WIDTH = 1024;
export const PLAN_GUIDE_HEIGHT = 1024;

const FEATURE_TERMS = {
  garage: ["garage"],
  carport: ["carport"],
  balcony: ["balkon"],
  dormer: ["gaube", "dachgaube"],
  gable: ["giebel"],
  extension: ["anbau", "erker"],
  pool: ["pool", "schwimmbecken"],
};

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function text(value) {
  return typeof value === "string" ? value.trim() : "";
}

function normalizedText(value) {
  return text(value)
    .toLocaleLowerCase("de-DE")
    .normalize("NFD")
    .replace(/\p{Diacritic}/gu, "");
}

function finite(value, fallback = 0) {
  const candidate = Number(value);
  return Number.isFinite(candidate) ? candidate : fallback;
}

function rounded(value, digits = 4) {
  const factor = 10 ** digits;
  return Math.round(finite(value) * factor) / factor;
}

function clamp(value, minimum = 0, maximum = 1) {
  return Math.max(minimum, Math.min(maximum, finite(value)));
}

function canonicalValue(value) {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (!isRecord(value)) return value;
  return Object.fromEntries(
    Object.keys(value)
      .sort()
      .filter((key) => value[key] !== undefined)
      .map((key) => [key, canonicalValue(value[key])]),
  );
}

export function canonicalJson(value) {
  return JSON.stringify(canonicalValue(value));
}

export function sha256Hex(value) {
  return createHash("sha256").update(value).digest("hex");
}

function normalizedPoint(point) {
  return {
    x: rounded(point?.x),
    y: rounded(point?.y),
  };
}

export function floorplanGeometryPayload(variant) {
  return {
    storey_type: text(variant?.storeyType),
    footprint: {
      width_m: rounded(variant?.metrics?.footprintWidthM, 3),
      depth_m: rounded(variant?.metrics?.footprintDepthM, 3),
    },
    floors: (Array.isArray(variant?.floors) ? variant.floors : []).map((floor) => ({
      floor: finite(floor.floor),
      name: text(floor.name),
      reference_layout_id: text(floor.referenceLayoutId),
      reference_footprint: floor.referenceFootprint
        ? {
            x: rounded(floor.referenceFootprint.x),
            y: rounded(floor.referenceFootprint.y),
            width: rounded(floor.referenceFootprint.width),
            height: rounded(floor.referenceFootprint.height),
          }
        : null,
      reference_footprint_polygon: Array.isArray(floor.referenceFootprintPolygon)
        ? floor.referenceFootprintPolygon.map(normalizedPoint)
        : null,
      rooms: [...(Array.isArray(floor.rooms) ? floor.rooms : [])]
        .sort((left, right) => text(left.id).localeCompare(text(right.id)))
        .map((room) => ({
          id: text(room.id),
          kind: text(room.kind),
          x: rounded(room.x),
          y: rounded(room.y),
          width: rounded(room.width),
          height: rounded(room.height),
          polygon: Array.isArray(room.polygon)
            ? room.polygon.map(normalizedPoint)
            : null,
        })),
      stair: floor.stair
        ? {
            type: text(floor.stair.type),
            usable_flight_width_m: rounded(floor.stair.usableFlightWidthM, 3),
            footprint_width_m: rounded(floor.stair.footprintWidthM, 3),
            footprint_length_m: rounded(floor.stair.footprintLengthM, 3),
          }
        : null,
    })),
  };
}

export function geometrySha256(variant) {
  if (/^[a-f0-9]{64}$/.test(text(variant?.canonicalGeometrySha256))) {
    return text(variant.canonicalGeometrySha256);
  }
  return sha256Hex(canonicalJson(floorplanGeometryPayload(variant)));
}

function roofFromDedicatedAnswer(source, brief) {
  const exteriorPreferences = isRecord(source.exterior_preferences)
    ? source.exterior_preferences
    : {};
  const answer = text(exteriorPreferences.roof_answer);
  const normalized = normalizedText(answer);
  if (normalized.includes("dachform") && normalized.includes("ableiten")) {
    return {
      form: null,
      source: "dedicated_roof_answer",
      confidence: "unverified",
      evidence: answer,
    };
  }
  if (normalized.includes("satteldach")) {
    return {
      form: "satteldach",
      source: "dedicated_roof_answer",
      confidence: "verified",
      evidence: answer,
    };
  }
  if (normalized.includes("walmdach")) {
    return {
      form: "walmdach",
      source: "dedicated_roof_answer",
      confidence: "verified",
      evidence: answer,
    };
  }
  const mentionsFlat = normalized.includes("flachdach");
  const mentionsShed = normalized.includes("pultdach");
  if (mentionsFlat && mentionsShed) {
    return {
      form: "flach_oder_pultdach",
      source: "dedicated_roof_answer",
      confidence: "inferred",
      evidence: answer,
    };
  }
  if (mentionsFlat || mentionsShed) {
    return {
      form: mentionsFlat ? "flachdach" : "pultdach",
      source: "dedicated_roof_answer",
      confidence: "verified",
      evidence: answer,
    };
  }
  const inferred = text(brief?.roof);
  return {
    form: inferred ? normalizedText(inferred).replace(/\s+/g, "_") : null,
    source: inferred ? "generator_inference" : "unknown",
    confidence: "inferred",
    evidence: inferred || null,
  };
}

function storeyContext(variant) {
  const type = text(variant?.storeyType);
  return {
    type: type === "1_storey"
      ? "bungalow"
      : type === "1_5_storey"
        ? "one_and_half_storeys"
        : "two_storeys",
    count: type === "1_storey" ? 1 : type === "1_5_storey" ? 1.5 : 2,
    floor_count: Array.isArray(variant?.floors) ? variant.floors.length : 0,
  };
}

function requestedFeatureText(source) {
  const parts = [
    source?.room_program?.description,
    source?.exterior_preferences?.description,
    source?.exterior_preferences?.roof_answer,
    ...(Array.isArray(source?.reference_search?.search_tags)
      ? source.reference_search.search_tags
      : []),
  ];
  return normalizedText(parts.filter(Boolean).join(" "));
}

export function buildZuhausefinderVisualizationContext(input, brief, variant) {
  const source = validateZuhausefinderBrief(input);
  const footprintWidth = rounded(variant?.metrics?.footprintWidthM, 3);
  const footprintDepth = rounded(variant?.metrics?.footprintDepthM, 3);
  const roof = roofFromDedicatedAnswer(source, brief);
  const storeys = storeyContext(variant);
  const mustMatch = [
    `Geschossigkeit: ${storeys.count}`,
    `Baukörper-Proportion Breite zu Tiefe: ${rounded(
      footprintDepth > 0 ? footprintWidth / footprintDepth : 1,
      3,
    )}`,
  ];
  if (roof.confidence === "verified" && roof.form) {
    mustMatch.push(`Dachform: ${roof.form}`);
  }

  const requested = requestedFeatureText(source);
  const mustNotInvent = Object.entries(FEATURE_TERMS)
    .filter(([, terms]) => !terms.some((term) => requested.includes(term)))
    .map(([feature]) => feature);
  const unresolved = [
    "plot_orientation",
    "street_side",
    "garden_side",
    "entrance_side",
    "exact_exterior_opening_positions",
    "local_planning_law",
  ];
  if (roof.confidence !== "verified") unresolved.push("exact_roof_form");

  return {
    schema: VISUALIZATION_CONTEXT_VERSION,
    geometry_sha256: geometrySha256(variant),
    footprint: {
      width_m: footprintWidth,
      depth_m: footprintDepth,
      aspect_ratio: rounded(footprintDepth > 0 ? footprintWidth / footprintDepth : 1, 3),
    },
    storeys,
    roof,
    orientation: {
      street: null,
      garden: null,
      confidence: "unverified",
    },
    must_match: mustMatch,
    may_vary: [
      "camera_position",
      "landscaping",
      "non_structural_material_details",
      "unverified_window_rhythm",
    ],
    must_not_invent: mustNotInvent,
    unresolved,
  };
}

function floorBounds(floor) {
  if (
    floor?.referenceFootprint &&
    finite(floor.referenceFootprint.width) > 0 &&
    finite(floor.referenceFootprint.height) > 0
  ) {
    return {
      x: finite(floor.referenceFootprint.x),
      y: finite(floor.referenceFootprint.y),
      width: finite(floor.referenceFootprint.width),
      height: finite(floor.referenceFootprint.height),
    };
  }
  const rooms = Array.isArray(floor?.rooms) ? floor.rooms : [];
  if (!rooms.length) return { x: 0, y: 0, width: 1, height: 1 };
  const minX = Math.min(...rooms.map((room) => finite(room.x)));
  const minY = Math.min(...rooms.map((room) => finite(room.y)));
  const maxX = Math.max(...rooms.map((room) => finite(room.x) + finite(room.width)));
  const maxY = Math.max(...rooms.map((room) => finite(room.y) + finite(room.height)));
  return {
    x: minX,
    y: minY,
    width: Math.max(1, maxX - minX),
    height: Math.max(1, maxY - minY),
  };
}

export function planGeometryGuideModel(variant) {
  const floors = (Array.isArray(variant?.floors) ? variant.floors : []).map((floor) => {
    const bounds = floorBounds(floor);
    return {
      floor: finite(floor.floor),
      rooms: [...(Array.isArray(floor.rooms) ? floor.rooms : [])]
        .sort((left, right) => text(left.id).localeCompare(text(right.id)))
        .map((room) => ({
          id: text(room.id),
          kind: text(room.kind) || "flex",
          x: clamp((finite(room.x) - bounds.x) / bounds.width),
          y: clamp((finite(room.y) - bounds.y) / bounds.height),
          width: clamp(finite(room.width) / bounds.width),
          height: clamp(finite(room.height) / bounds.height),
        })),
    };
  });
  return {
    width: PLAN_GUIDE_WIDTH,
    height: PLAN_GUIDE_HEIGHT,
    footprint_aspect_ratio: rounded(
      finite(variant?.metrics?.footprintDepthM) > 0
        ? finite(variant?.metrics?.footprintWidthM) /
          finite(variant?.metrics?.footprintDepthM)
        : 1,
      3,
    ),
    floors,
  };
}

export function assertValidPlanGuidePng(bytes) {
  const buffer = Buffer.isBuffer(bytes) ? bytes : Buffer.from(bytes);
  if (
    buffer.length < 1000 ||
    buffer.length > 3 * 1024 * 1024 ||
    buffer.subarray(0, 8).toString("hex") !== "89504e470d0a1a0a"
  ) {
    throw new Error("Der Geometrieleitfaden ist keine gültige PNG-Datei.");
  }
  const width = buffer.readUInt32BE(16);
  const height = buffer.readUInt32BE(20);
  if (width !== PLAN_GUIDE_WIDTH || height !== PLAN_GUIDE_HEIGHT) {
    throw new Error("Der Geometrieleitfaden hat unerwartete Abmessungen.");
  }
  return buffer;
}
