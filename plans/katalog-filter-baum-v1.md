# katalog-filter-baum-v1

Rainer, 2026-11-09: neuer Baum des Chefs (docs/Grundriss Pfad 1.pdf, Pfad 2 = gleicher Baum hochkant) ist massgeblich, REGELN 37 umgeschrieben. Preisfenster bleiben als Anhaltspunkt.

Katalog-Filter (Snippet 10, scripts/katalog-fragebogen-snippet.py v3): Budget raus, Wohnflaeche rein (bis 130 / 131-160 / >160 m2); Flaeche und Zimmer je Hausart nur Aeste des Baums; Karte zeigt m2. Live geprueft (DH ohne >160, ZFH nur >160 und 3/4, Bungalow 131-160 ohne 3 Zimmer).

Rueckweg: katalog-fragebogen-snippet.py.before-baum, alter Snippet-Code im Scratchpad snippet10-vorher.php.

Stand 2026-11-09 (fertig-ledger): 9 von 19 Feldern ohne fertiges Haus (EFH bis 130 4/5, DH alle 4, ZFH 3/4, Bungalow >160 5 Zi); 21 von 38 Endpunkten mit Dusche leer.

## 2026-11-09 Lücken im Countdown + haus-skalieren-v1
- Countdown (Snippet 11, katalog-countdown-snippet.py) zeigt je Baumfeld mit <2 fertigen Häusern: "fertig machen" und bis 6 Vorlagen (gleiche/verwandte Hausart, ±30 % Fläche, ±1 Zimmer). Test: katalog_countdown_snippet.test.py (BaumLuecken).
- scripts/haus-skalieren.py: Vorschau-PNG (E:\...\vorschau-skalieren), skaliert nur floor_scale; --anlegen kopiert in neuen Projektordner + abgeleitet.json. Quelle bleibt unberührt.
- Beispiel: german_catalog_review_onehalfstorey_1_1_2_efh_120 151 → 129 m², 4 Zi, Strecken −7,6 %. Wartet auf Rainers OK, noch nichts angelegt.
- 2026-11-09 angelegt + gebaut: onehalfstorey_efh120_s129 (k=0,9243). Treppe in echter Länge (sonst R9_stair_access: 2271 statt 2620 mm), Anker Wendelecke. Möbel aus der Vorlage übertragen (scripts/moebel-uebertragen.py: an der Wand bleibt der Wandabstand, sonst anteilig), weil "Alle Räume einrichten" doppelte Küchenteile und kein Sofa setzte. Auto-Möbel gesichert im Scratchpad furniture-auto-s129. Bau: 1 fertig, Verifier grün. Offen: Codex-Bilder (REGELN 11 einzeln prüfen).
