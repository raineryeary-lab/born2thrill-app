#!/usr/bin/env node
// One-off test batch: generate a handful of real 3D furniture meshes via the
// Tripo3D API to validate quality/scale before committing to the full
// 30-piece catalog. See plans/furnished-3d-dollhouse-render-v1.md.
//
// Run with: node --env-file=.env.local scripts/tripo-generate-furniture-test.mjs
//
// No texture/PBR requested (texture:false, pbr:false) — per Rainer's
// decision, colour/material variation is applied procedurally in Blender at
// render time (see FURNITURE_FINISHES in furniture-catalog.mjs), not baked
// into the generated mesh. This halves the per-piece credit cost (10 vs 20).

import { mkdir, writeFile } from "node:fs/promises";
import path from "node:path";

const API_KEY = process.env.TRIPO_API_KEY;
if (!API_KEY) {
  console.error("TRIPO_API_KEY not set. Run with: node --env-file=.env.local scripts/tripo-generate-furniture-test.mjs");
  process.exit(1);
}

const BASE_URL = "https://openapi.tripo3d.ai/v3";
const OUTPUT_DIR = path.resolve("data/furniture-assets/test-batch");

const NEGATIVE_PROMPT =
  "blurry, low quality, broken mesh, floating geometry, disconnected parts, bedding, pillows, cushion clutter, decorative props, text, watermark, room background, floor, wall, multiple objects";

const TEST_ITEMS = [
  {
    type: "bed_double",
    style: "modern",
    prompt:
      "A modern double bed frame, minimalist upholstered low headboard, clean straight lines, tapered wooden legs, no bedding or pillows, standalone furniture product shot, plain white background",
  },
  {
    type: "bed_double",
    style: "classic",
    prompt:
      "A classic traditional double bed frame, ornate carved wooden headboard, turned wooden legs, elegant traditional details, no bedding or pillows, standalone furniture product shot, plain white background",
  },
  {
    type: "sofa",
    style: "modern",
    prompt:
      "A modern minimalist three-seat sofa, clean straight lines, low profile, slim tapered wooden legs, no throw pillows, standalone furniture product shot, plain white background",
  },
  {
    type: "sofa",
    style: "classic",
    prompt: "A classic traditional three-seat sofa, rolled arms, tufted back cushions, turned wooden feet, standalone furniture product shot, plain white background",
  },
  {
    type: "dining_chair",
    style: "modern",
    prompt: "A modern minimalist dining chair, molded seat shell, slim tapered wooden legs, no armrests, standalone furniture product shot, plain white background",
  },
  {
    type: "dining_chair",
    style: "classic",
    prompt: "A classic traditional wooden dining chair, carved backrest, turned legs, upholstered seat pad, standalone furniture product shot, plain white background",
  },
];

async function submitTask(item) {
  const response = await fetch(`${BASE_URL}/generation/text-to-model`, {
    method: "POST",
    headers: { Authorization: `Bearer ${API_KEY}`, "Content-Type": "application/json" },
    body: JSON.stringify({
      prompt: item.prompt,
      negative_prompt: NEGATIVE_PROMPT,
      model: "v3.1-20260211",
      texture: false,
      pbr: false,
      geometry_quality: "detailed",
      face_limit: 30000,
      export_uv: false,
    }),
  });
  const body = await response.json();
  if (!response.ok || body.code !== 0) throw new Error(`Submit failed for ${item.type}/${item.style}: ${JSON.stringify(body)}`);
  return body.data.task_id;
}

async function pollTask(taskId, { intervalMs = 4000, timeoutMs = 5 * 60 * 1000 } = {}) {
  const deadline = Date.now() + timeoutMs;
  while (Date.now() < deadline) {
    const response = await fetch(`${BASE_URL}/tasks/${taskId}`, { headers: { Authorization: `Bearer ${API_KEY}` } });
    const body = await response.json();
    if (!response.ok || body.code !== 0) throw new Error(`Task query failed for ${taskId}: ${JSON.stringify(body)}`);
    const { status, progress } = body.data;
    process.stdout.write(`  task ${taskId}: ${status} (${progress}%)\n`);
    if (status === "success") return body.data;
    if (status === "failed" || status === "cancelled") throw new Error(`Task ${taskId} ${status}: ${body.data.error_message || "no error message"}`);
    await new Promise((resolve) => setTimeout(resolve, intervalMs));
  }
  throw new Error(`Task ${taskId} timed out after ${timeoutMs}ms`);
}

async function downloadFile(url, destPath) {
  const response = await fetch(url);
  if (!response.ok) throw new Error(`Download failed (${response.status}) for ${url}`);
  const buffer = Buffer.from(await response.arrayBuffer());
  await writeFile(destPath, buffer);
  return buffer.length;
}

async function main() {
  await mkdir(OUTPUT_DIR, { recursive: true });
  const results = [];
  let totalCredits = 0;

  for (const item of TEST_ITEMS) {
    const label = `${item.type}__${item.style}`;
    console.log(`Submitting ${label}...`);
    const taskId = await submitTask(item);
    console.log(`  task_id: ${taskId}`);
    const result = await pollTask(taskId);
    console.log(`  done, ${result.credits_consumed} credits consumed`);
    totalCredits += result.credits_consumed || 0;

    const modelPath = path.join(OUTPUT_DIR, `${label}.glb`);
    const previewPath = path.join(OUTPUT_DIR, `${label}.png`);
    const modelBytes = await downloadFile(result.output.model_url, modelPath);
    let previewBytes = 0;
    if (result.output.rendered_image_url) previewBytes = await downloadFile(result.output.rendered_image_url, previewPath);
    console.log(`  saved ${modelPath} (${modelBytes} bytes), preview ${previewBytes} bytes`);

    results.push({
      type: item.type,
      style: item.style,
      task_id: taskId,
      credits_consumed: result.credits_consumed,
      model_path: modelPath,
      preview_path: previewBytes ? previewPath : null,
    });
  }

  const manifestPath = path.join(OUTPUT_DIR, "test-batch-manifest.json");
  await writeFile(manifestPath, JSON.stringify({ generated_at: new Date().toISOString(), total_credits_consumed: totalCredits, items: results }, null, 2));
  console.log(`\nTest batch complete. Total credits consumed: ${totalCredits}`);
  console.log(`Manifest: ${manifestPath}`);
}

main().catch((error) => {
  console.error(error);
  process.exit(1);
});
