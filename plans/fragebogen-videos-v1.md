# fragebogen-videos-v1 (ENTWURF, wartet auf Rainers OK)

2026-11-03: Produktion gestoppt, Rainer will erst das Konzept abhaken:
docs/fragebogen-videos/KONZEPT.md (gilt vor dem Storyboard unten).

Rainer, 2026-11-03: "i wanted to change the questionair to flow from one video
to the next with a short video that fits to the situation". Der alte
Fragebogen kam schlecht an. Figuren: letztes Bild im ChatGPT-Chat
"Picasso Don Quixote Overview" (Vater, Mutter, Tochter Teen, Tochter jung,
Sohn jung, Grossvater ~60, Grossmutter, Baby im Buggy, Hund).

Fragen und Logik bleiben wie im Fragebogen-PDF (REGELN 37). Nur die Form
aendert sich: jede Frage ist eine kurze Szene (4-8 s). Am Ende der Szene
bleibt das letzte Bild stehen, die Antworten erscheinen als Buttons darauf.
Die Antwort startet die passende naechste Szene.

## Storyboard (Vorschlag)

| # | Frage | Szene | Antworten -> Anschluss-Szene |
|---|---|---|---|
| 0 | Start | Familie steht vor leerem Bauschild, Hund bellt | "Jetzt Haus konfigurieren" |
| 1 | Grundstueck? | Vater mit Spaten, Mutter mit Plan | Ja: Familie auf eigener Wiese / In Aussicht: Fernglas auf ein Grundstueck / Nein: Familie mit Landkarte |
| 1a | Ort, Groesse | Formular im Bauschild | Eingabe |
| 2 | Budget | Vater schuettelt Sparschwein, Mutter rechnet | 3 Szenen, Sparschwein klein / mittel / gross |
| 3 | Hausart | Familie steht um eine Skizze | EFH: Eltern + Kinder / Bungalow: Grosseltern / DHH: junges Paar mit Buggy / ZFH: alle drei Generationen |
| 4 | Baustil | Mutter haelt zwei Bilder hoch | Klassisch / Modern (echte Renderings aus dem Katalog) |
| 5 | Dachform | Sohn baut Dach aus Bauklotz | Sattel / Walm / Pult / Flach (echte Renderings) |
| 6 | Zimmer | Kinder rennen und beanspruchen Raeume | 3 / 4 / 5 (nur erlaubte je Hausart) |
| 7 | Gaeste-WC mit Dusche | Grossvater kommt vom Joggen, Hund ist schlammig | Ja / Nein |
| 8 | Kontakt | Familie winkt, Briefkasten | Formular |
| 9 | Ergebnis | Familie zieht ein, Tuer auf -> Grundriss + Aussenbild + Preis | - |

Etwa 20 kurze Clips.

## Technik

- Ein `<video>`-Spieler, Clips nacheinander; Buttons ueber dem letzten Bild;
  Zurueck-Knopf; ohne Ton spielbar; Untertitel mit der Frage.
- Erst lokale Probe-Seite mit Standbildern als Platzhalter, keine
  Aenderung an born2thrill.de.
- Ziel (REGELN 38): eigenstaendiges Paket (HTML/JS, Videos, Hausdaten als
  JSON) fuer die one.com-Seite des Chefs (hausbau-konfigurator.de, Baukasten
  onecdn.io), direkt unter der Landingpage. Bis alle zufrieden sind, wird in
  WordPress (born2thrill.de/test) gebaut und getestet, aber als
  herausloesbares Paket; danach Uebergabe, laeuft ohne Rainer und WordPress.
- Offen: Kontaktdaten -- one.com-Formular oder PHP, je nach Paket des Chefs.

## Offen

- Clips mit Seedance (Codex-Vorschlag 2026-11-03, gut fuer Squash & Stretch).
  Zugang offen: Dreamina/CapCut-Web, ComfyUI-API-Knoten (Comfy-Guthaben),
  fal.ai oder BytePlus -- Konto und Schluessel legt Rainer an.
  2026-11-03: Chef will Runway Max (Seedance 2.0 dort enthalten, laut
  Fremdquellen 9.500 Credits/Monat, "unlimited" nur eingeschraenkt --
  auf runwayml.com pruefen). Clips dann in Rainers Chrome bei Runway.
- Erst EIN Beispiel-Clip (Szene 3, Hausart) zeigen, dann den Rest (REGELN 8).
