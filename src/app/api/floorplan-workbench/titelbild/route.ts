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

const FRIST_MS = 30_000;

/** Antwort als JSON lesen; ein WP_Error ({code, message}) oder HTML ist ein
 *  Fehler, auch mit HTTP 200 (ZUVERLAESSIGKEIT-001 B6). */
function katalogAntwort(text: string): { ok: true; daten: any } | { ok: false; fehler: string } {
  let daten: any;
  try { daten = JSON.parse(text); } catch {
    return { ok: false, fehler: `Katalog antwortet nicht mit JSON: ${text.slice(0, 160)}` };
  }
  if (daten && typeof daten === "object" && typeof daten.code === "string" && "message" in daten) {
    return { ok: false, fehler: `Katalog meldet ${daten.code}: ${String(daten.message).slice(0, 160)}` };
  }
  if (daten && typeof daten === "object" && (daten.ok === false || daten.success === false)) {
    return { ok: false, fehler: `Katalog meldet Fehlschlag: ${text.slice(0, 160)}` };
  }
  return { ok: true, daten };
}

/** Nicht melden, was geschickt wurde, sondern was der Katalog jetzt sagt:
 *  die Bildzeile aus b2t/v1/bilder (sie traegt send und cover).
 *  Runde 2: "nicht lesbar" (Zeitlimit, HTTP-Fehler, kein Array) ist etwas
 *  anderes als "liest einen anderen Wert" -- das erste heisst nur
 *  "geschrieben, Bestaetigung offen", das zweite ist ein Fehlschlag. */
type Rueckblick = { art: "zeile"; zeile: any } | { art: "offen"; grund: string };

async function bildZeile(plan: string, id: number): Promise<Rueckblick> {
  try {
    const antwort = await fetch(`${SITE}/wp-json/b2t/v1/bilder?plan=${encodeURIComponent(plan)}`,
      { cache: "no-store", signal: AbortSignal.timeout(FRIST_MS) });
    if (!antwort.ok) return { art: "offen", grund: `Bildliste HTTP ${antwort.status}` };
    const liste = await antwort.json().catch(() => null);
    if (!Array.isArray(liste)) return { art: "offen", grund: "Bildliste ist keine Liste" };
    const zeile = liste.find((b: any) => Number(b?.id) === id);
    if (!zeile) return { art: "offen", grund: `Bild ${id} steht (noch) nicht in der Bildliste von ${plan}` };
    return { art: "zeile", zeile };
  } catch (error) {
    return { art: "offen", grund: `Bildliste nicht lesbar: ${error instanceof Error ? error.message : String(error)}` };
  }
}

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
  const plan = /^[A-Za-z0-9_.-]+$/.test(String(body.plan || "")) ? String(body.plan) : "";
  if (!Number.isInteger(id) || id <= 0) {
    return Response.json({ error: "Bild-Id fehlt." }, { status: 400 });
  }
  // Runde 2: ohne Plan kann nichts zurueckgelesen werden -- dann lieber gar
  // nicht schreiben als einen unbestaetigten "Erfolg" melden.
  if (!plan) {
    return Response.json({ error: "Plan fehlt." }, { status: 400 });
  }
  try {
    const antwort = await fetch(`${SITE}/wp-json/b2t/v1/titelbild`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: authorization },
      body: JSON.stringify({ id }),
      cache: "no-store",
      signal: AbortSignal.timeout(FRIST_MS),
    });
    const text = await antwort.text();
    if (!antwort.ok) {
      return Response.json({ error: `Katalog antwortet ${antwort.status}: ${text.slice(0, 200)}` },
                           { status: 502 });
    }
    const geprueft = katalogAntwort(text);
    if (!geprueft.ok) return Response.json({ error: geprueft.fehler }, { status: 502 });
    const blick = await bildZeile(plan, id);
    if (blick.art === "offen") {
      return Response.json({ ok: true, id, bestaetigt: false,
        warnung: `Geschrieben, aber nicht bestaetigt (${blick.grund}). Nicht erneut klicken -- Bilder neu laden.` });
    }
    // Runde 3 (Codex): eine Zeile ohne boolesches cover ist "nicht bestaetigbar",
    // kein Widerspruch.
    if (typeof blick.zeile.cover !== "boolean") {
      return Response.json({ ok: true, id, bestaetigt: false,
        warnung: "Geschrieben, aber nicht bestaetigt (Bildzeile ohne cover-Feld). Nicht erneut klicken -- Bilder neu laden." });
    }
    if (blick.zeile.cover !== true) {
      return Response.json({ error: `Nicht uebernommen: Bild ${id} ist im Katalog nicht das Titelbild.` },
        { status: 502 });
    }
    return Response.json({ ok: true, id, bestaetigt: true });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : String(error) },
                         { status: 502 });
  }
}
