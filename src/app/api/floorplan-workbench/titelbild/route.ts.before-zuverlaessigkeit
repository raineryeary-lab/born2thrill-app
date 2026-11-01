/**
 * Titelbild eines Grundrisses setzen.
 *
 * Der Katalog kann das seit jeher (b2t/v1/titelbild, ein Bild-Id), aber die
 * Workbench hatte nie einen Knopf dafuer -- Rainer, 2026-08-23: "why can't I
 * pick the Titelbild anymore". Gesucht und nachgemessen: im ganzen Projekt
 * kam "titelbild" kein einziges Mal vor. Es fehlte also, statt kaputt zu
 * sein.
 *
 * POST { plan, id } -> setzt das Bild mit dieser Mediathek-Id als Titelbild.
 *
 * Zugangsdaten bleiben serverseitig (WP_USER + WP_APP_PASSWORD), genau wie
 * beim Hochladen; der Browser sieht sie nie.
 */
export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const SITE = (process.env.B2T_SITE || "https://born2thrill.de").replace(/\/+$/, "");

function normalizedHostname(value: string) {
  const first = value.split(",")[0]?.trim().toLowerCase() || "";
  if (first.startsWith("[")) return first.slice(1, first.indexOf("]"));
  return first.split(":")[0];
}

function enabled(request: Request) {
  const urlHost = new URL(request.url).hostname.toLowerCase();
  const headerHost = normalizedHostname(request.headers.get("host") || "");
  const erlaubt = new Set(["localhost", "127.0.0.1", "::1"]);
  return erlaubt.has(urlHost) && (!headerHost || erlaubt.has(headerHost));
}

function credentials() {
  const user = process.env.WP_USER?.trim();
  const password = process.env.WP_APP_PASSWORD?.trim();
  if (!user || !password) return null;
  return "Basic " + Buffer.from(`${user}:${password}`).toString("base64");
}

export async function POST(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });
  const authorization = credentials();
  if (!authorization) {
    return Response.json({ error: "Kein Zugang: WP_USER und WP_APP_PASSWORD fehlen." },
                         { status: 503 });
  }
  const body = await request.json().catch(() => ({}));
  const id = Number(body.id);
  if (!Number.isInteger(id) || id <= 0) {
    return Response.json({ error: "Bild-Id fehlt." }, { status: 400 });
  }
  try {
    const antwort = await fetch(`${SITE}/wp-json/b2t/v1/titelbild`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: authorization },
      body: JSON.stringify({ id }),
      cache: "no-store",
    });
    const text = await antwort.text();
    if (!antwort.ok) {
      return Response.json({ error: `Katalog antwortet ${antwort.status}: ${text.slice(0, 200)}` },
                           { status: 502 });
    }
    return Response.json({ ok: true, id });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : String(error) },
                         { status: 502 });
  }
}
