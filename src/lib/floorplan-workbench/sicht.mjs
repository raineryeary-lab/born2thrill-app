/**
 * Zoomen im Grundriss-Editor.
 *
 * Rainer, 2026-08-31: "can we add a zoom to the furniture setting? it would be
 * easier to place the furniture."
 *
 * Der SVG hat bisher einen festen viewBox aus den Geschossgrenzen. Ein Sofa
 * auf 30 mm genau zu setzen heisst, auf einem 680 px hohen Bild ein Haus von
 * 15 Metern zu treffen -- rund 22 mm je Bildschirmpunkt.
 *
 * Gezoomt wird ueber den viewBox und NICHT ueber eine CSS-Transformation:
 * `coordinate()` im Editor rechnet mit `getScreenCTM()`, und die kennt den
 * viewBox von selbst. Damit bleibt jede Maus-Rechnung unveraendert richtig --
 * kein zweiter Weg, auf dem sich Zeiger und Zeichnung auseinanderleben
 * koennen.
 *
 * Kein eigenes Verschieben. Wer um den Zeiger herum zoomt, verschiebt schon:
 * herauszoomen, Zeiger woandershin, hineinzoomen. Ein zusaetzlicher
 * Zieh-Modus muesste sich mit Setzen, Rahmen-Auswahl und Punkte-Ziehen um
 * dieselbe Maustaste streiten.
 */

export const ZOOM_MIN = 1;
export const ZOOM_MAX = 8;
export const ZOOM_SCHRITT = 1.25;

/** Zoom in die erlaubten Grenzen. */
export function zoomKlemmen(zoom) {
  if (!Number.isFinite(zoom)) return ZOOM_MIN;
  return Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, zoom));
}

/**
 * Der viewBox fuer eine Sicht.
 *
 * `sicht` ist null (alles zeigen) oder {zoom, cx, cy} -- cx/cy ist der Punkt
 * der ZEICHNUNG, der in der Mitte stehen soll.
 *
 * Die Mitte wird so begrenzt, dass der Ausschnitt im Grundriss bleibt: sonst
 * zoomt man einmal am Rand und sieht nur noch weisse Flaeche und sucht das
 * Haus.
 */
export function sichtKasten(kasten, sicht) {
  if (!sicht || zoomKlemmen(sicht.zoom) <= ZOOM_MIN) return kasten;
  const zoom = zoomKlemmen(sicht.zoom);
  const breite = kasten.width / zoom;
  const hoehe = kasten.height / zoom;
  const klemm = (wert, min, max) => Math.min(max, Math.max(min, wert));
  const cx = klemm(sicht.cx, kasten.minX + breite / 2,
                   kasten.minX + kasten.width - breite / 2);
  const cy = klemm(sicht.cy, kasten.minY + hoehe / 2,
                   kasten.minY + kasten.height - hoehe / 2);
  return { minX: cx - breite / 2, minY: cy - hoehe / 2,
           width: breite, height: hoehe };
}

/**
 * Zoomen, ohne dass der Punkt unter dem Zeiger wegrutscht.
 *
 * `anteil` ist die Lage des Zeigers im Bild, 0..1 je Achse. Der Punkt der
 * Zeichnung, der dort liegt, soll hinterher wieder dort liegen -- sonst
 * zoomt man an der Stelle vorbei, die man vergroessern wollte.
 */
export function zoomUmZeiger(kasten, sicht, neuerZoom, anteil) {
  const alt = sichtKasten(kasten, sicht);
  const zeigerX = alt.minX + anteil.x * alt.width;
  const zeigerY = alt.minY + anteil.y * alt.height;
  const zoom = zoomKlemmen(neuerZoom);
  if (zoom <= ZOOM_MIN) return null;              // wieder alles zeigen
  const breite = kasten.width / zoom;
  const hoehe = kasten.height / zoom;
  // Neue Mitte so, dass der Zeigerpunkt an derselben Bildstelle bleibt.
  return { zoom,
           cx: zeigerX + (0.5 - anteil.x) * breite,
           cy: zeigerY + (0.5 - anteil.y) * hoehe };
}
