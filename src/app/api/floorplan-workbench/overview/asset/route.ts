/**
 * Serves one image out of the inventory roots so the overview tab can show
 * thumbnails of renders and room concepts. Read-only: it opens files, it never
 * creates or modifies them.
 *
 * The path is always root-relative and is refused if it escapes its root, is
 * absolute, or does not end in an image extension. Raster images are downscaled
 * with sharp (already a dependency) because the baseline PNGs are 2-4 MB each
 * and a grid of full-size ones would be unusable.
 */
import { readFile, stat } from "node:fs/promises";
import sharp from "sharp";
import { resolveAssetPath } from "@/lib/floorplan-workbench/inventory";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const MIME_TYPES: Record<string, string> = {
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp",
  ".svg": "image/svg+xml",
};
const MAX_RAW_BYTES = 48 * 1024 * 1024;

function normalizedHostname(value: string) {
  const first = value.split(",")[0]?.trim().toLowerCase() || "";
  if (first.startsWith("[")) return first.slice(1, first.indexOf("]"));
  return first.split(":")[0];
}

function enabled(request: Request) {
  const urlHost = new URL(request.url).hostname.toLowerCase();
  const headerHost = normalizedHostname(request.headers.get("x-forwarded-host") || request.headers.get("host") || "");
  return process.env.FLOORPLAN_WORKBENCH_ENABLED === "true"
    && ["127.0.0.1", "localhost", "::1"].includes(urlHost)
    && ["127.0.0.1", "localhost", "::1"].includes(headerHost);
}

function extensionOf(value: string) {
  const dot = value.lastIndexOf(".");
  return dot < 0 ? "" : value.slice(dot).toLowerCase();
}

export async function GET(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const url = new URL(request.url);
  const rootKey = url.searchParams.get("root") || "";
  const relativePath = url.searchParams.get("path") || "";
  const target = resolveAssetPath(rootKey, relativePath);
  if (!target) return Response.json({ error: "Asset outside the inventory roots." }, { status: 404 });

  const extension = extensionOf(target);
  const mime = MIME_TYPES[extension];
  if (!mime) return Response.json({ error: "Only image assets are served." }, { status: 415 });

  const info = await stat(target).catch(() => null);
  if (!info || !info.isFile()) return Response.json({ error: "Asset not found." }, { status: 404 });
  if (info.size > MAX_RAW_BYTES) return Response.json({ error: "Asset too large to serve." }, { status: 413 });

  const bytes = await readFile(target);
  const widthParam = Number(url.searchParams.get("w"));
  const width = Number.isFinite(widthParam) ? Math.trunc(widthParam) : 0;

  // SVGs go out untouched; rasterising them would only lose fidelity.
  if (extension === ".svg" || width <= 0) {
    return new Response(new Uint8Array(bytes), {
      headers: {
        "Content-Type": mime,
        "Content-Length": String(bytes.length),
        "Cache-Control": "private, max-age=60",
        "Content-Disposition": "inline",
      },
    });
  }

  try {
    const thumbnail = await sharp(bytes)
      .resize({ width: Math.min(Math.max(width, 48), 2000), withoutEnlargement: true })
      .webp({ quality: 78 })
      .toBuffer();
    return new Response(new Uint8Array(thumbnail), {
      headers: {
        "Content-Type": "image/webp",
        "Content-Length": String(thumbnail.length),
        "Cache-Control": "private, max-age=60",
        "Content-Disposition": "inline",
      },
    });
  } catch {
    return new Response(new Uint8Array(bytes), {
      headers: { "Content-Type": mime, "Cache-Control": "private, max-age=60" },
    });
  }
}
