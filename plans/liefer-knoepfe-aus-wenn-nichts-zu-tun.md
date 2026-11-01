# Hochladen und Freigeben ausgrauen, wenn nichts Neues ansteht

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Rainer, 2026-10-07: "could the hochladen and the freigeben button be grayed out
whatever if there is nothing new to upload or nothing new for freigabe"

Im Liefern-Schritt der Hausakte (`/haus`, Tab "Hochladen & Freigeben") sind
beide Knoepfe immer klickbar. Bei einem fertigen Haus laedt "Hochladen" dieselben
Bilder erneut hoch und "Freigeben" schaltet erneut scharf, was schon scharf ist --
man erfaehrt erst aus der Ausgabe, dass es nichts zu tun gab.

Die Uebersichtsseite macht das schon richtig
(`overview/page.tsx:461`: `pending.length === 0 ? "alles hochgeladen"`, Knopf
`disabled`). Die Hausakte soll es genauso machen.

## Current evidence and behavior

- `src/app/haus/page.tsx:1010` — `disabled={!!laeuft}`, sonst nichts.
- `src/app/haus/page.tsx:1067` — `disabled={!!laeuft || !grund.trim() || rechte?.erklaerung?.antwort === "nein"}`.
- Die Zustandsmaschine kennt die Antwort bereits
  (`src/lib/floorplan-workbench/house-state.mjs`, `deriveBasis`):
  `hochgeladen === 0 && finalsLokal > 0` -> `bilder_hochladen`;
  `freigegeben < hochgeladen` -> `bilder_freigeben`;
  `approved !== "ja"` -> `warten_auf_freigabe`.
- Die Seite bekommt diese Tatsachen aber nicht: `/api/floorplan-workbench/state`
  liefert pro Haus nur `state, blocker, action, catalogue_images, approved`
  (`state/route.ts:245`). Bei `fertig_update` ist der Grund nur noch Prosa im
  `blocker`-Text, nicht maschinenlesbar.

## Exact scope

1. `house-state.mjs`: neue reine Funktion `lieferstand(facts)` ->
   `{ hochladen: "noetig"|"nichts"|"unbekannt", freigeben: "noetig"|"nichts"|"unbekannt", grund: string }`.
   Unabhaengig davon, welches Gate zuerst feuert, damit sie auch fuer
   `fertig_update` stimmt.
   - `hochladen: "noetig"` wenn `finalsLokal > hochgeladen`.
   - `hochladen: "nichts"` wenn `finalsLokal <= hochgeladen` und `hochgeladen > 0`,
     oder wenn es gar keine fertigen Bilder gibt (dann ist Codex dran, nicht der Upload).
   - `freigeben: "noetig"` wenn `freigegeben < hochgeladen` oder `approved !== "ja"`.
   - `"unbekannt"` wenn WordPress nicht erreichbar oder die Lieferung veraltet ist
     (`wordpress: null`). Unbekannt ist NICHT "nichts zu tun" -- der Knopf bleibt dann klickbar.
2. `state/route.ts`: `lieferstand` pro Haus mit ausliefern (neues Feld `lieferstand`).
3. `haus/page.tsx`: beide Knoepfe `disabled`, wenn der jeweilige Stand `"nichts"` ist,
   plus eine Zeile darunter, die sagt warum (nach dem Muster der Uebersichtsseite:
   der Knopftext selbst sagt "alles hochgeladen" / "alles freigegeben").
   Ausgegraut, nicht unsichtbar: ein verschwundener Knopf laesst einen suchen,
   ein grauer sagt "hier ist nichts zu tun".

## Files in scope

- `src/lib/floorplan-workbench/house-state.mjs`
- `src/lib/floorplan-workbench/house-state.test.mjs` (nur Ergaenzungen)
- `src/app/api/floorplan-workbench/state/route.ts`
- `src/app/haus/page.tsx`

## Explicitly out of scope

- `overview/page.tsx` (macht es schon richtig)
- Die Zustands-Gates selbst, `STATES`, `ERLEDIGT`, `FAST_FERTIG`, der Ledger
- `pipeline/route.ts` -- der Server bleibt die Wahrheit; das Ausgrauen ist nur
  die Oberflaeche. Ein geduldiger Klick ueber die API bleibt moeglich und muss
  weiter dasselbe tun wie heute.
- Der Rechte-Dialog und seine Begruendungspflicht (bleibt zusaetzliche Bedingung)

## API, schema, and data-contract effects

`/api/floorplan-workbench/state` bekommt pro Haus ein zusaetzliches Feld
`lieferstand`. Rein additiv; kein bestehendes Feld aendert Namen, Typ oder Bedeutung.

## Acceptance criteria

1. Fertiges Haus (6 lokal, 6 hochgeladen, 6 freigegeben, approved ja):
   beide Knoepfe grau, Text "alles hochgeladen" / "alles freigegeben".
2. `bilder_hochladen` (6 lokal, 0 online): Hochladen aktiv, Freigeben grau-unbeteiligt
   (erst hochladen) -- genauer: Freigeben ist "noetig", bleibt also aktiv, weil
   approved noch nicht ja ist. Nur Hochladen entscheidet sich hier.
3. `bilder_freigeben` (9 hochgeladen, 6 freigegeben): Hochladen grau, Freigeben aktiv.
4. `warten_auf_freigabe` (alle Bilder durch, Plan nicht auf ja): Hochladen grau,
   Freigeben aktiv.
5. WordPress nicht erreichbar: beide aktiv, Begruendung sichtbar.
6. `fertig_update` wegen "Renderer neuer" bei sonst vollstaendiger Lieferung:
   beide grau -- die Lieferung ist vollstaendig, der Build ist eine Notiz.
7. Die Begruendungspflicht fuer Freigeben bleibt: ohne Grund weiter grau.

## Tests and verification commands

Neu in `house-state.test.mjs`:
- "lieferstand: fertiges Haus hat nichts zu tun"
- "lieferstand: lokal mehr als online heisst hochladen"
- "lieferstand: weniger freigegeben als hochgeladen heisst freigeben"
- "lieferstand: Plan nicht auf ja heisst freigeben"
- "lieferstand: WordPress unerreichbar ist unbekannt, nicht erledigt"
- "lieferstand: veraltete Lieferung ist unbekannt"
- "lieferstand: fertig_update mit vollstaendiger Lieferung hat nichts zu tun"

Kein bestehender Test wird geloescht, uebersprungen, abgeschwaecht oder umgeschrieben.

Befehle:
- `node --test --test-isolation=none src/lib/floorplan-workbench/house-state.test.mjs`
- `npx tsc --noEmit` (oder der im Projekt eingerichtete Typcheck)
- Von Hand: `/haus?plan=<fertiges Haus>` -> Liefern-Tab, beide Knoepfe grau;
  `/haus?plan=<Haus in bilder_freigeben>` -> Hochladen grau, Freigeben aktiv.

## Protected and risky paths

`house-state.mjs` ist die einzige Stelle, die sagt, in welchem Zustand ein Haus
ist -- Farbe der Hausliste, Zaehler im Kopf und Sortierung haengen daran. Die
neue Funktion steht DANEBEN und ruehrt `deriveHouseState`/`deriveBasis` nicht an;
die bestehenden Tests sind der Nachweis.

## Rights, provenance, privacy, and security impact

Keiner. Das Ausgrauen entfernt keine Pruefung: Rechtefrage, Begruendungspflicht
und `approve-plan.py` bleiben unveraendert. Es wird nur schwerer, versehentlich
etwas erneut zu veroeffentlichen -- die Richtung ist konservativ.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an
approved corrected corpus reference?

Nein. Die Aenderung erzeugt keine Geometrie und ruft kein Veroeffentlichen auf.
Sie nimmt nur Klickbarkeit WEG; jeder Pfad, der veroeffentlicht
(`pipeline/route.ts` -> `go.py --hochladen`, `approve-plan.py`, `freigeben.py`),
bleibt unangetastet und behaelt seine eigenen Pruefungen.

## Customer, email, database, deployment, and external effects

Keine. Kein Commit, kein Push, kein Deploy, keine Kundenmail.

## Repository baselines

- `born2thrill-local-workbench`, Branch `agent/furnished-render-and-annotation-schema`, Base SHA `5be1a4e`
- Arbeitsbaum ist schmutzig (274 Eintraege aus der Sitzung vom 2026-09-03,
  Renderer/Modell-Pipeline). Diese Aenderung beruehrt keine dieser Dateien;
  nichts davon wird aufgeraeumt oder ueberschrieben.

## Rollback

`git checkout -- src/lib/floorplan-workbench/house-state.mjs src/lib/floorplan-workbench/house-state.test.mjs src/app/api/floorplan-workbench/state/route.ts src/app/haus/page.tsx`

Vier Dateien, keine Datenaenderung, kein Migrationsschritt.
