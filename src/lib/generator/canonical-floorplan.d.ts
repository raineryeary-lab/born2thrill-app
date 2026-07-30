export type PointMm = [number, number];
export type PolygonMm = PointMm[];

export type CanonicalFloorplan = {
  schema_version: "dmh-canonical-floorplan-v1";
  plan_id: string;
  units: "mm";
  coordinate_system: {
    origin: "northwest";
    x_positive: "east";
    y_positive: "south";
    integer_precision_mm: 1;
    north_rotation_degrees: number | null;
    wall_reference: "centerline";
  };
  building: {
    storey_type: "1_storey" | "1_5_storey" | "2_storey";
  };
  footprint: {
    boundary_reference: "exterior_wall_centerline";
    boundary_polygon_mm: PolygonMm;
  };
  storeys: Array<{
    id: string;
    level_index: number;
    elevation_mm: number;
    planning_boundary_mm: PolygonMm;
    rooms: Array<{
      id: string;
      name: string;
      room_type: string;
      access_required: boolean;
      habitable: boolean;
      polygon_mm: PolygonMm;
    }>;
    walls: Array<{
      id: string;
      wall_type: "exterior" | "loadbearing" | "partition";
      start_mm: PointMm;
      end_mm: PointMm;
      thickness_mm: number;
      separates: [string, string];
    }>;
    openings: Array<{
      id: string;
      opening_type: "door" | "window" | "open_passage";
      wall_id: string;
      offset_mm: number;
      width_mm: number;
      connects: [string, string];
      traversable: boolean;
      sill_height_mm?: number;
      height_mm?: number;
    }>;
    slab_openings: Array<{
      id: string;
      opening_type: "stairs" | "shaft" | "void";
      polygon_mm: PolygonMm;
    }>;
  }>;
  entrance: {
    storey_id: string;
    opening_id: string;
    enters_room_id: string;
  };
  stairs: Array<{
    id: string;
    stair_type: "straight" | "quarter_turn" | "half_turn" | "multi_turn";
    from_storey_id: string;
    to_storey_id: string;
    clear_width_mm: number;
    direction: "up";
    path_mm: PointMm[];
    interfaces: Array<{
      storey_id: string;
      footprint_polygon_mm: PolygonMm;
      arrival_room_id: string;
      slab_opening_id: string | null;
    }>;
  }>;
  provenance: {
    source_kind: "real_annotated" | "synthetic_test";
    source_project_id: string;
    source_schema_version: string;
    source_annotation_sha256: string | null;
    conversion_method: string;
    scale_anchor: {
      status: "verified" | "user_confirmed_inferred" | "not_applicable_synthetic";
      kind: "overall_width" | "overall_depth" | "dimension_line" | "survey" | null;
      source_segment_normalized: [[number, number], [number, number]] | null;
      length_mm: number | null;
    };
  };
  geometry_hash: {
    algorithm: "sha256";
    canonicalization: "dmh-canonical-geometry-v1";
    value: string;
  };
  approval: {
    state: "internal_reference" | "commercial_approved" | "rejected";
    quality_status: "passed" | "review_required" | "rejected";
    rights_status: "not_explicitly_recorded" | "confirmed_owned" | "licensed" | "restricted";
    usage_scope: "internal_reference_only" | "commercial_generator";
    approved_by: string | null;
    approved_at: string | null;
    rights_evidence_reference: string | null;
  };
};

export type CanonicalFloorplanValidationReport = {
  passed: boolean;
  errors: string[];
  warnings: string[];
  stats: Record<string, string | number>;
};

export const CANONICAL_FLOORPLAN_SCHEMA_VERSION: "dmh-canonical-floorplan-v1";
export const CANONICAL_GEOMETRY_VERSION: "dmh-canonical-geometry-v1";
export const GEOMETRY_TOLERANCE_MM: 5;
export function canonicalFloorplanGeometryPayload(plan: CanonicalFloorplan): unknown;
export function canonicalFloorplanGeometrySha256(plan: CanonicalFloorplan): string;
export function withCanonicalGeometryHash(plan: CanonicalFloorplan): CanonicalFloorplan;
export function validateCanonicalFloorplan(plan: unknown): CanonicalFloorplanValidationReport;
export class CanonicalFloorplanValidationError extends Error {
  report: CanonicalFloorplanValidationReport;
}
export function loadCanonicalFloorplan(
  source: string | Buffer | CanonicalFloorplan,
): CanonicalFloorplan;
