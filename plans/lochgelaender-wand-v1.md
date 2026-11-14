# lochgelaender-wand-v1

Rainer, 2026-11-03: "your railing rule automatic is not working i am constantly
getting railings in walls even if i didnt draw anything".

## Befund (onehalfstorey_021, interior-modern-upper-baseline.blend, gemessen)

- `loch-rail-1-right` steht bei x 1,18–1,23 m in der Aussenwand wall-9 (x 0,98–1,22).
- `loch-rail-0-right` 150 mm vor wall-5, `loch-rail-2-right` 20 mm vor wall-0.
- `loch-rail-0-left` / `2-left` stehen mitten im Treppenauge, Loch auf beiden Seiten.

Ursache: `wall_adjacent_intervals()` (render-furnished-dollhouse.py) bekommt die
Kanten in Metern (`corners = polygon_mm * MM`), reicht sie aber als `point_mm`
an `wall_within()` weiter, das gegen Waende in mm misst. Es findet nie eine Wand,
also baut die Automatik (Regel 35) an jeder Kante. Seit spaetestens 2026-10-09
in jedem Backup so.

## Aenderung

- Neue reine Funktion `lochkante_luecken(a_mm, b_mm, walls, loch_teile)`:
  offene Stuecke einer Treppenloch-Kante = Wand laengs (wie `gelaender_freie_stuecke`,
  Nachtrag A1) ODER Loch auf beiden Seiten (Treppenauge).
- Automatik-Zweig der Treppenloch-Gelaender ruft sie in mm auf; die kaputte
  `wall_adjacent_intervals` / `wall_within` entfallen (kein anderer Aufrufer).
- Manuelle Seitenwahl unveraendert.

Ausserhalb: Luftraum-/Balkon-Gelaender (rechnen schon in mm), Annotator, Plan-Builder.

## Tests

`lochgelaender_wand.test.py`: Kanten aus onehalfstorey_021 – Wand laengs → offen,
Aussenwand → offen, Treppenauge → offen, freie Flurkante → gebaut.
Bestehende `treppenloch_*.test.py` gruen.

## Nachweis

onehalfstorey_021 OG neu bauen, Objekte gegen Waende messen, Bild ansehen.
Keine Kundensendung, kein Upload.

## Rueckweg

`render-furnished-dollhouse.py.before-lochgelaender-wand` zurueckkopieren.
