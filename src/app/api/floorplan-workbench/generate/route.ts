import { generateVariants, parseBrief } from "@/lib/generator/floorplan";

export const dynamic = "force-dynamic";

function normalizedHostname(value: string) {
  const firstHost = value.split(",")[0]?.trim().toLowerCase() ?? "";
  if (firstHost.startsWith("[")) {
    return firstHost.slice(1, firstHost.indexOf("]"));
  }
  return firstHost.split(":")[0];
}

function isLocalHostname(hostname: string) {
  return hostname === "127.0.0.1" || hostname === "localhost" || hostname === "::1";
}

function isLocalRequest(request: Request) {
  const urlHostname = new URL(request.url).hostname.toLowerCase();
  const forwardedHost = request.headers.get("x-forwarded-host");
  const headerHostname = normalizedHostname(
    forwardedHost || request.headers.get("host") || "",
  );
  return isLocalHostname(urlHostname) && isLocalHostname(headerHostname);
}

function normalizedEntries(value: unknown): Array<[string, string]> | null {
  if (!Array.isArray(value) || value.length > 200) return null;
  const entries: Array<[string, string]> = [];
  for (const item of value) {
    if (!Array.isArray(item) || item.length !== 2) return null;
    const name = String(item[0] ?? "").trim().slice(0, 80);
    const fieldValue = String(item[1] ?? "").trim().slice(0, 2_000);
    if (!name) return null;
    entries.push([name, fieldValue]);
  }
  return entries;
}

export async function POST(request: Request) {
  if (
    process.env.FLOORPLAN_WORKBENCH_ENABLED !== "true"
    || !isLocalRequest(request)
  ) {
    return Response.json(
      { error: "Der Grundriss-Arbeitsplatz ist nur lokal aktiviert." },
      { status: 404 },
    );
  }

  let body: unknown;
  try {
    body = await request.json();
  } catch {
    return Response.json({ error: "Ungültige JSON-Anfrage." }, { status: 400 });
  }

  const entries = normalizedEntries(
    body && typeof body === "object" ? (body as { entries?: unknown }).entries : null,
  );
  if (!entries) {
    return Response.json({ error: "Ungültige Eingabefelder." }, { status: 400 });
  }

  const brief = parseBrief(entries);
  const variants = generateVariants(brief);
  return Response.json(
    { brief, variants },
    { headers: { "Cache-Control": "no-store" } },
  );
}
