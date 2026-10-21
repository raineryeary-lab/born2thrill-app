# Der Sockel bekommt Fenster und eine fugenlose Wand

Status: APPROVED (Rainer, 2026-08-28, "fix it")

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-08-28 zu `onehalfstorey_020`: "fenster und tueren im Untergeschoss
fehlen, es wirkt so wie eine geisteretage, und ausserdem muess die gesammte
aussenwand doch homogen weiss verputzt sein".

Beides gemessen in `interior-modern-upper-baseline.blend`:

| | Rahmen | Glas | Fensterbank | Tuerblatt |
|---|---|---|---|---|
| gerendertes Geschoss | 40 | 9 | 7 | 12 |
| Sockel | **0** | **0** | **0** | **0** |

Der Sockel ist 11 nackte Wandkoerper mit hineingeschnittenen Loechern. Das
Material ist identisch (`dollhouse-wall`, rgb 0.90/0.89/0.87, Rauheit 0.90),
aber die Kaesten ueberlappen sich an den Ecken; ihre gleichliegenden Flaechen
erzeugen die sichtbaren senkrechten Fugen im Putz.

## Exact scope

`scripts/render-furnished-dollhouse.py`, nur der Sockel-Abschnitt:

1. Je Sockel-Oeffnung Rahmen (Pfosten, Sturz) und bei Fenstern eine Bank,
   dazu eine Glasscheibe. Dieselben Materialien wie im Geschoss.
2. **Keine Tuerblaetter.** Regelwerk §6: der Sockel ist Kulisse, er wird nicht
   moebliert. Eine Tueroeffnung braucht einen Rahmen, kein Blatt.
3. Die Wandkoerper eines Sockelgeschosses werden zu EINEM Koerper vereinigt
   (Boolean UNION), damit die ueberlappenden Flaechen verschwinden. Schlaegt
   die Vereinigung fehl, bleiben die Einzelkoerper stehen -- ein Sockel mit
   Fugen ist besser als kein Sockel.
4. Die Namen bleiben `sockel-...`. Das ist tragend: `verify_render_blend.py`
   indexiert `wall-<n>` fuer R0 und R8; ein Sockelteil, das `wall-3` hiesse,
   wuerde als Teil des gerenderten Geschosses gemessen.

## Files in scope

- `scripts/render-furnished-dollhouse.py`
- `scripts/render-furnished-dollhouse.test.py`

## Explicitly out of scope

- Das gerenderte Geschoss, die Kamera, der Dollhouse-Schnitt.
- `verify_render_blend.py` und seine Regeln.
- Neu-Rendern anderer Haeuser (geschieht beim naechsten Bauen von selbst).

## API, schema, and data-contract effects

Keine. Nur zusaetzliche Objekte in der Szene, alle mit dem Praefix `sockel-`.

## Acceptance criteria

- Jede Sockel-Oeffnung hat Rahmen; jedes Sockel-Fenster hat Glas und Bank.
- Kein `sockel-*-door`-Blatt.
- Im Sockel keine sichtbaren senkrechten Fugen mehr.
- `DMH_SOCKEL=0` schaltet den Sockel weiterhin ganz ab.
- R0, R8 und R9 messen weiterhin nur das gerenderte Geschoss.

## Tests and verification commands

`python scripts/render-furnished-dollhouse.test.py` -- neue Faelle fuer die
reine Zaehl-/Benennungslogik. Danach `python scripts/go.py onehalfstorey_020`
und die Objekte im .blend nachzaehlen: Sockelrahmen > 0, Sockelglas > 0,
Sockeltuerblaetter = 0, ein Wandkoerper je Sockelgeschoss.

Kein bestehender Test wird geloescht, uebersprungen, abgeschwaecht oder umgeschrieben.

## Protected and risky paths

Der Boolean UNION kann bei entarteten Wandkoerpern fehlschlagen. Deshalb in
`try/except` mit Rueckfall auf die Einzelkoerper.

## Rights, provenance, privacy, and security impact

Keine.

## Floorplan-suite invariant

Kann ein geaenderter Pfad Geometrie erzeugen, veroeffentlichen oder mailen,
ohne zu einer freigegebenen korrigierten Korpusreferenz zu passen?

**Nein.** Die Aenderung fuegt einer Kulisse Rahmen und Glas hinzu. Sie liest
denselben Bauplan wie bisher, erzeugt keine neue Geometriequelle, ruft weder
`publish-renders.py` noch `approve-plan.py` und beruehrt den Katalog nicht.

## Customer, email, database, deployment, and external effects

Keine.

## Failed-hypothesis log

(leer)

## Rollback

Sicherung aus dem Scratchpad zurueckkopieren und neu bauen.

## Unresolved questions

Keine.

## Approval record

Rainer, 2026-08-28: "fix it".
