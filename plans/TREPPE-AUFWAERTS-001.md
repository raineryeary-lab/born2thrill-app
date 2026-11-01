# Treppe nach oben im mittleren Geschoss

Status: DONE

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-11-01: "bauen" auf den Vorschlag, bei drei Geschossen den Lauf nach oben zu bauen. Beispiele `twostorey_xvit`, `other_xvitv1`.

## Exact scope

`render-furnished-dollhouse.py`: `treppenlaeufe()`, im mittleren Geschoss zusätzlich der Lauf ab Boden, an der Schnittebene gekappt wie im Erdgeschoss. Der Lauf steht genau über dem unteren. Das automatische Geländer lässt den Antritt offen.

## Explicitly out of scope

Gegenläufig gezeichnete Treppen je Geschoss, gezeichnete Treppenöffnung, Upload, gespeicherte Häuser.

## Tests

`scripts/treppe_aufwaerts.test.py`, Probebau im Temp-Ordner.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

Answer: no. Geändert wird nur die Darstellung einer Treppe aus der vorhandenen Lauflinie.

## Rollback

`render-furnished-dollhouse.py.before-treppe-aufwaerts` zurückkopieren.

## Approval record

Rainers "bauen" vom 2026-11-01 im Chat.
