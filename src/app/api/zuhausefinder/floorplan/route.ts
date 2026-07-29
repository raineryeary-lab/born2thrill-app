import { timingSafeEqual } from "node:crypto";
import type { HouseBrief } from "@/lib/generator/floorplan";
import { generateVariants } from "@/lib/generator/floorplan";
import {
  classifyZuhausefinderFloorplan,
  mapZuhausefinderBrief,
} from "@/lib/generator/zuhausefinder-brief.mjs";
import {
  assertSafeGeneratedSvg,
  customerFacingQualityPassed,
  floorplanQuality,
  renderFloorplanSvg,
  selectQualityVariant,
} from "@/lib/generator/floorplan-svg.mjs";
import { renderPlanGeometryGuidePng } from "@/lib/generator/floorplan-guide";
import {
  buildZuhausefinderVisualizationContext,
  REFERENCE_GENERATOR_VERSION,
  sha256Hex,
} from "@/lib/generator/zuhausefinder-visualization.mjs";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const MAX_REQUEST_BYTES = 64 * 1024;

function json(data: unknown, status = 200) {
  return Response.json(data, {
    status,
    headers: {
      "Cache-Control": "no-store",
      "X-Content-Type-Options": "nosniff",
    },
  });
}

function authorized(request: Request) {
  const expected = process.env.ZUHAUSEFINDER_WEBHOOK_TOKEN?.trim() ?? "";
  const header = request.headers.get("authorization") ?? "";
  const supplied = header.startsWith("Bearer ") ? header.slice(7).trim() : "";
  if (!expected || !supplied) return false;
  const expectedBytes = Buffer.from(expected);
  const suppliedBytes = Buffer.from(supplied);
  return expectedBytes.length === suppliedBytes.length
    && timingSafeEqual(expectedBytes, suppliedBytes);
}

export function GET() {
  return json({
    status: "ok",
    service: "zuhausefinder-floorplan",
    input_schema: "dmh-floorplan-brief-v1",
    output_schema: "dmh-floorplan-result-v2",
    output: "base64-svg-and-png-guide",
  });
}

export async function POST(request: Request) {
  if (!process.env.ZUHAUSEFINDER_WEBHOOK_TOKEN?.trim()) {
    return json({ error: "Der Generator ist noch nicht konfiguriert." }, 503);
  }
  if (!authorized(request)) {
    return json({ error: "Nicht autorisiert." }, 401);
  }
  const body = await request.text();
  if (Buffer.byteLength(body, "utf8") > MAX_REQUEST_BYTES) {
    return json({ error: "Das Grundriss-Briefing ist zu groß." }, 413);
  }

  try {
    const source = JSON.parse(body) as unknown;
    const brief = mapZuhausefinderBrief(source) as HouseBrief;
    const variants = generateVariants(brief);
    const variant = selectQualityVariant(variants);
    if (!variant) {
      return json({ error: "Es konnte keine passende Referenz ausgewählt werden." }, 422);
    }
    const quality = floorplanQuality(variant);
    if (!customerFacingQualityPassed(quality)) {
      return json({
        error: "Der ausgewählte Grundriss hat die harten Geometrieprüfungen nicht bestanden.",
        reference_layout_id: variant.metrics.referenceLayoutId,
        failed_checks: quality.failedChecks,
        critical_failures: quality.criticalFailures,
      }, 422);
    }
    const classification = classifyZuhausefinderFloorplan(source, brief, variant, quality);
    const sourceRequest = source as {
      request_id?: string;
      design_fingerprint?: string;
      output_requirements?: { mandatory_label?: string };
    };
    const svg = assertSafeGeneratedSvg(renderFloorplanSvg(variant, {
      requestId: sourceRequest.request_id,
      mandatoryLabel: sourceRequest.output_requirements?.mandatory_label,
    }));
    const visualizationContext = buildZuhausefinderVisualizationContext(
      source,
      brief,
      variant,
    );
    let guidePng: Buffer;
    try {
      guidePng = await renderPlanGeometryGuidePng(variant);
    } catch {
      return json({
        error: "Der Grundriss wurde erstellt, aber der sichere Geometrieleitfaden konnte nicht gerendert werden.",
      }, 500);
    }
    const svgBytes = Buffer.from(svg, "utf8");
    return json({
      schema: "dmh-floorplan-result-v2",
      request_id: sourceRequest.request_id,
      design_fingerprint: sourceRequest.design_fingerprint,
      mime_type: "image/svg+xml",
      filename: `zuhausefinder-${sourceRequest.request_id}.svg`,
      file_base64: svgBytes.toString("base64"),
      artifact_sha256: sha256Hex(svgBytes),
      generator: {
        version: REFERENCE_GENERATOR_VERSION,
        reference_layout_id: variant.metrics.referenceLayoutId,
        score: variant.score,
        floor_count: variant.floors.length,
        storey_type: variant.storeyType,
        stair_core_id: variant.stairCore?.id ?? null,
        stair_geometry: variant.stairCore?.geometry ?? null,
        failed_checks: quality.failedChecks,
        critical_failures: quality.criticalFailures,
        quality_status: classification.geometry_quality,
      },
      classification,
      visualization_context: visualizationContext,
      reference_images: [
        {
          role: "plan_geometry_guide",
          mime_type: "image/png",
          file_base64: guidePng.toString("base64"),
          sha256: sha256Hex(guidePng),
          width: 1024,
          height: 1024,
        },
      ],
    });
  } catch (error) {
    const message = error instanceof Error ? error.message : "Ungültiges Grundriss-Briefing.";
    return json({ error: message }, 400);
  }
}
