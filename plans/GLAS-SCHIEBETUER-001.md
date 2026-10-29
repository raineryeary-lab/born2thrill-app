# GLAS-SCHIEBETUER-001 — Glas-Schiebetür im Möbel-Tab

Status: PROPOSED (wartet auf Rainers OK)

Rainer, 2026-10-18: "can we add inner glass doors to the möbel tab? like for
walk in closets we would right click 3 door 2 door 1 door, you know for
closets where you just slide the whole wall more or less".

## Was

Ein neues Möbelsymbol **Glas-Schiebetür** (Bereich Schlafen und Ankleide). Es
wird gezeichnet wie die Vorwandinstallation, als Lauf von Wand zu Wand (2
Punkte). Ein Rechtsklick auf den Lauf bietet **1 Flügel / 2 Flügel / 3 Flügel**
an; Vorgabe sind 2. Im Editor zeigen Teilstriche die Flügel. Im Blender-Bau
entsteht eine raumhohe Schiebewand: Alu-Schiene oben und unten, N Glasflügel
(je Lauflänge/N + 50 mm Überlappung), versetzt auf zwei Spuren, schmale
Alu-Rahmen. Das Glas ist das vorhandene `GLASS_MAT` der Fenster.

## Die Kette (jede Naht wird getestet — siehe "Helfer ohne Aufruf")

| Stelle | Änderung |
|---|---|
| `src/lib/generator/symbol-catalog.mjs` | Symbol `glasschiebetuer`, placement `path`, depth 80, height 2400; in die Eimer schlafen / ankleide |
| `src/lib/generator/furniture-document.mjs` | `normalizeFurnitureSymbol` lässt `fluegel` (1–3) durch; ohne das fällt es beim Speichern still weg |
| `src/app/floorplan-workbench/page.tsx` | Rechtsklick-Menü am Lauf: drei Einträge Flügel 1/2/3, nur für dieses Symbol |
| `src/app/floorplan-workbench/furniture.tsx` | Teilstriche je Flügel im Lauf |
| `scripts/build-simplifier-render-plan.py` | `SYMBOL_3D["glasschiebetuer"]` mit build `glass_slider`; `fluegel` in die Placement |
| `scripts/render-furnished-dollhouse.py` | `build_glass_slider()`: Schienen, Flügel, Rahmen |

## Tests zuerst

- symbol-catalog.test.mjs: das Symbol existiert, ist `path`, steht in schlafen/ankleide
- furniture-document-Test: `fluegel: 3` übersteht das Normalisieren, `fluegel: 7` wird zu 2
- Plan-Builder-Test: die Placement trägt `fluegel` und build `glass_slider`
- render-furnished-dollhouse.test.py: `build_glass_slider` liefert bei 1/2/3 Flügeln 1/2/3 Glasflächen, Gesamtbreite = Lauflänge

## Risiko, das Rainer kennen muss

Plan-Builder und Renderer stehen im Toolchain-Hash. Nach dieser Änderung zeigt
**jedes Haus "Bau veraltet"**, bis es neu gebaut ist. Das lässt sich nicht
vermeiden, weil der Renderer das neue Teil bauen muss. Es kann aber mit dem
nächsten Neubau aller Häuser zusammenfallen.

## Nicht drin

- Schiebetüren in Wänden (Annotator-Türtyp): eigener Plan, falls gewünscht.
- Milchglas/Spiegel-Varianten.

## Sicherheitsfrage

Kann ein geänderter Pfad Geometrie ohne genehmigte Referenz erzeugen,
veröffentlichen oder mailen? Nein: nur ein Möbelstück, das der Mensch selbst
setzt; kein Upload, kein Versand.

## Rückweg

`*.before-glasschiebetuer` je Datei zurückkopieren; gesetzte Symbole dieses
Typs aus den Möbeldateien löschen.
