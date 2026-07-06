import { NextResponse } from "next/server";
import { createPresignedPutUrl, hasObjectStorageConfig } from "@/lib/storage/object-storage";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const sourceTypes = new Set(["bestseller", "cubicasa", "simplifier", "user_test", "other"]);

type PresignBody = {
  source_type?: string;
  filename?: string;
};

function sanitizeFilename(filename: string) {
  const extension = filename.includes(".") ? `.${filename.split(".").pop()}` : "";
  const base = filename.replace(extension, "");

  return `${base
    .normalize("NFKD")
    .replace(/[\u0300-\u036f]/g, "")
    .replace(/[^a-zA-Z0-9-_]+/g, "-")
    .replace(/^-+|-+$/g, "")
    .slice(0, 80) || "upload"}${extension.toLowerCase()}`;
}

function errorResponse(message: string, status = 400) {
  return NextResponse.json({ error: message }, { status });
}

function safeErrorMessage(error: unknown) {
  if (error instanceof Error) return error.message;
  return "Unknown server error.";
}

export async function POST(request: Request) {
  try {
    if (!hasObjectStorageConfig()) {
      return errorResponse(
        "Object Storage ist noch nicht konfiguriert. Bitte OBJECT_STORAGE_ENDPOINT, OBJECT_STORAGE_BUCKET, OBJECT_STORAGE_ACCESS_KEY_ID und OBJECT_STORAGE_SECRET_ACCESS_KEY in Railway setzen.",
        503,
      );
    }

    const body = (await request.json()) as PresignBody;

    if (!body.source_type || !sourceTypes.has(body.source_type)) {
      return errorResponse("Invalid source_type.");
    }

    if (!body.filename) {
      return errorResponse("Missing filename.");
    }

    const uploadId = crypto.randomUUID();
    const dateFolder = new Date().toISOString().slice(0, 10);
    const safeFilename = sanitizeFilename(body.filename);
    const storagePath = `${body.source_type}/${dateFolder}/${uploadId}-${safeFilename}`;
    const upload = createPresignedPutUrl(storagePath);

    return NextResponse.json({
      upload_id: uploadId,
      storage_provider: upload.provider,
      storage_bucket: upload.bucket,
      storage_path: upload.path,
      upload_url: upload.url,
      public_url: upload.publicUrl,
      expires_at: upload.expiresAt,
    });
  } catch (error) {
    return errorResponse(`Upload-Adresse konnte nicht erstellt werden: ${safeErrorMessage(error)}`, 500);
  }
}

