/**
 * Ist die Möblierung noch gültig, oder wurde die Geometrie darunter geändert?
 *
 * Rainer, 2026-08-20: "when changes are made in the Räume and exteriours then
 * the data has to be regenerated for the furnishing." Genau so ist es: Möbel
 * werden auf Räume gesetzt, und wenn die Räume danach umgezeichnet werden,
 * stehen sie gegen eine Geometrie, die es nicht mehr gibt -- ohne dass irgendwo
 * etwas rot wird.
 *
 * Der Vergleich geht über `geometry_hash`: die Korrektur-Revision hat den, aus
 * dem sie gebaut wurde, und /generate liefert den, der sich aus der HEUTIGEN
 * Annotation ergibt. Unterschiedlich heißt: umgezeichnet, seit die Möbel
 * gesetzt wurden.
 *
 * Nicht über Zeitstempel: eine Datei anzufassen ändert ihre mtime, ohne dass
 * sich an der Geometrie irgendetwas geändert hätte.
 */
import { readdir, readFile } from "node:fs/promises";
import { join, resolve } from "node:path";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

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

async function neuesteRevision(dataRoot: string, plan: string) {
  const ordner = join(dataRoot, "corrections", plan, "revisions");
  try {
    const namen = (await readdir(ordner)).filter((n) => n.endsWith(".json")).sort();
    if (namen.length === 0) return null;
    const roh = await readFile(join(ordner, namen[namen.length - 1]), "utf8");
    const doc = JSON.parse(roh);
    return { datei: namen[namen.length - 1], geometry_hash: doc.geometry_hash || null };
  } catch {
    return null;
  }
}

// Nur die echten Geschossdateien (floor-0.json, floor-1.json ...), nicht die
// Sicherungskopien daneben (floor-0.vor-vorderseite-2026-09-03.json).
const GESCHOSSDATEI = /^floor-\d+\.json$/;

async function moebelDateien(dataRoot: string, plan: string) {
  const ordner = join(dataRoot, "corrections", plan, "furniture");
  try {
    const namen = (await readdir(ordner)).filter((n) => GESCHOSSDATEI.test(n)).sort();
    const docs = [];
    for (const n of namen) {
      try { docs.push(JSON.parse(await readFile(join(ordner, n), "utf8"))); } catch { /* unlesbar: ueberspringen */ }
    }
    return docs;
  } catch {
    return [];
  }
}

// Der Koordinatenraum, in dem der Moebel-Schritt heute speichert -- dieselbe
// Geometrie, aus der gebaut wird (corrections/route.ts saveFurniture).
const BAU_GEOMETRIE = "render-geometry-mm-y-down-v1";

export async function GET(request: Request) {
  if (!enabled(request)) return Response.json({ error: "Local-only endpoint." }, { status: 404 });

  const plan = new URL(request.url).searchParams.get("plan") || "";
  if (!/^[A-Za-z0-9_.-]+$/.test(plan)) {
    return Response.json({ error: "Kein gültiger Plan." }, { status: 400 });
  }

  const suite = resolve(process.cwd(), "..");
  // Nicht raten. 2026-08-21: der Datenordner zog von C: nach E:; ein
  // stiller Rueckfall auf den alten C:-Nachbarordner wuerde unbemerkt
  // gegen veraltete Daten arbeiten (Codex-Review desselben Tages).
  const _konfiguriert = process.env.FLOORPLAN_WORKBENCH_DATA_DIR?.trim();
  if (!_konfiguriert) {
    throw new Error("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt -- "
      + "verweigere, den Datenordner zu erraten. Siehe .env.local.");
  }
  const dataRoot = resolve(_konfiguriert);

  const revision = await neuesteRevision(dataRoot, plan);
  const dateien = await moebelDateien(dataRoot, plan);
  const moebel = dateien.reduce((summe, d) => summe + (d.symbols || []).length, 0);

  // Der aktuelle Stand kommt aus derselben Quelle, die auch die Korrektur
  // speist -- sonst verglichen wir zwei verschiedene Rechnungen.
  let jetzt: string | null = null;
  let fehler: string | null = null;
  try {
    const url = new URL(request.url);
    url.pathname = "/api/floorplan-workbench/generate";
    url.search = `?reference=${encodeURIComponent(plan)}&transform=identity`;
    const antwort = await fetch(url.toString(), { cache: "no-store" });
    const daten = await antwort.json();
    jetzt = daten.geometry_hash || null;
    if (!antwort.ok) fehler = daten.error || "generate fehlgeschlagen";
  } catch (e) {
    fehler = String(e);
  }

  // MOEBEL-FREMD-FEHLALARM-001, 2026-10-07. Rainer: die Warnung "Moebel auf
  // fremder Geometrie" stand bei 11 Haeusern und ging durch Speichern im
  // Moebel-Schritt nie weg -- sie fragte nur, ob es eine Korrektur-Revision
  // gibt, und die schreibt der Moebel-Schritt nie. Seit der Moebel-Schritt die
  // Bau-Geometrie zeigt und jede Datei mit deren geometry_identity stempelt,
  // ist die echte Frage: passt der Stempel noch zur heutigen Geometrie?
  const mitMoebeln = dateien.filter((d) => (d.symbols || []).length > 0);
  const aufBauGeometrie = mitMoebeln.filter((d) => d.coordinate_space === BAU_GEOMETRIE);
  const geschossVeraltet: string[] = [];
  if (aufBauGeometrie.length) {
    try {
      const url = new URL(request.url);
      url.pathname = "/api/floorplan-workbench/corrections";
      url.search = "";
      const antwort = await fetch(url.toString(), {
        method: "POST", cache: "no-store", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ action: "render_geometry", reference: plan }),
      });
      const daten = await antwort.json();
      const floors: any[] = daten?.geometry?.floors || [];
      for (const d of aufBauGeometrie) {
        const index = Number(String(d.floor_id || "").replace(/^floor-/, ""));
        const heute = floors[index]?.geometry_identity;
        if (heute && d.geometry_identity && heute !== d.geometry_identity) {
          geschossVeraltet.push(index === 0 ? "Erdgeschoss" : `${index}. Obergeschoss`);
        }
      }
    } catch (e) {
      fehler = fehler || String(e);
    }
  }

  const veraltet = Boolean(revision?.geometry_hash && jetzt && revision.geometry_hash !== jetzt)
    || geschossVeraltet.length > 0;

  // Ohne Revision baut die Pipeline aus der ANNOTATION, waehrend der
  // Moebeleditor die Geometrie des KORREKTUR-Kandidaten zeigt. Gemessen an
  // bungalow_039 am 2026-08-20: dieselben 7 Raeume, aber x 0..12500 im Editor
  // gegen x 1252..10261 im Bauplan, und in y ein anderes Verhaeltnis als in x.
  // Kein Versatz, keine Skalierung -- zwei verschieden gerechnete Grundrisse.
  // Wer hier moebliert, setzt Moebel in ein Haus, das so nie gebaut wird:
  // 15 von 29 landeten ausserhalb. Das muss man wissen, BEVOR man eine Stunde
  // lang Schraenke stellt.
  //
  // Heute gilt das nur noch fuer Moebel, die NICHT im Bau-Koordinatenraum
  // gespeichert sind (alte Dateien von vor der Umstellung).
  const geometrieFremd = Boolean(!revision
    && mitMoebeln.some((d) => d.coordinate_space !== BAU_GEOMETRIE));

  return Response.json({
    plan,
    moebel,
    revision: revision?.geometry_hash || null,
    jetzt,
    veraltet,
    geometrieFremd,
    // Ohne Revision gibt es nichts zu entwerten -- das Haus ist einfach noch
    // nicht durch den Korrektureditor gegangen.
    geschossVeraltet,
    grund: fehler ? fehler
      : geschossVeraltet.length ? `Räume umgezeichnet (${geschossVeraltet.join(", ")}), seit die Möbel gesetzt wurden`
      : !revision ? "noch keine Revision"
      : veraltet ? "Geometrie wurde geändert, seit die Möbel gesetzt wurden"
      : "aktuell",
  }, { headers: { "Cache-Control": "no-store" } });
}
