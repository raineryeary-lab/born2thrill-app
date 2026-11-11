# konfigurator-neu-v1

Rainer, 2026-11-08: "Los geht's" der Landingpage soll auf einen neuen Konfigurator
zeigen, /test bleibt. "test einfach kopieren und das neue nach unseren neuen
Vorgaben": kein zweites "Los geht's", Einstiegsvideo läuft sofort, Fragen fliegen
unten ein.

## Umfang
- Neue WP-Seite `konfigurator`, Snippet "Konfigurator neu" aus
  `scripts/konfigurator-neu-snippet.py` (eigenständiges Dokument ohne Theme, REGELN 38;
  dieselbe Datei als `wordpress/konfigurator-neu/index.html`).
- Layout: CSS-Kopie von /test (hausklar-flug.css, Kino-Layout), Schrift Archivo.
- Bühne: Comic-Clips statt 3D. Vorhanden: Einstieg (Seedance R5, Mediathek 1737).
  Fehlende Clips: Szenenkarte aus Codex' storyboards.js ("Clip folgt").
- Fragen: Codex' comic-flow.js (Grundstück, Details, Budget, Hausart, Baustil,
  Dachform, Zimmer, Gäste-WC mit Dusche, Kontakt), bei jedem Lauf frisch gelesen.
- Ergebnis: Zusammenfassung + Preisrahmen (REGELN 37) + Link zum Grundriss-Katalog.
  Kontakt sendet nichts.
- Landingpage: alle Start-Knöpfe auf /konfigurator/ (FUNNEL_URL im Snippet überschrieben).

## Nicht im Umfang
/test, Codex' Dateien (nur gelesen), echte Hausvorschläge, Kontaktversand.

## Rückweg
Snippet deaktivieren, Seite löschen; Landingpage-Snippet neu erzeugen.

## Sicherheitsfrage
Geometrie erzeugen/veröffentlichen/mailen? Nein.

## v2 (2026-11-08, Auftrag Rainer ueber Codex)
Grundstueck + Details in einem Schritt (Detail-Schritt aus comic-flow.js wird im Konfigurator herausgefiltert, Codex' Datei unveraendert). Standbilder 01 (Warten am X) und 02 (Sparschwein) als Platzhalter; Intro-Clip unveraendert; kein Loop. Gepruefte Faelle: alle drei Zweige, Wechsel, Noch offen, Zurueck mit erhaltenen Eingaben, Budget-Bild, weisse Buehne nach Intro (Ende und Ueberspringen), Handy 375 px und Desktop.

## Intro-Tausch (2026-11-08, Auftrag Rainer ueber Codex)
Einstiegsvideo ersetzt durch Aquarell-Fassung intro-watercolor-preserved-dog-v1.mp4 -> Mediathek 1741, https://born2thrill.de/wp-content/uploads/2026/11/konfigurator-intro-watercolor-v1.mp4 (15,4 s, 854x480). Snippet 15: nur die Videozeile geaendert (Diff live vs. neu = 1 Zeile). Alte Datei 1737 bleibt in der Mediathek. Karten-Warteschleife (Runway) noch nicht freigegeben. Rueckweg: konfigurator-neu-snippet.py.before-intro-aquarell.

## Warteschleife Grundstueck (2026-11-08, Auftrag Rainer ueber Codex)
wait-loop-pivot-v4.mp4 -> Mediathek 1742, https://born2thrill.de/wp-content/uploads/2026/11/konfigurator-grundstueck-schleife-v4.mp4. CFG.loops["01"]: autoplay muted loop playsinline nach Intro-Ende/Skip und bei Rueckkehr; Budget ersetzt die Buehne (Schleife weg); reduced motion = Standbild. wait-loop-v1 abgelehnt, nicht verwendet. Live geprueft. Rueckweg: *.before-schleife.

## Gesamtfilm (2026-11-08, Auftrag Rainer ueber Codex)
full-film-hq-v1-loop-ready.mp4 -> Mediathek 1743, https://born2thrill.de/wp-content/uploads/2026/11/konfigurator-film-hq-v1.mp4 (1920x1080, 20 s, unveraendert hochgeladen). CFG.film {url, schleifeAb:15}: einmal 0-20 s, bei ended currentTime=15 + play (kein natives loop). Frage ab 15 s; Ueberspringen -> 15 s; Rueckkehr von Budget -> Film ab 15 s (#t=15); andere Frage ersetzt die Buehne. Reduced motion: Standbild 01. Intro 1741 und Schleife 1742 bleiben als Rueckfall. Live geprueft (Desktop: 4 Durchlaeufe, Skip, Budget, Zurueck mit 1 Durchlauf; Handy 375 px lokal: Skip + 2 Durchlaeufe). Rueckweg: *.before-gesamtfilm.

## Frage zuerst, dann Film (2026-11-09, Chef ueber Rainer)
Start: Nummer 01 + Grundstuecksfrage fliegen sofort ein, Film startet 0,9 s spaeter (CFG.filmNachMs) ueber der Karte, kein Vollbild. Danach unveraendert 0-20 s einmal, dann 15-20 s endlos. Rueckweg: *.before-frage-zuerst.

## Film-Einblendung + Felder daneben (2026-11-09, Rainer)
Film laedt sofort vor, erstes Bild blendet ein (0,8 s) und steht, Start nach Kartenflug. Grundstueck ab 701 px: Felder rechts neben den drei Antworten (Grid), Karte waechst nicht nach unten (Handy weiter darunter). Rueckweg: *.before-blende.
