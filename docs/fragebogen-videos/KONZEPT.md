# Video-Fragebogen – Konzept

Stand 2026-11-03. Erst abhaken, dann wird produziert.
Fragen und Logik: Fragebogen-PDF (REGELN 37). Bau und Test in WordPress,
danach Übergabe an die one.com-Seite des Chefs (REGELN 38).

## So funktioniert es

1. **Ein Figurenblatt für alle Clips.** `familie-figuren.png` ist die Besetzungsliste
   (Vater, Mutter, Tochter Teen, Tochter jung, Sohn mit roter Kappe, Großvater ~60,
   Großmutter ~60, Baby im Buggy, Hund). Jeder Clip bekommt das Blatt als Vorlage;
   das Videomodell zeichnet jedes Mal eine neue Szene mit denselben Figuren im
   selben Stil. Nichts wird von Hand ausgeschnitten.
2. **Frage-Clip** (ca. 5 s) stellt die Situation dar.
3. **Standbild:** das letzte Bild bleibt stehen, die Antworten erscheinen als Knöpfe darauf.
4. **Reaktions-Clip** (ca. 5 s) je Antwort, dort sitzt die Pointe. Die Pointen
   bauen aufeinander auf (Budget: Motten → Sohn bringt Geld → Geld aus dem Buggy).
5. Danach startet die nächste Frage.

- **Figuren genau wie im Blatt** (Rainer, 2026-11-03: „das war viel Arbeit“): Augen
  nur kleine schwarze Punkte oder Striche, nie große runde Augen mit Pupillen;
  Staunen über Augenbrauen und Mund. Rosa Wangen, lange dünne Hälse, richtige
  Größenverhältnisse (Papa am größten, Mama fast so groß, Kinder deutlich kleiner).
  Die volle Beschreibung steht in `szenen.json` → `figuren` und geht in jeden Clip.
- **Papa ist nie gierig.** Er ist eher verloren als geizig, und wenn Hilfe kommt, ist er erleichtert.
- **Humor:** Slapstick wie im Sonntagmorgen-Zeichentrick, nie gemein, niemand wird verletzt.
- **Ton:** Musik (Ukulele, Xylophon) und Geräusche (boing, plopp), **keine Sprache**.
- **Austauschbar:** jeder Clip einzeln. Jetzt lokal (ComfyUI, ruhigere Bewegung),
  später Seedance über Runway. Die Seite bleibt gleich.
- **Fehlt ein Clip,** zeigt die Seite das Figurenblatt als Standbild und läuft weiter.

## Szenen zum Abhaken

Typ: **F** = Frage-Clip, **R** = Reaktion auf eine Antwort.
Die genauen Texte für das Videomodell stehen in `szenen.json`.

| OK | Clip | Typ | Wer | Gag |
|---|---|---|---|---|
| [ ] | 00 Start | F | alle | Familie marschiert los, Papa mit Karte in die falsche Richtung, der Hund zieht alle wie ein Gummiband zurück, sie landen auf einem Haufen und ploppen lächelnd hoch. |
| [ ] | 01 Grundstück? | F | Papa, Mama | Papa rammt den Spaten in den Boden, der federt wie ein Pogostick und schleudert ihn hoch, Mama fängt ihn am Kragen. |
| [ ] | 01a Ja | R | Papa, Mama, Hund | Papa posiert als Entdecker, der Hund buddelt im Turbo und überschüttet ihn mit Erde, Papa bleibt stolz stehen. |
| [ ] | 01b In Aussicht | R | Mama, Sohn | Mama schaut verkehrt herum durchs Fernglas, der Sohn dreht es um, ihre Augen werden riesig: Daumen hoch. |
| [ ] | 01c Nein | R | Papa, Mama, Teen | Die Landkarte faltet sich endlos auf und wickelt Papa ein wie eine Mumie, die Teen hält gelassen ihr Handy hoch. |
| [ ] | 02 Budget | F | Papa | Papa hält das Sparschwein ans Ohr und lauscht angestrengt, dann fragender Blick zum Zuschauer. |
| [ ] | 02a 300–450 Tsd. | R | Papa | Er schüttelt das Schwein kopfüber: nur zwei Motten flattern heraus und kreisen um seine Nase. |
| [ ] | 02b 450–600 Tsd. | R | Papa, Sohn | Schließt an 02a an: Die Kamera zieht auf, und man sieht, dass der (viel kleinere) Sohn die ganze Zeit mit einem Bündel Geld neben Papa stand; Papa hatte nur den Überblick verloren. Papa ist erleichtert, nicht gierig. Die Seite spielt 02a + 02b. |
| [ ] | 02c über 600 Tsd. | R | Papa, Sohn, Mama, Baby | Schließt an 02b an, gleiche Totale: Mama schlendert lässig von links ins Bild, mit dem Buggy voller Geld und dem Baby obendrauf, beide sehr zufrieden mit sich. Papa schaut fragend. Mama in richtiger Größe. Die Seite spielt 02a + 02b + 02c. |
| [ ] | 03 Hausart | F | Eltern, 3 Kinder | Papa beugt sich über die Hausskizze, immer weiter, bis er kopfüber hineinfällt; die anderen ziehen ihn an den Knöcheln heraus. |
| [ ] | 03a Einfamilienhaus | R | Eltern, 3 Kinder | Der Fußball des Sohnes prallt von Papas Kopf an Mamas Dutt und zurück auf seinen Fuß; alle lachen. |
| [ ] | 03b Bungalow | R | Großeltern | Keine Treppe: die Großeltern schlittern auf Socken über den Boden wie Eisschnellläufer und enden in einer Tanzpose. |
| [ ] | 03c Doppelhaushälfte | R | Eltern, Baby, Hund | Das Haus teilt sich, der Hund rennt zwischen den Hälften hin und her, bis ihm schwindlig ist, und plumpst in die Mitte. |
| [ ] | 03d Zweifamilienhaus | R | Großeltern, Eltern, Kinder | Großeltern und Eltern wollen gleichzeitig durch die Haustür, klemmen fest wie Zahnpasta und ploppen durch. |
| [ ] | 04 Baustil | F | Mama, Teen, Oma | Teen zerrt am modernen Bild, Oma am klassischen, Mamas Arme dehnen sich wie Gummi, dann schnalzt sie zurück. |
| [ ] | 05 Dachform | F | Papa, Opa, Hund | Ein Kran tauscht die Dächer aus (Sattel, Walm, Pult, Flach). Papa winkt dem Kranführer (Opa im Führerhaus) wild die Richtung, der Hund schüttelt bei jedem falschen Dach den Kopf und schaut Papa tief enttäuscht an. |
| [ ] | 06 Zimmer | F | alle, Hund | Clownsauto: immer mehr Familienmitglieder quetschen sich ins kleine Haus, die Wände beulen aus, zuletzt springt der Hund noch hinein und ein Fenster ploppt auf. |
| [ ] | 06a 3 Zimmer | R | alle, Hund | Das Haus bleibt prall gefüllt, die Haustür springt auf und der Hund kullert heraus. |
| [ ] | 06b 4 Zimmer | R | alle | Das Haus dehnt sich wie ein Akkordeon, alle atmen hörbar auf. |
| [ ] | 06c 5 Zimmer | R | alle | Das Haus wächst um ein Zimmer, jeder liegt ausgestreckt und zufrieden in seinem eigenen Raum. |
| [ ] | 07 Gäste-WC mit Dusche | F | Opa, Hund | Opa kommt vom Joggen, der schlammige Hund schüttelt sich neben ihm, Opa ist von oben bis unten voll Schlamm (nur die Brille sauber) und zeigt auf eine Duschtür. |
| [ ] | 08 Kontakt | F | alle, Hund | Der Hund wirft einen Umschlag in den Briefkasten, die Klappe schnappt zu, er springt erschrocken zurück und wedelt. |
| [ ] | 09 Ergebnis | – | alle | Papa öffnet die Haustür, alle wollen gleichzeitig hinein, verkeilen sich, der Hund flitzt durch die Beine, sie purzeln lachend ins Haus. Dann: Grundriss, Außenansicht, Preis. |

23 Clips.

## Noch zu entscheiden

- [ ] Reaktions-Clips auch für **Baustil, Dachform, Zimmer, Gäste-WC**? Vorschlag: nein,
  dort zeigen die Knöpfe echte Hausbilder (Stil, Dach). Mit Reaktionen wären es ca. 13 Clips mehr.
- [ ] Die Landingpage fragt zuerst „Was ist Ihnen beim Bauen am wichtigsten?“ (Familie,
  Design, Budget, Komfort). Soll das eine eigene Szene werden oder nur die Vorauswahl bleiben?
- [ ] Die Landingpage sagt „6 kurze Fragen“, das PDF hat 7 plus Kontakt.
