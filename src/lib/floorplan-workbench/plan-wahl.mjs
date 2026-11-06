/**
 * Welches Haus zeigt die Hausakte? (ZUVERLAESSIGKEIT-001, A1/A2)
 *
 * Vorher stand `plan` auf "" bis die Hausliste da war -- die braucht ueber
 * 30 Sekunden, und so lange lud der Rahmen `annotate.html?project=` (leer).
 * Fehlte das verlinkte Haus in der Liste, oder kam die Liste gar nicht,
 * sprang die Seite stumm auf ein ANDERES Haus und schrieb dessen Namen in
 * die Adresszeile. Rainer, 2026-10-25: "why is this so unrelyable?"
 *
 * Regeln hier, damit sie testbar sind:
 *   - Ein ausdruecklich verlangtes Haus (URL oder schon gewaehlt) bleibt
 *     gewaehlt, auch wenn es in der Liste fehlt -- dann mit Hinweis.
 *   - Ein Standardhaus wird nur gewaehlt, wenn keines verlangt war.
 */

/** Plan aus der Adresszeile, oder "". */
export function planAusUrl(search) {
  try {
    return (new URLSearchParams(search || "").get("plan") || "").trim();
  } catch {
    return "";
  }
}

/**
 * @param {{ jetzt: string, urlPlan: string, liste: {plan: string, state: string}[],
 *           istErledigt: (state: string) => boolean, listeGeladen?: boolean }} eingabe
 *   listeGeladen: die Liste ist eine echte Antwort der Route (auch wenn leer).
 *   Ohne das gilt eine leere Liste als "noch nicht da" -- dann kein Hinweis.
 * @returns {{ plan: string, hinweis: string }}
 */
export function waehlePlan({ jetzt, urlPlan, liste, istErledigt, listeGeladen = false }) {
  const verlangt = jetzt || urlPlan || "";
  if (verlangt) {
    const fehlt = (listeGeladen || liste.length > 0) && !liste.some((h) => h.plan === verlangt);
    return {
      plan: verlangt,
      hinweis: fehlt
        ? `${verlangt} steht nicht in der Hausliste (Projektordner fehlt oder `
          + "annotations.json ist unlesbar). Es wird kein anderes Haus geöffnet."
        : "",
    };
  }
  const standard = liste.find((h) => !istErledigt(h.state)) || liste[0];
  return { plan: standard?.plan || "", hinweis: "" };
}

/**
 * Die Antwort der State-Route pruefen. Wirft mit lesbarer Meldung, statt aus
 * einem Fehler stumm eine leere Liste zu machen.
 */
export function pruefeStateAntwort(ok, status, daten) {
  if (!ok) {
    const grund = daten && typeof daten === "object" && daten.error ? `: ${daten.error}` : "";
    throw new Error(`Hausliste nicht geladen (HTTP ${status}${grund})`);
  }
  if (!daten || typeof daten !== "object" || !Array.isArray(daten.houses)) {
    throw new Error("Hausliste nicht geladen: Antwort ohne houses-Liste");
  }
  // Jede Zeile pruefen, bevor sie die alte Liste ersetzt: ein [null] lief
  // sonst durch und stuerzte erst beim Zeichnen (h.plan) ab (Runde 2).
  daten.houses.forEach((h, i) => {
    if (!h || typeof h !== "object" || typeof h.plan !== "string" || !h.plan
        || typeof h.state !== "string") {
      throw new Error(`Hausliste nicht geladen: Zeile ${i + 1} ist kein gueltiges Haus`);
    }
  });
  return daten.houses;
}

/** Gesamtfehler der Route, die sonst niemand sieht: der Lieferzustand
 *  (Python) oder der Katalog (WordPress) konnte nicht gelesen werden. */
export function stateWarnungen(daten) {
  const w = [];
  if (daten?.zustand_fehler) {
    w.push(`Lieferzustand nicht lesbar: ${daten.zustand_fehler}. `
      + "Zertifikat/Frische der Häuser sind unbekannt -- nichts danach bauen oder hochladen.");
  }
  if (daten?.katalog_fehler) {
    w.push(`Katalog (WordPress) nicht lesbar: ${daten.katalog_fehler}. `
      + "Ob ein Haus online steht, ist gerade unbekannt.");
  }
  if (daten?.ledger_fehler) {
    w.push(`fertig-Ledger nicht lesbar: ${daten.ledger_fehler}. `
      + "Es wird nicht geschrieben, bis die Datei repariert ist; Versionsnummern fehlen.");
  }
  return w;
}

/** Ist der Zustand dieses Hauses unbekannt (Pruefung fehlgeschlagen)? */
export function istZustandUnbekannt(haus) {
  return !!haus && haus.zustand_unbekannt === true;
}

/** Antwort von bild-freigabe/titelbild deuten.
 *  ok+bestaetigt: fertig. ok ohne Bestaetigung: geschrieben, aber nicht
 *  zurueckgelesen -- gelbe Warnung, Bilder neu holen. Sonst: Fehler. */
export function freigabeErgebnis(antwort) {
  if (antwort?.ok && antwort.bestaetigt !== false) return { art: "ok", text: "" };
  if (antwort?.ok) {
    return { art: "warnung",
             text: antwort.warnung || "Geschrieben, aber nicht bestätigt -- Bilder werden neu geladen." };
  }
  return { art: "fehler", text: antwort?.error || "fehlgeschlagen" };
}

/**
 * Nur die juengste Anfrage darf den Zustand setzen. Jede neue Anfrage holt
 * sich eine Nummer; eine spaete Antwort einer aelteren wird verworfen
 * (Haus A darf nicht in Haus B hineinschreiben -- A6).
 */
export function anfrageZaehler() {
  let letzte = 0;
  return {
    neu() { letzte += 1; return letzte; },
    aktuell(nummer) { return nummer === letzte; },
  };
}

/**
 * Schreiben in einem Bereich (Dachform, Rechte) -- Runde 3 (Codex):
 * - immer nur EIN Schreibvorgang zur selben Zeit (start() gibt null, wenn
 *   schon einer laeuft), sonst konnte ein spaet scheiternder erster Versuch
 *   den erfolgreichen zweiten zurueckdrehen;
 * - die Antwort gilt nur, solange seit dem Start nichts Neueres im selben
 *   Bereich begonnen hat (gemeinsamer Zaehler mit dem Lesen).
 */
export function schreibSperre(zaehler) {
  let laeuft = false;
  return {
    start() {
      if (laeuft) return null;
      laeuft = true;
      return zaehler.neu();
    },
    gilt(nummer) { return nummer !== null && zaehler.aktuell(nummer); },
    ende() { laeuft = false; },
    laeuft() { return laeuft; },
  };
}

/** Kennung fuer einen Speicher-Handschlag mit dem Annotator (Runde 3). */
export function neueAnfrageKennung() {
  const c = globalThis.crypto;
  if (c && typeof c.randomUUID === "function") return c.randomUUID();
  return `a${Date.now().toString(36)}${Math.random().toString(36).slice(2, 12)}`;
}

/** Eine Antwort ohne oder mit fremder Kennung gehoert zu einem anderen
 *  (frueheren) Handschlag und wird ignoriert. */
export function passtZurAnfrage(daten, anfrage) {
  return Boolean(daten && typeof daten === "object" && anfrage
    && typeof daten.anfrage === "string" && daten.anfrage === anfrage);
}

/** Wie lange der Browser hoechstens auf einen Pipeline-Schritt wartet (ms).
 *  Immer LAENGER als das Zeitlimit der Route selbst (pipeline/route.ts:
 *  bauen/hochladen 6 h, freigeben 10, codex 5, treppe 3 min) -- sonst gibt
 *  der Browser auf, bevor die Route ihr eigenes, lesbares "ZEITLIMIT" melden
 *  kann. */
export const PIPELINE_FRIST_MS = {
  bauen: (6 * 60 + 10) * 60_000,
  hochladen: (6 * 60 + 10) * 60_000,
  // Die Route erlaubt zwei Schritte nacheinander zu je 10 min.
  freigeben: 25 * 60_000,
  regenerieren: 15 * 60_000,
  codex: 7 * 60_000,
  treppe: 4 * 60_000,
};
