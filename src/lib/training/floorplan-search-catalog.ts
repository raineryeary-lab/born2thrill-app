import catalogJson from "../../../data/simplifier-v2/search-catalog.json";

export type FloorplanCatalogRecord = {
  project_id: string;
  house_type: string;
  package_status: string;
  quality_status: string;
  approval_status: string;
  usage_scope: string;
  source_kind: string;
  source_rights_status: string;
  reconstruction_only: boolean;
  commercial_generator_eligible: boolean;
  annotation_sha256: string;
  floor_count: number;
  habitable_floor_count: number;
  floor_levels: string[];
  has_basement: boolean;
  room_polygon_count: number;
  source_room_counts: Record<string, number>;
  room_counts: Record<string, number>;
  derived_counts: Record<string, number>;
  program_tags: string[];
  element_count: number;
  element_counts: Record<string, number>;
  metric_area: {
    status: "unavailable";
    reason: string;
  };
  discrepancy_count: number;
};

export type FloorplanCatalog = {
  schema: "zf-floorplan-search-catalog-v1";
  source_dataset_version: string;
  source_schema: string;
  totals: {
    projects: number;
    floors: number;
    rooms: number;
    elements: number;
  };
  records: FloorplanCatalogRecord[];
};

export type FloorplanCatalogFilters = {
  projectId?: string;
  houseType?: string;
  habitableFloorCount?: number;
  qualityStatus?: string;
  usageScope?: string;
  hasBasement?: boolean;
  requiredTags?: string[];
  minimumRoomCounts?: Record<string, number>;
};

const catalog = catalogJson as unknown as FloorplanCatalog;

export function floorplanSearchCatalog(): FloorplanCatalog {
  return catalog;
}

export function floorplanCatalogRecord(projectId: string): FloorplanCatalogRecord | null {
  return catalog.records.find((record) => record.project_id === projectId) ?? null;
}

export function filterFloorplanCatalog(
  filters: FloorplanCatalogFilters = {},
): FloorplanCatalogRecord[] {
  const requiredTags = filters.requiredTags ?? [];
  const minimumRoomCounts = filters.minimumRoomCounts ?? {};
  return catalog.records.filter((record) => {
    if (filters.projectId && record.project_id !== filters.projectId) return false;
    if (filters.houseType && record.house_type !== filters.houseType) return false;
    if (
      filters.habitableFloorCount !== undefined
      && record.habitable_floor_count !== filters.habitableFloorCount
    ) return false;
    if (filters.qualityStatus && record.quality_status !== filters.qualityStatus) return false;
    if (filters.hasBasement !== undefined && record.has_basement !== filters.hasBasement) return false;
    if (filters.usageScope) {
      if (record.usage_scope !== filters.usageScope) return false;
      if (
        filters.usageScope === "commercial_generator"
        && (
          !record.commercial_generator_eligible
          || record.reconstruction_only
          || record.source_rights_status === "restricted_reference"
        )
      ) return false;
    }
    if (!requiredTags.every((tag) => record.program_tags.includes(tag))) return false;
    return Object.entries(minimumRoomCounts).every(
      ([roomId, minimum]) => (record.room_counts[roomId] ?? 0) >= minimum,
    );
  });
}
