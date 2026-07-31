import { timingSafeEqual } from "node:crypto";
import { type HouseBrief } from "@/lib/generator/floorplan";
import {
  CORRECTED_FLOORPLAN_GENERATOR_VERSION,
  correctedFloorplanForBrief,
  renderCorrectedFloorplanArtifacts,
} from "@/lib/generator/corrected-floorplan";
import {
  classifyZuhausefinderFloorplan,
  mapZuhausefinderBrief,
} from "@/lib/generator/zuhausefinder-brief.mjs";
import { floorplanQuality } from "@/lib/generator/floorplan-svg.mjs";
import {
  buildZuhausefinderVisualizationContext,
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
    output: "base64-jpeg-and-png-guide",
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
    const referenceUsageScope: NonNullable<HouseBrief["referenceUsageScope"]> =
      "internal_reference_only";
    const brief = {
      ...(mapZuhausefinderBrief(source) as HouseBrief),
      referenceUsageScope,
    };
    const corrected = correctedFloorplanForBrief(brief);
    if (!corrected || !corrected.wordpressEligible) {
      return json({
        error: "F\u00fcr diese Geschossigkeit und dieses Raumprogramm ist noch kein freigegebener korrigierter Grundriss verf\u00fcgbar.",
        requested_storey_type: brief.storeyType,
        approved_catalog_required: true,
      }, 422);
    }

    const variant = corrected.variant;
    const quality = floorplanQuality(variant);
    const customerReady = true;

    const classification = classifyZuhausefinderFloorplan(
      source,
      brief,
      variant,
      quality,
    );
    const sourceRequest = source as {
      request_id?: string;
      design_fingerprint?: string;
      output_requirements?: { mandatory_label?: string };
    };
    const visualizationContext = buildZuhausefinderVisualizationContext(
      source,
      brief,
      variant,
    );

    let guidePng: Buffer;
    let floorplanJpeg: Buffer;
    try {
      const artifacts = await renderCorrectedFloorplanArtifacts(
        corrected.document,
        {
          requestId: sourceRequest.request_id,
          mandatoryLabel: sourceRequest.output_requirements?.mandatory_label,
        },
      );
      floorplanJpeg = artifacts.jpeg;
      guidePng = artifacts.guide;
    } catch {
      return json({
        error: "Der Grundriss wurde erstellt, aber die sicheren Bildartefakte konnten nicht gerendert werden.",
      }, 500);
    }

    return json({
      schema: "dmh-floorplan-result-v2",
      request_id: sourceRequest.request_id,
      design_fingerprint: sourceRequest.design_fingerprint,
      mime_type: "image/jpeg",
      filename: `zuhausefinder-${sourceRequest.request_id}.jpg`,
      file_base64: floorplanJpeg.toString("base64"),
      artifact_sha256: sha256Hex(floorplanJpeg),
      generator: {
        version: CORRECTED_FLOORPLAN_GENERATOR_VERSION,
        reference_layout_id: variant.metrics.referenceLayoutId,
        reference_usage_scope: "commercial_generator",
        distribution_scope: corrected.distributionScope,
        rights_eligible_for_customer_delivery: true,
        geometry_revision: corrected.document.revision,
        canonical_geometry_sha256:
          corrected.document.geometry_hash
          ?? variant.canonicalGeometrySha256
          ?? null,
        score: variant.score,
        floor_count: variant.floors.length,
        storey_type: variant.storeyType,
        stair_core_id: variant.stairCore?.id ?? null,
        stair_geometry: variant.stairCore?.geometry ?? null,
        failed_checks: quality.failedChecks,
        critical_failures: quality.criticalFailures,
        quality_status: classification.geometry_quality,
        customer_ready: customerReady,
        manual_review_required: false,
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
    const message = error instanceof Error
      ? error.message
      : "Ungültiges Grundriss-Briefing.";
    return json({ error: message }, 400);
  }
}
