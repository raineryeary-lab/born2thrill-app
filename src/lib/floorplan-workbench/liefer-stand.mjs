/**
 * Was der Tab "Hochladen & Freigeben" zum offenen Haus sagt
 * (LIEFERN-STATUS-SICHTBAR-001).
 *
 * Rainer, 2026-10-30: "auf den localhost 3020 ist es nie erkennbar [...] was
 * jetzt ncoh nicht gemacht ist". Der Tab zeigte immer dieselben zwei Knoepfe.
 *
 * "Ist freigegeben" sagt diese Funktion nur, wenn der Katalog "ja" meldet UND
 * jedes Bild frei ist. Weiss sie es nicht, sagt sie das, statt zu raten.
 *
 * @param online Bilder im Katalog; null = laedt noch
 * @param fehlenLokal fertige lokale Bilder, die noch nicht online sind
 * @param frei Bilder mit Kundenhaken
 * @param katalogOk true/false; null = unbekannt
 * @param freigegebenAm approval_recorded_at aus dem Ledger
 * @param bilderFehler der Katalog war nicht erreichbar
 */
export function lieferStand({ online, fehlenLokal = 0, frei = 0, katalogOk = null,
                              freigegebenAm = null, bilderFehler = false }) {
  if (bilderFehler) {
    const unbekannt = { stand: "unbekannt", text: "Stand unbekannt", detail: "Katalog nicht erreichbar" };
    return { hochladen: unbekannt, freigabe: unbekannt };
  }
  if (online === null || online === undefined) {
    const laedt = { stand: "laedt", text: "Stand wird geladen …", detail: "" };
    return { hochladen: laedt, freigabe: laedt };
  }
  return {
    hochladen: hochladenStand(online, fehlenLokal),
    freigabe: freigabeStand(online, frei, katalogOk, freigegebenAm),
  };
}

function hochladenStand(online, fehlenLokal) {
  if (fehlenLokal > 0) {
    return { stand: online > 0 ? "teilweise" : "offen", text: "Jetzt hochladen",
      detail: fehlenLokal === 1 ? "1 Bild fehlt noch" : `${fehlenLokal} Bilder fehlen noch` };
  }
  if (online === 0) return { stand: "offen", text: "Jetzt hochladen", detail: "" };
  return { stand: "erledigt", text: "Ist hochgeladen",
    detail: online === 1 ? "1 Bild" : `${online} Bilder` };
}

function freigabeStand(online, frei, katalogOk, freigegebenAm) {
  if (online === 0) return { stand: "gesperrt", text: "Erst hochladen", detail: "" };
  if (frei === 0) return { stand: "offen", text: "Jetzt freigeben", detail: "" };
  if (frei < online) {
    return { stand: "teilweise", text: "Jetzt freigeben", detail: `${frei} von ${online} Bildern frei` };
  }
  if (katalogOk === null) {
    return { stand: "unbekannt", text: "Stand unbekannt", detail: "Katalog meldet keinen Stand" };
  }
  if (!katalogOk) {
    return { stand: "offen", text: "Jetzt freigeben", detail: "Katalog steht noch auf offen" };
  }
  const datum = deutschesDatum(freigegebenAm);
  return datum
    ? { stand: "erledigt", text: `Ist freigegeben am ${datum}`, detail: "" }
    : { stand: "erledigt", text: "Ist freigegeben", detail: "Datum nicht erfasst" };
}

/** Direkt aus dem Text, damit keine Zeitzone den Tag verschiebt. */
function deutschesDatum(wert) {
  const treffer = /^(\d{4})-(\d{2})-(\d{2})/.exec(String(wert || ""));
  return treffer ? `${treffer[3]}.${treffer[2]}.${treffer[1]}` : null;
}
