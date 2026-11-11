/**
 * Ein einzelnes Bild an Kunden freigeben oder wieder zurueckziehen.
 *
 * Der Katalog kann das (b2t/v1/freigabe, {id, send}) -- gemessen am
 * 2026-08-25: Abhaken ueber die Route liefert sauber {"id":87,"send":false}.
 * Auf der Katalogseite selbst liess sich der Haken trotzdem nicht loesen
 * (Rainer: "the checkmark an Kunden i cannot uncheck"), das Skript dort ist
 * kaputt. Diese Route stellt denselben Schalter in der Werkbank bereit, wo
 * der Weg nachweislich funktioniert.
 *
 * POST { plan, id, send } -> Haken setzen oder loesen.
 *
 * Zugangsdaten bleiben serverseitig (WP_USER + WP_APP_PASSWORD), wie beim
 * Hochladen und beim Titelbild; der Browser sieht sie nie.
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
  const send = Boolean(body.send);
  try {
    const antwort = await fetch(`${SITE}/wp-json/b2t/v1/freigabe`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: authorization },
      body: JSON.stringify({ id, send }),
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
    // Die Route selbst antwortet {id, send} (gemessen 2026-08-25). Widerspricht
    // das dem Gewollten, war es kein Erfolg.
    if (typeof geprueft.daten?.send === "boolean" && geprueft.daten.send !== send) {
      return Response.json({ error: `Katalog meldet send=${geprueft.daten.send}, gewollt war ${send}.` },
                           { status: 502 });
    }
    const blick = await bildZeile(plan, id);
    if (blick.art === "offen") {
      return Response.json({ ok: true, id, send, bestaetigt: false,
        warnung: `Geschrieben, aber nicht bestaetigt (${blick.grund}). Nicht erneut klicken -- Bilder neu laden.` });
    }
    // Runde 3 (Codex): eine Zeile ohne boolesches send ist "nicht bestaetigbar",
    // kein Widerspruch -- sonst meldet die Seite einen Fehler, der keiner ist.
    if (typeof blick.zeile.send !== "boolean") {
      return Response.json({ ok: true, id, send, bestaetigt: false,
        warnung: "Geschrieben, aber nicht bestaetigt (Bildzeile ohne send-Feld). Nicht erneut klicken -- Bilder neu laden." });
    }
    if (blick.zeile.send !== send) {
      return Response.json({ error: `Nicht uebernommen: der Katalog zeigt Bild ${id} mit send=${blick.zeile.send}.` },
        { status: 502 });
    }
    return Response.json({ ok: true, id, send, bestaetigt: true });
  } catch (error) {
    return Response.json({ error: error instanceof Error ? error.message : String(error) },
                         { status: 502 });
  }
}
