import { createHash } from "node:crypto";
import { APPROVED_FLOORPLAN_RECORDS } from "./fixtures/approved/catalog.generated.mjs";
import type { HouseBrief, PlannedRoom, StairGeometry } from "./floorplan";

type Point = [number, number];

export type ApprovedRoom = {
  id: string;
  name: string;
  kind: PlannedRoom["kind"];
  polygon: Point[];
  area_m2: number;
};

export type ApprovedWall = {
  id: string;
  start: Point;
  end: Point;
  thickness: number;
  wall_type: "exterior" | "partition";
  room_ids: string[];
};

export type ApprovedOpening = {
  id: string;
  opening_type: "door" | "window" | "passage";
  wall_id: string;
  position: number;
  width: number;
  role: string;
  connects: string[];
  traversable: boolean;
};

export type ApprovedFloor = {
  id: string;
  name: string;
  level: number;
  footprint: Point[];
  rooms: ApprovedRoom[];
  walls: ApprovedWall[];
  openings: ApprovedOpening[];
  stair_core_id: string | null;
};

export type ApprovedFloorplanDocument = {
  schema: "dmh-floorplan-approved-canonical-v1";
  revision: number;
  plan_id: string;
  provenance: {
    creation_mode: string;
    source_assets_included: false;
    internal_source_record_retained_locally?: boolean;
  };
  rights: {
    source_status?: string;
    usage_scope: "commercial_generator";
    decision: "commercially_cleared" | "generic_layout_reconstructed";
    commercial_approval_attested?: boolean;
    wordpress_eligible: true;
  };
  building: {
    coordinate_unit: "mm";
    footprint_width_mm: number;
    footprint_depth_mm: number;
    floor_height_mm?: number;
    storey_type: HouseBrief["storeyType"];
    roof_form?: string;
    geometry_source?: string;
  };
  floors: ApprovedFloor[];
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
  status: "approved";
  wordpress_eligible: true;
};

export type ApprovedFloorplanManifest = {
  schema: "dmh-floorplan-approved-package-v3";
  plan_id: string;
  geometry_hash: string;
  wordpress_eligible: true;
  rights: ApprovedFloorplanDocument["rights"];
};

export type ApprovedFloorplanRecord = {
  document: ApprovedFloorplanDocument;
  manifest: ApprovedFloorplanManifest;
};

function canonicalValue(value: unknown): unknown {
  if (Array.isArray(value)) return value.map(canonicalValue);
  if (!value || typeof value !== "object") return value;
  const source = value as Record<string, unknown>;
  return Object.fromEntries(
    Object.keys(source).sort().map((key) => [key, canonicalValue(source[key])]),
  );
}

export function approvedGeometryHash(document: Pick<
  ApprovedFloorplanDocument,
  "building" | "floors" | "shared_stair_core"
>) {
  return createHash("sha256")
    .update(JSON.stringify(canonicalValue({
      building: document.building,
      floors: document.floors,
      shared_stair_core: document.shared_stair_core,
    })))
    .digest("hex");
}

export function assertApprovedFloorplanRecord(
  source: unknown,
): ApprovedFloorplanRecord {
  const record = structuredClone(source) as ApprovedFloorplanRecord;
  const { document, manifest } = record || {};
  const geometryHash = document && approvedGeometryHash(document);
  if (
    !document
    || !manifest
    || document.schema !== "dmh-floorplan-approved-canonical-v1"
    || manifest.schema !== "dmh-floorplan-approved-package-v3"
    || document.status !== "approved"
    || document.wordpress_eligible !== true
    || manifest.wordpress_eligible !== true
    || document.rights?.usage_scope !== "commercial_generator"
    || document.rights?.wordpress_eligible !== true
    || manifest.rights?.usage_scope !== "commercial_generator"
    || manifest.rights?.wordpress_eligible !== true
    || !["commercially_cleared", "generic_layout_reconstructed"].includes(
      document.rights?.decision,
    )
    || document.geometry_hash !== geometryHash
    || manifest.geometry_hash !== geometryHash
    || document.plan_id !== manifest.plan_id
    || document.plan_id !== `plan-${geometryHash?.slice(0, 16)}`
    || document.building?.coordinate_unit !== "mm"
    || !["1_storey", "1_5_storey", "2_storey"].includes(
      document.building?.storey_type,
    )
  ) {
    throw new Error("Approved floorplan catalogue entry is inconsistent.");
  }
  return record;
}

export function approvedPlanFeatures(document: ApprovedFloorplanDocument) {
  const rooms = document.floors.flatMap((floor) => floor.rooms);
  return {
    area: rooms.reduce((sum, room) => sum + Number(room.area_m2 || 0), 0),
    bedrooms: rooms.filter((room) => room.kind === "sleeping").length,
    office: rooms.some((room) => /b.ro|buero|office/i.test(room.name)),
    guestWc: rooms.some((room) =>
      /g.ste.?wc|gaeste.?wc|guest.?wc|\bwc\b/i.test(room.name)
    ),
    utilityRoom: rooms.some((room) =>
      room.kind === "service" || /hwr|htr|technik|utility/i.test(room.name)
    ),
  };
}

export function selectApprovedFloorplan(
  brief: Pick<
    HouseBrief,
    "storeyType" | "area" | "bedrooms" | "office" | "guestWc" | "utilityRoom"
  >,
  records: readonly unknown[] = APPROVED_FLOORPLAN_RECORDS,
) {
  const candidates = records.flatMap((source) => {
    try {
      const record = assertApprovedFloorplanRecord(source);
      if (record.document.building.storey_type !== brief.storeyType) return [];
      const features = approvedPlanFeatures(record.document);
      if (
        features.bedrooms < brief.bedrooms
        || (brief.office && !features.office)
        || (brief.guestWc && !features.guestWc)
        || (brief.utilityRoom && !features.utilityRoom)
      ) {
        return [];
      }
      return [{ record, distance: Math.abs(features.area - brief.area) }];
    } catch {
      return [];
    }
  });
  candidates.sort((left, right) =>
    left.distance - right.distance
    || left.record.document.plan_id.localeCompare(right.record.document.plan_id)
  );
  return candidates[0]?.record ?? null;
}
