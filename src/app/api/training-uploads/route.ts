import { NextResponse } from "next/server";
import { hasDatabaseUrl, query } from "@/lib/db/postgres";
import { createClient } from "@/lib/supabase/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const sourceTypes = new Set(["bestseller", "cubicasa", "simplifier", "user_test", "other"]);

type TrainingUploadBody = {
  id?: string;
  source_type?: string;
  storage_bucket?: string;
  storage_path?: string;
  original_filename?: string;
  mime_type?: string | null;
  size_bytes?: number | null;
  notes?: string;
  metadata?: Record<string, unknown>;
};

function errorResponse(message: string, status = 400) {
  return NextResponse.json({ error: message }, { status });
}

export async function GET() {
  if (hasDatabaseUrl()) {
    const result = await query(
      `
        select
          id,
          created_at,
          source_type,
          storage_bucket,
          storage_path,
          original_filename,
          mime_type,
          size_bytes,
          notes,
          status
        from public.training_uploads
        order by created_at desc
        limit 20
      `,
    );

    return NextResponse.json({ uploads: result.rows, provider: "database" });
  }

  const supabase = await createClient();
  const { data, error } = await supabase
    .from("training_uploads")
    .select("id, created_at, source_type, storage_path, original_filename, mime_type, size_bytes, notes, status")
    .order("created_at", { ascending: false })
    .limit(20);

  if (error) return errorResponse(error.message, 500);
  return NextResponse.json({ uploads: data ?? [], provider: "supabase" });
}

export async function POST(request: Request) {
  const body = (await request.json()) as TrainingUploadBody;

  if (!body.source_type || !sourceTypes.has(body.source_type)) {
    return errorResponse("Invalid source_type.");
  }

  if (!body.storage_path || !body.original_filename) {
    return errorResponse("Missing storage_path or original_filename.");
  }

  const uploadId = body.id ?? crypto.randomUUID();
  const storageBucket = body.storage_bucket ?? "training-uploads";

  if (hasDatabaseUrl()) {
    const result = await query(
      `
        insert into public.training_uploads (
          id,
          source_type,
          storage_provider,
          storage_bucket,
          storage_path,
          original_filename,
          mime_type,
          size_bytes,
          notes,
          metadata
        )
        values ($1, $2, 'supabase', $3, $4, $5, $6, $7, $8, $9)
        returning
          id,
          created_at,
          source_type,
          storage_bucket,
          storage_path,
          original_filename,
          mime_type,
          size_bytes,
          notes,
          status
      `,
      [
        uploadId,
        body.source_type,
        storageBucket,
        body.storage_path,
        body.original_filename,
        body.mime_type ?? null,
        body.size_bytes ?? null,
        body.notes ?? "",
        body.metadata ?? {},
      ],
    );

    return NextResponse.json({ upload: result.rows[0], provider: "database" });
  }

  const supabase = await createClient();
  const { data, error } = await supabase
    .from("training_uploads")
    .insert({
      id: uploadId,
      source_type: body.source_type,
      storage_bucket: storageBucket,
      storage_path: body.storage_path,
      original_filename: body.original_filename,
      mime_type: body.mime_type ?? null,
      size_bytes: body.size_bytes ?? null,
      notes: body.notes ?? "",
      metadata: body.metadata ?? {},
    })
    .select("id, created_at, source_type, storage_path, original_filename, mime_type, size_bytes, notes, status")
    .single();

  if (error) return errorResponse(error.message, 500);
  return NextResponse.json({ upload: data, provider: "supabase" });
}
