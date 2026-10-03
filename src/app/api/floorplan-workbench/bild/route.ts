/**
 * Ein einzelnes Bild aus dem Katalog entfernen.
 *
 * Rainer, 2026-08-20: "mach doch kelein mülleinmer ran zum löschen" -- die
 * Baselines liegen neben den fertigen Bildern und sollen weg, ohne dafuer ins
 * wp-admin zu wechseln.
 *
 * WordPress kennt fuer Anhaenge keinen Papierkorb: DELETE ohne `force` wird
 * abgelehnt, mit `force=true` ist es endgueltig.
 *
 * Zwei Schritte, nicht einer. Codex, 2026-08-20, zur ersten Fassung: "Die
 * Zuordnung wird gelesen und danach separat geloescht -- ein TOCTOU-Fenster.
 * Es gibt kein CSRF-/Action-Token und keine erneute serverseitige Bestaetigung
 * gegen das konkrete WP-Medium unmittelbar vor der endgueltigen Loeschung."
 *
 *   1. POST {plan, id}          -> pruefen und eine kurzlebige Marke ausgeben,
 *                                  zusammen mit dem echten Dateinamen aus der
 *                                  Mediathek, damit die Rueckfrage zeigt, was
 *                                  wirklich getroffen wird.
 *   2. POST {plan, id, marke}   -> unmittelbar vor dem DELETE das Medium SELBST
 *                                  noch einmal holen und pruefen, dass sein
 *                                  Dateiname mit "<plan>-" beginnt. Das ist das
 *                                  Merkmal, an dem der Katalog Bild und Haus
 *                                  verknuepft (publish-renders.py), und es
 *                                  haengt am Medium, nicht an einer Liste, die
 *                                  inzwischen veraltet sein kann.
 *
 * Die Datei auf der Platte bleibt: geloescht wird die Kopie in der Mediathek,
 * nicht das Render im go-baseline-Ordner.
 */
import { readFile } from "node:fs/promises";
import { randomUUID } from "node:crypto";
import { join, resolve } from "node:path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

const SITE = (process.env.B2T_SITE || "https://born2thrill.de").replace(/\/+$/, "");

/** Ausgegebene Loeschmarken. Kurzlebig und einmalig. */
const MARKEN = new Map<string, { plan: string; id: number; bis: number }>();
const MARKE_GILT_MS = 90_000;

function markeAusgeben(plan: string, id: number) {
  const marke = randomUUID();
  const jetzt = Date.now();
  for (const [schluessel, wert] of MARKEN) if (wert.bis < jetzt) MARKEN.delete(schluessel);
  MARKEN.set(marke, { plan, id, bis: jetzt + MARKE_GILT_MS });
  return marke;
}

function markeEinloesen(marke: string, plan: string, id: number) {
  const wert = MARKEN.get(marke);
  if (!wert) return false;
  MARKEN.delete(marke);                       // genau einmal gueltig
  return wert.bis >= Date.now() && wert.plan === plan && wert.id === id;
}

function normalizedHostname(value: string) {
  const first = value.split(",")[0]?.trim().toLowerCase() || "";
  if (first.startsWith("[")) return first.slice(1, first.indexOf("]"));
  return first.split(":")[0];
}

function enabled(request: Request) {
  const urlHost = new URL(request.url).hostname.toLowerCase();
  const headerHost = normalizedHostname(
    request.headers.get("x-forwarded-host") || request.headers.get("host") || "",
  );
  return process.env.FLOORPLAN_WORKBENCH_ENABLED === "true"
    && ["127.0.0.1", "localhost", "::1"].includes(urlHost)
    && ["127.0.0.1", "localhost", "::1"].includes(headerHost);
}

/** Zugangsdaten wie publish-renders.py: Umgebung zuerst, sonst .env.local. */
async function zugang() {
  let user = process.env.WP_USER;
  let pass = process.env.WP_APP_PASSWORD;
  if (!user || !pass) {
    try {
      const suite = resolve(process.cwd(), "..");
      const text = await readFile(
        join(suite, "born2thrill-local-workbench", ".env.local"), "utf8");
      for (const zeile of text.split(/\r?\n/)) {
        const [name, ...rest] = zeile.split("=");
        const wert = rest.join("=").trim().replace(/^["']|["']$/g, "");
        if (name?.trim() === "WP_USER" && !user) user = wert;
        if (name?.trim() === "WP_APP_PASSWORD" && !pass) pass = wert;
      }
    } catch { /* ohne Datei bleibt es bei der Umgebung */ }
  }
  if (!user || !pass) return null;
  return "Basic " + Buffer.from(`${user}:${pass}`).toString("base64");
}

/** Der Dateiname, unter dem das Medium in der Bibliothek liegt. */
function dateiname(medium: any) {
  const quelle = String(medium?.source_url || "");
  const ausUrl = quelle.split("/").pop() || "";
  return String(medium?.slug || ausUrl || "");
}

/** Gehoert dieses Medium wirklich zu diesem Haus? */
function gehoertZu(medium: any, plan: string) {
  const name = dateiname(medium).toLowerCase();
  return name.startsWith(plan.toLowerCase() + "-");
}

export async function POST(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });

  const body = await request.json().catch(() => ({}));
  const plan = String(body.plan || "");
  const id = Number(body.id);
  const marke = body.marke ? String(body.marke) : "";
  if (!/^[A-Za-z0-9_.-]+$/.test(plan) || !Number.isInteger(id) || id <= 0) {
    return Response.json({ error: "Plan oder Bild-id fehlt." }, { status: 400 });
  }

  const auth = await zugang();
  if (!auth) {
    return Response.json({ error: "WP_USER / WP_APP_PASSWORD fehlen." }, { status: 400 });
  }

  // Das Medium selbst, nicht eine Liste ueber es. Diese Abfrage steht bewusst
  // unmittelbar vor dem DELETE.
  const medium = await fetch(`${SITE}/wp-json/wp/v2/media/${id}?context=edit`, {
    headers: { Authorization: auth }, cache: "no-store",
  }).then((r) => (r.ok ? r.json() : null)).catch(() => null);
  if (!medium || !Number.isInteger(Number(medium.id))) {
    return Response.json({ error: `Bild ${id} gibt es in der Mediathek nicht.` },
      { status: 404 });
  }
  if (!gehoertZu(medium, plan)) {
    return Response.json({
      error: `Bild ${id} heisst "${dateiname(medium)}" und gehoert damit nicht `
        + `zu ${plan}. Nicht geloescht.`,
    }, { status: 409 });
  }

  // Schritt 1: nur pruefen und die Marke ausgeben.
  if (!marke) {
    return Response.json({
      bestaetigen: true, id, plan, name: dateiname(medium),
      marke: markeAusgeben(plan, id),
      hinweis: "WordPress legt Anhaenge nicht in den Papierkorb. Das Loeschen "
        + "ist endgueltig; die Datei im Render-Ordner bleibt.",
    }, { headers: { "Cache-Control": "no-store" } });
  }

  // Schritt 2: Marke einloesen und loeschen.
  if (!markeEinloesen(marke, plan, id)) {
    return Response.json({ error: "Die Bestaetigung ist abgelaufen. Noch einmal." },
      { status: 409 });
  }

  const antwort = await fetch(`${SITE}/wp-json/wp/v2/media/${id}?force=true`, {
    method: "DELETE",
    headers: { Authorization: auth },
  });
  if (!antwort.ok) {
    const text = await antwort.text();
    return Response.json({ error: `WordPress: ${antwort.status} ${text.slice(0, 200)}` },
      { status: 502 });
  }
  return Response.json({ ok: true, id, name: dateiname(medium) },
    { headers: { "Cache-Control": "no-store" } });
}
