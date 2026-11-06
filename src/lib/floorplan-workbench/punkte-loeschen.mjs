/**
 * Was "Löschen" an einem gezeichneten Lauf (Kuechenzeile, Vorwand ...) trifft.
 *
 * Rainer, 2026-11-03: "if one point on a küchenzeile is active and not the
 * whole zeile and i press on delete please just delete that one pont and not
 * the whole küchenzeile". Gewaehlte Punkte gehen, der Lauf bleibt. Ohne
 * Punktauswahl bleibt es beim ganzen Moebel. Unter zwei Punkte faellt ein
 * Lauf nie -- und dann wird auch nicht stattdessen das Ganze geloescht.
 *
 * @param {Array<[number, number]>|undefined} punkte  points_mm des Laufs
 * @param {number[]} auswahl  gewaehlte Punktindizes
 * @returns {{art: "punkte", punkte: Array<[number, number]>} | {art: "ganz"} | {art: "zuWenig"}}
 */
export function loeschZiel(punkte, auswahl) {
  if (!Array.isArray(punkte)) return { art: "ganz" };
  const weg = new Set((auswahl || []).filter((i) => Number.isInteger(i) && i >= 0 && i < punkte.length));
  if (!weg.size) return { art: "ganz" };
  const rest = punkte.filter((_, i) => !weg.has(i));
  if (rest.length < 2) return { art: "zuWenig" };
  return { art: "punkte", punkte: rest };
}
