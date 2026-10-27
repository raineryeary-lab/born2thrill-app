/**
 * Eine Wahrheit fuer Dachform und Massstab eines Hauses -- JS-Seite.
 *
 * Beide Angaben liegen in ZWEI Dateien nebeneinander:
 *
 *   projects/<plan>/annotations.json    die Zeichnung des Nutzers
 *   projects/<plan>/gebaeudemass.json   die spaeter eingetragene Messung
 *
 * VORRANGREGEL, ueberall gleich und PRO FELD: annotations.json gewinnt; ist
 * das Feld dort leer, zaehlt gebaeudemass.json. Das ist das Verhalten des
 * Bauens (scripts/build-simplifier-render-plan.py) -- der Bau ist die
 * Wahrheit, die Anzeigen richten sich danach, nicht umgekehrt.
 *
 * Dieselbe Regel und dieselben Feldnamen wie scripts/hausdaten.py. Wer hier
 * etwas aendert, aendert es dort mit; die Tests beider Seiten pruefen dieselben
 * vier Faelle.
 *
 * Gelesen wird nur -- geschrieben wird weiter dort, wo es heute geschieht.
 */
import { readFile } from "node:fs/promises";
import { join } from "node:path";

/** Woran man erkennt, dass ueberhaupt ein Gebaeudemass eingetragen wurde.
 *  Die Dachform gehoert NICHT dazu: sie in die Massstabs-Pruefung zu mischen
 *  war genau der Fehler der Statusroute. */
const MASS_FELDER = ["floor_scale", "rahmen_m", "gebaeude_breite_m", "gebaeude_tiefe_m"];

async function liesJson(pfad) {
  try {
    // BOM abschneiden: die Python-Seite liest mit utf-8-sig, und ohne das
    // hier war cubicasa_review_high_quality_architectural_904 fuer den Bau
    // ein Haus und fuer die Statusliste keins.
    const text = await readFile(pfad, "utf8");
    return JSON.parse(text.charCodeAt(0) === 0xfeff ? text.slice(1) : text);
  } catch {
    return null;
  }
}

/** Leere Zeichenketten, leere Objekte und null zaehlen als nicht gesetzt. */
export function gesetzt(wert) {
  if (wert === null || wert === undefined) return false;
  if (typeof wert === "string") return wert.trim().length > 0;
  if (Array.isArray(wert)) return wert.length > 0;
  if (typeof wert === "object") return Object.keys(wert).length > 0;
  return Boolean(wert);
}

function waehle(annotationen, sidecar, feld) {
  if (gesetzt(annotationen[feld])) return [annotationen[feld], "annotations"];
  if (gesetzt(sidecar[feld])) return [sidecar[feld], "gebaeudemass"];
  return [null, null];
}

/** floor_scale pro GESCHOSS zusammenfuehren: ein gemessenes Erdgeschoss
 *  schlaegt den eingetragenen Wert, ein Obergeschoss, das nur im Sidecar
 *  steht, geht trotzdem nicht verloren. */
function massstab(annotationen, sidecar) {
  const ausSidecar = (sidecar.floor_scale && typeof sidecar.floor_scale === "object")
    ? sidecar.floor_scale : {};
  const ausAnnotation = (annotationen.floor_scale && typeof annotationen.floor_scale === "object")
    ? annotationen.floor_scale : {};
  const zusammen = {};
  for (const quelle of [ausSidecar, ausAnnotation]) {
    for (const [geschoss, wert] of Object.entries(quelle)) {
      if (gesetzt(wert)) zusammen[geschoss] = wert;
    }
  }
  if (!Object.keys(zusammen).length) return [{}, null];
  const ausZeichnung = Object.values(ausAnnotation).some(gesetzt);
  return [zusammen, ausZeichnung ? "annotations" : "gebaeudemass"];
}

/**
 * @param {string} projektOrdner projects/<plan>
 * @returns {Promise<{dachform_modern: any, dachform_classic: any,
 *   floor_scale: Record<string, any>, annotation_space: any,
 *   gebaeudemass: Record<string, any>, hat_gebaeudemass: boolean,
 *   annotationen: any, herkunft: Record<string, string|null>}>}
 */
export async function hausdaten(projektOrdner) {
  const annotationen = await liesJson(join(projektOrdner, "annotations.json"));
  const sidecar = await liesJson(join(projektOrdner, "gebaeudemass.json"));
  const a = (annotationen && typeof annotationen === "object") ? annotationen : {};
  const g = (sidecar && typeof sidecar === "object") ? sidecar : {};

  const [modern, herkunftModern] = waehle(a, g, "roof_type_modern");
  const [classic, herkunftClassic] = waehle(a, g, "roof_type_classic");
  const [scale, herkunftScale] = massstab(a, g);
  const [raum, herkunftRaum] = waehle(a, g, "annotation_space");

  return {
    annotationen: (annotationen && typeof annotationen === "object") ? annotationen : null,
    gebaeudemass: g,
    dachform_modern: modern,
    dachform_classic: classic,
    floor_scale: scale,
    annotation_space: raum,
    hat_gebaeudemass: MASS_FELDER.some((feld) => gesetzt(g[feld])),
    herkunft: {
      dachform_modern: herkunftModern,
      dachform_classic: herkunftClassic,
      floor_scale: herkunftScale,
      annotation_space: herkunftRaum,
    },
  };
}
