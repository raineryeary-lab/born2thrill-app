# Übergabe an Codex: Fragen für das Comic-Storyboard

Erstellt 2026-11-05 von Claude, nur aus lokalen Dateien. Nichts gerendert,
nichts hochgeladen, keine Website geändert.

## 0. Wichtig vorab

- **Eine neuere Fragenliste als das PDF vom 03.11. gibt es lokal nicht.** Rainer
  wollte am 04.11. die „finalen“ Fragen bekommen. In diesem Chat und in den lokalen
  Dateien ist keine neue Fassung angekommen. Falls es sie gibt, liegt sie woanders
  (anderer Chat, E-Mail o. Ä.). Bitte bei Rainer nachfragen.
- **Neu seit 05.11. ist nur die Preislogik** (REGELN 37, Chef): Preis je Zimmerzahl
  statt der drei Budgetstufen. Ob die Budget-Frage im Fragebogen bleibt, ist offen
  (siehe 4).

## 1. Quellen

| Quelle | Pfad | Stand |
|---|---|---|
| Fragebogen (maßgeblich, REGELN 37) | `born2thrill-local-workbench/docs/Hausbau-Konfigurator-Fragen-Ablauf.pdf` | 03.11.2026, SHA-256 `3877FBC2…92DF14A`, identisch mit `G:\Meine Ablage\_____grundrisse\Hausbau-Konfigurator – Fragen & Ablauf.pdf` |
| Preisfenster je Zimmerzahl | `REGELN.md` Nr. 37; `E:\born2thrill-local-workbench-data\konfigurator.json` → `preisfenster` | 05.11.2026 |
| Abhaken der Häuser | `born2thrill-local-workbench/scripts/konfigurator-matrix.py`, Ausgabe `E:\…\konfigurator-fehlt.md` | 05.11.2026 |
| Comic-Konzept (23 Szenen) | `docs/fragebogen-videos/KONZEPT.md`, `szenen.json`, `prompt_bauen.py` | 03.11.2026 |
| Probe-Seite (veraltet, s. 6) | `docs/fragebogen-videos/seite/` | 03.11.2026 |
| Landingpage des Chefs | https://hausbau-konfigurator.de/vorschlag-landingpage (one.com) | gesehen 03.11.2026 |

## 2. Fragen in Reihenfolge, genauer Wortlaut (PDF)

**1. Startseite.** Ziel: optisch ansprechender Einstieg mit wenig Text und klarer
Handlungsaufforderung. Nutzenversprechen: „Individueller Grundriss“, „Passende
Außenansicht“, „Ungefährer Preisrahmen“, „100 % kostenlos und unverbindlich“.
CTA: **„Jetzt Haus konfigurieren“**

**2. Grundstück.** Frage: **„Hast du bereits ein Grundstück?“**
Antworten: „Ja“ · „In Aussicht“ · „Nein“
- Falls „Ja“ oder „In Aussicht“: „Ort / PLZ: Wo befindet sich dein Grundstück?“ ·
  „Grundstücksgröße: Wie groß ist dein Grundstück?“
- Falls „Nein“: „Ort / PLZ: Wo suchst du ein Grundstück?“ ·
  „Grundstücksgröße: Wie groß soll dein Grundstück sein?“

**3. Budget.** Frage: **„Wie viel möchtest du für dein Haus investieren?“**
Antworten: „300.000 € – 450.000 €“ · „450.000 € – 600.000 €“ · „Mehr als 600.000 €“
Hinweis: „Alle Angaben verstehen sich zuzüglich Grundstücks- und Baunebenkosten.“
→ **Konflikt, siehe 4.**

**4. Hausart.** Frage: **„Was möchtest du bauen?“**
Antworten: „Einfamilienhaus“ · „Bungalow“ · „Doppelhaus / Doppelhaushälfte“ · „Zweifamilienhaus“

**5. Baustil.** Frage: **„Welcher Baustil spricht dich am meisten an?“**
Antworten: „Klassisch“ · „Modern“

**6. Dachform.** Frage: **„Welcher Look gefällt dir am besten?“**
Antworten: „Satteldach“ · „Walmdach“ · „Pultdach“ · „Flachdach“

**7. Anzahl der Zimmer.** Frage: **„Wie viel Platz soll dein neues Zuhause bieten?“**
Antworten: „3 Zimmer“ · „4 Zimmer“ · „5 Zimmer“
Hinweis: „Die Zimmeranzahl versteht sich zusätzlich zu Küche und Bad.“

**8. Gäste-WC mit Dusche.** Frage: **„Möchtest du eine zusätzliche Dusche in deinem Gäste-WC?“**
Antworten: „Ja“ · „Nein“

**9. Kontaktdaten.** Ziel: Kontaktdaten erfassen, bevor das Ergebnis angezeigt wird.
Felder: „Vorname“ · „Nachname“ · „Handynummer“ · „E-Mail-Adresse“
CTA: **„Mein Ergebnis anzeigen“**

**10. Ergebnisanzeige.** „Nach Eingabe der Kontaktdaten erhält der Nutzer sein
individuelles Konfigurationsergebnis.“ Ausgabe:
1. „Preisrahmen – Ungefähre Hauskosten, zuzüglich Grundstücks- und Baunebenkosten“
2. „Grundriss – Passend zur gewählten Hauskonfiguration“
3. „Außenansicht – Passend zu Hausart, Baustil und Dachform“

## 3. Verzweigungen und Regeln

- **Grundstück → Folgefragen:** Wortlaut von Ort/Größe hängt von Ja/In Aussicht vs. Nein ab
  (siehe oben). Nichts wird übersprungen.
- **Hausart → Zimmer** (PDF, „Bedingte Logik“):
  Einfamilienhaus nur 4 oder 5 · Doppelhaus/Doppelhaushälfte nur 4 oder 5 ·
  Bungalow 3, 4 oder 5 · Zweifamilienhaus 3, 4 oder 5.
- **Alle anderen Fragen:** keine Abhängigkeit (PDF, Abschnitt 11).
- **Kontakt** steht vor dem Ergebnis; ohne Kontakt kein Ergebnis.
- **Felder zum Abhaken (REGELN 37):** 10 Felder = efh-4, efh-5, dhh-4, dhh-5,
  bungalow-3/4/5, zfh-3/4/5. Ein 6-Zimmer-Haus zählt bei 5.
- **Preis je Zimmerzahl (Chef, 05.11.):** 3 Zimmer 450–500 · 4 Zimmer 480–550 ·
  5 Zimmer 550–650 Tsd. €. Ein Haus außerhalb seines Fensters füllt sein Feld nicht.
  Hauspreis intern = annotierte Wohnfläche × 3.000 €/m² (`konfigurator.json`).
- **Stand der Häuser (05.11., `konfigurator-fehlt.md`):** grün efh-4, efh-5, bungalow-3,
  bungalow-4; leer dhh-4, dhh-5, bungalow-5, zfh-3, zfh-4, zfh-5.

## 4. Konflikte und offene Entscheidungen (nichts davon ist entschieden)

1. **Budget-Frage (PDF Nr. 3) gegen Preisfenster (05.11.).** Das PDF fragt drei Budgets
   (300–450 / 450–600 / über 600). Seit 05.11. bestimmt die **Zimmerzahl** den Preis.
   Die drei Budgets passen nicht zu den Fenstern (z. B. 5 Zimmer 550–650 liegt in
   „450–600“ und „über 600“). Offen: Fällt die Budget-Frage weg, bleibt sie nur als
   Angabe ohne Einfluss, oder ändert der Chef die Antworten? **Davon hängen die
   Budget-Szenen 02, 02a, 02b, 02c ab.**
2. **Preisfenster überlappen** (3 Zi bis 500, 4 Zi ab 480). Offen, ob gewollt.
3. **Gilt das Preisfenster für alle Hausarten gleich?** (Roadmap KONFIG-PREISFENSTER-001: „Klären“.)
4. **Ergebnis-Preis:** PDF sagt „Preisrahmen“. Ob das Fenster der Zimmerzahl oder ein
   Preis des gefundenen Hauses gezeigt wird, ist nicht festgelegt.
5. **Landingpage gegen PDF:** Die one.com-Seite sagt „6 kurze Fragen“ (PDF: 7 Fragen
   plus Kontakt) und fragt zuerst „Was ist Ihnen beim Bauen am wichtigsten?“
   (Familie · Design · Budget · Komfort, als `?ziel=` an die Fragen übergeben).
   Diese Frage steht nicht im PDF. Offen: eigene Szene, nur Vorauswahl, oder weg?
6. **Was wird angezeigt, wenn es zum Feld kein Haus gibt** (DHH, ZFH, Bungalow 5)?
   Nicht festgelegt.
7. **Fragen vom 04.11.:** siehe 0, lokal nicht vorhanden.

## 5. Abgleich mit dem 23-Szenen-Konzept (03.11.)

| Szene | Frage im PDF | Stand |
|---|---|---|
| 00 Start | 1 Startseite | passt |
| 01 Grundstück? · 01a Ja · 01b In Aussicht · 01c Nein | 2 | passt (3 Antworten) |
| – | 2 Ort/PLZ, Größe | Formular ohne eigene Szene (so geplant) |
| 02 Budget · 02a · 02b · 02c | 3 Budget | **hängt an Konflikt 4.1**; Antworttexte im Konzept noch die drei alten Stufen |
| 03 Hausart · 03a EFH · 03b Bungalow · 03c DHH · 03d ZFH | 4 | passt (4 Antworten) |
| 04 Baustil | 5 | passt; Reaktions-Clips je Antwort offen (Konzept: Vorschlag nein) |
| 05 Dachform | 6 | passt (Kran, 4 Dachformen); Reaktionen offen (Vorschlag nein) |
| 06 Zimmer · 06a 3 · 06b 4 · 06c 5 | 7 | passt; 06a nur bei Bungalow/ZFH erreichbar |
| 07 Gäste-WC mit Dusche | 8 | passt; Reaktionen Ja/Nein offen (Vorschlag nein) |
| 08 Kontakt | 9 | passt |
| 09 Ergebnis | 10 | passt; Inhalt der Preisanzeige offen (4.4) |

Weitere offene Punkte aus dem Konzept:
- In 06 fliegt die Kappe des Sohnes weg, aber die Figurenregel sagt „trägt immer seine Kappe“.
  Widerspruch, entscheiden.
- Alle Zeilen in `KONZEPT.md` sind noch **nicht abgehakt**.

## 6. Feste Vorgaben von Rainer zum Comic (03.11.)

- Figuren exakt wie im Familienblatt („das war viel Arbeit“): Augen nur kleine schwarze
  Punkte oder Striche, nie große runde Augen mit Pupillen; Staunen über Brauen und Mund;
  rosa Wangen, lange dünne Hälse; richtige Größen (Papa am größten, Mama fast so groß,
  Kinder deutlich kleiner). Beschreibung je Figur: `szenen.json` → `figuren`.
- Je Clip nur die Figuren beschreiben, die mitspielen (`szenen.json` → `wer`), sonst
  steht die ganze Familie im Bild.
- Papa ist nie gierig; wenn Hilfe kommt, ist er erleichtert.
- Budget als Kette: 02a Motten → 02b Kamera zieht auf, der kleinere Sohn stand die ganze
  Zeit mit Geld daneben (Papa hatte den Überblick verloren) → 02c Mama schlendert lässig
  mit dem Buggy voller Geld ins Bild, Mama und Baby sehr zufrieden, Papa schaut fragend.
- Humor: Slapstick, nie gemein. Ton: Musik und Geräusche, keine Sprache.
- Erst das komplette Storyboard prüfen, dann generieren.

## 7. Stand Produktion und Probe-Seite

- Lokale Produktion pausiert; ComfyUI aus. Vorhandene Clips nur Platzhalter:
  `clips/02a-budget-klein.mp4` (nur Papa, Augen richtig, Gag fehlt),
  `probe-hausart-comfy.mp4` (alte Augen). `clips/alt/` = verworfene Versuche.
- Lokales Modell (MiniMax H3) trifft die Figuren, kann aber keine Gag-Bewegung und keinen
  Zoom. Für die echten Clips war Runway/Seedance vorgesehen (Entscheidung des Chefs offen).
- Die Probe-Seite `seite/` benutzt noch die drei alten Budgetstufen und die alten
  Feldnamen (`b600-efh-5+`) in `haeuser.json`. Nach dem 05.11. ist sie veraltet.
- Bau und Test in WordPress (born2thrill.de/test), danach eigenständiges Paket für die
  one.com-Seite des Chefs (REGELN 38).
