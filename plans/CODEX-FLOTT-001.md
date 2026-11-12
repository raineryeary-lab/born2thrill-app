# Codex wieder flott und weg von G:

Status: PROPOSED

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Codex antwortet auch in Bilder-Chats schnell, und nichts läuft mehr über Google Drive. Rainer hat das Zweite vor Wochen beschlossen, weil der Zugriff auf G: unsicher war. Umgesetzt wurde es bei Codex nicht.

## Current evidence and behavior

Gemessen am 2026-10-30 aus `~/.codex/sessions`, nur gelesen. Die Antwortzeit ist die Zeit vom Tool-Ergebnis oder der Eingabe bis zum nächsten Modell-Ereignis.

Antwortzeit nach Bildern, die schon im Chat liegen (Sitzungen seit 29.10. ab 1 MB):

| Bilder im Chat | Antworten | Median | P90 |
|---|---|---:|---:|
| 0 bis 4 | 30 | 5,2 s | 16,4 s |
| 5 bis 14 | 42 | 14,3 s | 27,7 s |
| 15 bis 39 | 131 | 12,3 s | 29,6 s |
| 40 bis 99 | 163 | 23,4 s | 46,5 s |
| 100 bis 199 | 214 | 23,8 s | 55,5 s |
| ab 200 | 253 | 24,3 s | 43,1 s |

- Kleine Chats ohne Bilder sind nicht langsamer geworden: heute Median 1,8 bis 2,5 s, auch um 19:05 Uhr. Die Ausnahme sind drei Chats mit je einer einzigen sehr schnellen Antwort (0,1 s).
- Die drei Bilder-Chats von gestern und heute: 22,5 s, 19,7 s und 18,1 s. Der 11-GB-Chat vom 11.10.: Tagesmedian 30,2 s.
- Die Zeit steigt mit den Bildern und bleibt ab etwa 40 Bildern bei rund 24 s stehen. Passend dazu lag der größte Kontext dieser Chats bei rund 245.000 Token.
- Schon ein Chat mit 38 Bildern kam auf 19,7 s. Ein Chat je Haus reicht deshalb allein nicht.
- In der Sitzung von 16:26 kamen 178 von 183 gezählten Bildern aus Tool-Ausgaben, also vor allem vom Ansehen.

Rechner: Prozessorlast 2 %, 39 GB RAM frei, genug Plattenplatz. Er ist nicht die Ursache.

Google Drive:

- Fast alle Codex-Chats seit dem 27.10. nennen `G:\My Drive\_CodexSync\Projects` als Arbeitsordner.
- Diesen Pfad gibt es von dieser Maschine aus nicht. Das Laufwerk heißt `G:\Meine Ablage`, dort liegt `_CodexSync\Projects`.
- Die Codex-App führt den Pfad weiter (20 Einträge in `.codex-global-state.json`).
- 144 von 519 Regeln in `~/.codex/rules/default.rules` nennen G:. Die Datei ist 322 KB groß und von Juli.
- Weitere G:-Stellen: 21 Treffer in 8 Dateien des Arbeitsbereichs, davon `floorplan-simplifier/AGENTS.md:67` als aktive Regel.
- Google Drive als Ursache der Langsamkeit ist nicht belegt, denn kleine Chats auf diesem Pfad sind schnell. Es geht hier um Rainers Entscheidung und um die Sicherheit. Nicht gemessen wurde die Laufzeit von Tool-Aufrufen auf G:.

Grenzen der Messung: Bilder-Chats leisten auch mehr Denkarbeit, nicht jede Sekunde ist also einsparbar. Die Stufe 0 bis 4 hat nur 30 Werte. Ladezeit und Bedienung der Codex-App wurden nicht gemessen.

## Repository baselines

- `born2thrill-local-workbench`: Branch `agent/furnished-render-and-annotation-schema`, Stand `5be1a4e`, 595 Einträge in `git status`.
- `floorplan-simplifier`: Branch `agent/annotation-window-type-door-swing`, Stand `8a08d19`, 248 Einträge in `git status`.
- Fremde Änderungen bleiben unangetastet.

## Exact scope

**Schritt 0: Regeln dorthin, wo Codex sie liest.**
Ursache, warum Beschlüsse verloren gehen: Rainer hat den G:-Beschluss am 2026-09-04 schon einmal angemahnt, aufgeschrieben wurde er nirgends. `~/.codex/AGENTS.md` ist leer (0 Bytes), im Arbeitsordner gibt es keine `AGENTS.md`, und die 41 Merkdateien liest nur Claude. Neue Datei `C:\dev\Floorplan-tools\REGELN.md` als einziges Regelbuch für Rainers feste Beschlüsse, höchstens 60 Zeilen, je Regel eine Zeile mit Datum. Claude lädt sie über eine neue `C:\dev\Floorplan-tools\CLAUDE.md`, Codex über `~/.codex/AGENTS.md` als Hardlink auf dieselbe Datei. Eine neue Regel ersetzt die alte, nichts wird angehängt und doppelt geführt. Das Skript `scripts/regeln-pruefen.py` meldet: mehr als 60 Zeilen, getrennter Hardlink, aktive Regeldateien mit G: als Arbeitsort. Die lange `CODEX-REGELN.md` bleibt das Bild-Regelwerk und wird nicht in jeden Chat geladen. Erste Regel: kein Arbeiten und keine Ablage auf G:, Neues nur lokal. Lesen der Originale aus `G:\Meine Ablage\_____grundrisse\_Original` und `_handoff` bleibt erlaubt, bis sie umgezogen sind. `floorplan-simplifier/AGENTS.md` Zeilen 47 bis 67 werden angeglichen. Jeder neue feste Beschluss kommt im selben Zug dort hinein.

**Schritt 1: Eigener lokaler Arbeitsordner.**
Neu: `C:\dev\Codex-Haus` mit einer kurzen `AGENTS.md`, die nur auf Auftrag und Regeln verweist. Schreibrecht zusätzlich nur für `E:\born2thrill-local-workbench-data\corrections`. Nicht `C:\dev\Floorplan-tools`, weil Codex dort unnötig viel Material vorfindet. Vor dem Umbau prüfen, wie die heutigen Läufe trotz Schreibrecht nur auf G: nach E: schreiben konnten.

**Schritt 2: Neuer Chat startet nur noch dort.**
Der G:-Eintrag verschwindet als Standard aus der Codex-App. Das macht Rainer in der App, falls die Einstellung nicht in `config.toml` liegt.

**Schritt 3: Regeldatei aufräumen.**
Sicherung anlegen, dann die 144 G:-Regeln entfernen. Auch die übrigen Regeln durchsehen und nur behalten, was noch gebraucht wird. Eine Regel für `publish-renders.py` darf `--send` nicht erlauben. Codex ist dabei geschlossen.

**Schritt 4: Kurzer Start statt 42 KB Text.**
`Auftrag kopieren` auf `/haus` liefert nur noch den kurzen Startprompt mit Plan-ID, Dateipfaden und den Bild-Regeln. Der Text wird aus einer Quelle erzeugt, von Hand wird nichts ersetzt.

**Schritt 5: Bildgrenze für den Chat.**
Der Prompt legt fest:
- Jede Bildversion wird nur einmal angesehen, Gesamtbild höchstens 1280 px breit, Details als Ausschnitt.
- Ab 40 Bildern im Chat schreibt Codex den Stand nach `_work/STAND.md`, und Rainer startet einen neuen Chat, der dort weitermacht.
- Rainers OK-Pflicht aus Abschnitt 12 des Regelwerks bleibt unverändert.

**Schritt 6: Alte Chats aus dem Weg.**
Rainer archiviert die vier großen Chats in der App. Nichts wird gelöscht. Danach Codex neu starten.

**Schritt 7: Google Drive inventarisieren und ablösen.**
Liste aller Inhalte in `G:\Meine Ablage\_CodexSync` mit der Angabe, ob sie noch gebraucht werden. Gebrauchtes wird lokal kopiert, das Original bleibt liegen. Die aktive Regel in `floorplan-simplifier/AGENTS.md:67` wird angepasst. Alte Berichte bleiben als Geschichte stehen. Ob etwas auf G: später gelöscht wird, entscheidet Rainer gesondert.

**Schritt 8: Messen.**
Ein Haus läuft neu, dasselbe Skript misst wie oben.

## Files in scope

- Neu: `C:\dev\Codex-Haus\AGENTS.md`
- `~/.codex/config.toml`, `~/.codex/rules/default.rules` (je mit Sicherung)
- `scripts/make-codex-job.py`
- `src/app/api/floorplan-workbench/auftrag/route.ts`
- `src/app/haus/page.tsx`
- `docs/CODEX-REGELN-4PLUS2.md` (nur Ergänzung zu Chatgröße und Bildern)
- `floorplan-simplifier/AGENTS.md`
- Tests zum Auftrag (neu, Name nach Sichtung der vorhandenen)

## Explicitly out of scope

- Löschen auf G: oder in `~/.codex`
- Eingriffe in `thread_history_1.sqlite` oder in Sitzungsdateien
- Änderungen an `publish-renders.py`, an Bildregeln, Rechten oder Freigaben
- Berichte und Pläne aus der Vergangenheit
- Laufende Bilderaufträge: Der Umbau beginnt, wenn kein Haus mehr in Arbeit ist

## API, schema, and data-contract effects

`codex-job.json` bleibt der Vertrag und die `CODEX-AUFTRAG.md` bleibt vollständig. Nur der kopierte Text wird kürzer.

## Acceptance criteria

1. Neue Codex-Chats starten in `C:\dev\Codex-Haus`, kein neuer Chat nennt G:.
2. `default.rules` enthält keine G:-Regel und keine Freigabe für `--send`.
3. Ein Testhaus läuft vollständig durch: Bildzahl stimmt, `catalog.json` ist geprüft, Rainer nimmt die Bilder an.
4. Dieses Haus erreicht Median unter 10 s und P90 unter 30 s (heute 18 bis 24 s und 42 bis 55 s).
5. Kein Chat überschreitet 40 Bilder.
6. Ein einfacher Chat bleibt bei rund 2 s.
7. Nichts wurde gelöscht, alle Sicherungen liegen vor.

## Tests and verification commands

Neue Tests zuerst:
- Der Startprompt enthält die richtige Plan-ID und die Pfade zu Auftrag und Regeln.
- Er enthält keinen G:-Pfad, kein `--send` und keine erste Fassung ohne Warten auf das OK.
- Die `CODEX-AUFTRAG.md` bleibt inhaltlich vollständig.

Bestehende Tests werden nicht geändert. Zeigt sich, dass einer geändert werden müsste, stoppe ich und frage nach.

Prüfung im Browser: `Auftrag kopieren` auf `/haus` an einem echten Haus. Messung mit `codex_tempo3.py` und `codex_tempo4.py`, beide werden nach `scripts/` übernommen, damit die Messung wiederholbar bleibt.

## Protected and risky paths

- Codex hat den Upload-Befehl in der Hand. Beim Aufräumen der Regeln darf keine Freigabe weiter werden als heute.
- Ein Schreibrecht nur für `corrections`, nicht für den ganzen Datenträger.
- Fehlt im neuen Ordner eine Berechtigung, stoppt der Lauf. Das fällt beim Testhaus auf, bevor weitere Häuser laufen.

## Rights, provenance, privacy, and security impact

Rechte und Freigaben bleiben unverändert. Weniger Pfade über Google Drive verringern das von Rainer genannte Risiko. Die Inventarliste enthält nur Namen, keine Inhalte.

## Floorplan-suite invariant

Can any changed path generate, publish, or email geometry without matching an approved corrected corpus reference?

Answer: no. Geändert werden nur Arbeitsordner, Codex-Regeln und der kopierte Starttext. Geometrie, `publish-renders.py` und der Rechte-Check bleiben unverändert. Beleg sind die neuen Tests und der unveränderte Upload-Befehl.

## Customer, email, database, deployment, and external effects

Keine. Das Testhaus lädt wie bisher nach Rainers OK hoch, ohne `--send`.

## Failed-hypothesis log

Noch keine. Geprüft und verworfen: Rechnerauslastung als Ursache. Nicht belegt: Google Drive als Ursache der Langsamkeit.

## Rollback

Sicherungen von `config.toml` und `default.rules` zurückkopieren. Die Dateien in den Repos über die `.before-codex-flott`-Sicherungen zurücksetzen. `C:\dev\Codex-Haus` kann danach entfernt werden. Archivierte Chats lassen sich in der App zurückholen.

## Unresolved questions

Keine, die den Start blockieren. Ob die App den Standardordner per Datei oder nur per Klick ändert, wird in Schritt 2 geklärt.

## Approval record

Schritt 0 freigegeben und gebaut am 2026-10-30 (Rainer: "we need a fucking rulebook"). Geprüft: `regeln-pruefen.py` grün, alle vier Fehlerfälle werden gemeldet, ein frischer Codex-Chat in einem leeren Ordner nennt die Regeln 1 und 22 ohne Dateizugriff. Sicherungen: `.before-regelbuch` bei `~/.codex/AGENTS.md`, `floorplan-simplifier/AGENTS.md` und `WORKFLOW.md`.

Rainer, 2026-10-30: "ja but the interior lights that codex has bee doing the last weeks was ok dont change the image generator just get rid of the trash". Schritte 1, 2, 3, 6, 7 freigegeben. Schritte 4 und 5 zurückgestellt, sie ändern den Generator oder den Bildablauf. Löschen auf G: und in `~/.codex` bleibt ausgeschlossen, Müll wird nur aus der aktiven Konfiguration entfernt. `make-codex-job.py` und die Lichtregeln sind wieder im Stand vor dem 30.10.

Stand 2026-10-30, 20:30: Schritte 1 und 3 ausgeführt, Schritt 7 kopiert (nichts gelöscht). Abweichung vom Plan: `writable_roots` begrenzt das Schreiben auf E: nicht, der Test schrieb auch nach `E:\_Archiv`. Offen sind Schritte 2 und 6 in der App und die Prüfung dort.
