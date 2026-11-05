/**
 * Was der Bilder-Tab in welcher Reihenfolge zeigt (bilder-tab-aufraeumen-v1).
 *
 * Rainer, 2026-10-22, onehalfstorey_045: "most of them i cant even select to
 * delete and most of them i cant select to show to customer". Die lokalen
 * Codex-Bilder standen OBEN und ohne Knoepfe, dieselben Bilder online mit
 * Knoepfen erst darunter -- jedes Bild zweimal.
 *
 * Online zuerst (dort sind Kundenhaken, Titelbild, Muell). Ein lokales
 * Codex-Bild, dessen Name schon online ist, entfaellt. Was lokal fertig,
 * aber noch nicht hochgeladen ist, folgt. Rohbauten zuletzt.
 */
export function bilderOrdnen(online, lokal) {
  const nachName = (a, b) => String(a.name || "").localeCompare(String(b.name || ""));
  const o = [...(online || [])].sort(nachName);
  const schonOnline = new Set(o.map((b) => b.name));
  const l = lokal || [];
  return {
    online: o,
    nichtHochgeladen: l.filter((b) => b.stufe === "final" && !schonOnline.has(b.name)).sort(nachName),
    rohbau: l.filter((b) => b.stufe !== "final").sort(nachName),
  };
}
