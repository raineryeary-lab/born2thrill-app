# landingpage-hauskonfigurator-v1

Rainer, 2026-11-08: neue Seite "Hauskonfigurator" mit der Landingpage des Kollegen
(https://hausbau-konfigurator.de/vorschlag-landingpage) -> "Auf Hauskonfigurator übernehmen".

## Umfang
- WP-Seite 1736, Slug `hauskonfigurator`.
- Snippet "Landingpage Hauskonfigurator" aus `scripts/landingpage-snippet.py`
  (Quelle `wordpress/landingpage-kollege/`, `--holen` zieht die neueste Fassung).
- Ausgabe als eigenes Dokument ohne Theme (Styles des Kollegen sind global; REGELN 38).
- Knöpfe führen wie beim Kollegen auf FUNNEL_URL born2thrill.de/test/?ziel=...
- Passwortsperre (Snippet 13) greift vorher.

## Nicht im Umfang
Texte, Design, Impressum-/Datenschutz-Links (beim Kollegen "#"), /test selbst.

## Test
Ohne Zugang Anmeldeseite; mit Zugang Landingpage ohne Theme; Knöpfe zeigen auf /test/.

## Rückweg
Snippet deaktivieren; Seite 1736 zeigt dann wieder den Konfigurator-Shortcode.

## Sicherheitsfrage
Geometrie erzeugen/veröffentlichen/mailen? Nein, nur statische Seite.
