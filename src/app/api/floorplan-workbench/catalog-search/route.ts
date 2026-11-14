import { filterFloorplanCatalog, floorplanSearchCatalog, type FloorplanCatalogFilters } from "@/lib/training/floorplan-search-catalog";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";
const DEFAULT_LIMIT = 60;

function hostname(value: string) { const first = value.split(",")[0]?.trim().toLowerCase() || ""; return first.startsWith("[") ? first.slice(1, first.indexOf("]")) : first.split(":")[0]; }
function enabled(request: Request) { const local = ["127.0.0.1", "localhost", "::1"]; return process.env.FLOORPLAN_WORKBENCH_ENABLED === "true" && local.includes(new URL(request.url).hostname.toLowerCase()) && local.includes(hostname(request.headers.get("x-forwarded-host") || request.headers.get("host") || "")); }

function parseMinimumRoomCounts(params: URLSearchParams): Record<string, number> | undefined {
  const entries = params.getAll("minRoom")
    .map((pair) => pair.split(":"))
    .filter((parts): parts is [string, string] => parts.length === 2 && parts[0].length > 0 && Number.isFinite(Number(parts[1])))
    .map(([roomId, count]) => [roomId, Number(count)] as const);
  if (!entries.length) return undefined;
  return Object.fromEntries(entries);
}

function parseFilters(params: URLSearchParams): FloorplanCatalogFilters {
  const filters: FloorplanCatalogFilters = {};
  const houseType = params.get("houseType"); if (houseType) filters.houseType = houseType;
  const habitableFloorCount = params.get("habitableFloorCount"); if (habitableFloorCount !== null && habitableFloorCount !== "" && Number.isFinite(Number(habitableFloorCount))) filters.habitableFloorCount = Number(habitableFloorCount);
  const qualityStatus = params.get("qualityStatus"); if (qualityStatus) filters.qualityStatus = qualityStatus;
  const usageScope = params.get("usageScope"); if (usageScope) filters.usageScope = usageScope;
  const hasBasement = params.get("hasBasement"); if (hasBasement === "true") filters.hasBasement = true; else if (hasBasement === "false") filters.hasBasement = false;
  const requiredTags = params.get("requiredTags"); if (requiredTags) filters.requiredTags = requiredTags.split(",").map((tag) => tag.trim()).filter(Boolean);
  const minimumRoomCounts = parseMinimumRoomCounts(params); if (minimumRoomCounts) filters.minimumRoomCounts = minimumRoomCounts;
  return filters;
}

export async function GET(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const url = new URL(request.url);
  const filters = parseFilters(url.searchParams);
  const limitParam = Number(url.searchParams.get("limit"));
  const limit = Number.isFinite(limitParam) && limitParam > 0 ? Math.min(limitParam, 200) : DEFAULT_LIMIT;
  const matches = filterFloorplanCatalog(filters);
  const results = matches.slice(0, limit).map((record) => ({
    project_id: record.project_id,
    house_type: record.house_type,
    habitable_floor_count: record.habitable_floor_count,
    has_basement: record.has_basement,
    quality_status: record.quality_status,
    approval_status: record.approval_status,
    usage_scope: record.usage_scope,
    program_tags: record.program_tags,
    room_counts: record.room_counts,
  }));
  return Response.json({
    schema: "zf-floorplan-workbench-catalog-search-v1",
    filters,
    total_catalogue_projects: floorplanSearchCatalog().totals.projects,
    matched_count: matches.length,
    returned_count: results.length,
    truncated: matches.length > results.length,
    results,
  }, { status: 200, headers: { "Cache-Control": "no-store" } });
}
