# Visual Catalog 4+2 — konsolidierte harte Regeln

Stand: 2026-09-05

## 1. Autoritaet und Quellen

1. Die neueste `.blend` des aktuellen Hauses ist die alleinige Autoritaet fuer Architektur, Objektbestand, Anzahl, Position, Mittelpunkt, Fussabdruck, Groesse und Drehung.
2. Vor jeder Erzeugung wird die `.blend` tatsaechlich neu geoeffnet beziehungsweise neu geladen. Erinnerung, alter Screenshot, altes PNG und eine fruehere Lieferung sind keine Geometriequelle.
3. Die MESH-Objektzahl wird aus der geoeffneten Datei ermittelt und im Nachweis eingetragen.
4. Ist die `.blend` neuer als der beigelegte Baseline-Render, darf der alte Render nicht verwendet werden. Erst einen passenden Baseline-Render erzeugen oder den Konflikt melden.
5. Die Objektkarte dient nur zum Identifizieren, Zaehlen, Positionieren und Lesen der Ausrichtung. Marker, Pfeile, Zahlen und Boxen erscheinen nie im Ergebnis.
6. Qualitaetsbeispiele bestimmen nur Stil, Materialtiefe, Licht, Atmosphaere und Ausstattungsdichte. Sie bestimmen niemals Grundriss oder Moebelpositionen.

## 2. Architektur-Lock

1. Waende, Raumgrenzen, Schnittebene, Dach, Treppenloch, Gelaender, Oeffnungen, Fenster, Tueren und Kamera bleiben exakt wie in der aktuellen `.blend`.
2. Keine Wand wird verschoben, verlaengert, gekuerzt, verdickt, entfernt, hinzugefuegt oder dunkel uebermalt.
3. Gleiche Kamera, gleicher Ausschnitt, gleiches Seitenverhaeltnis und dieselbe Blickrichtung in allen vier Innenstilen.
4. Keine Tuer in einem Fenster, kein Fenster anstelle einer Tuer und kein TV anstelle eines Fensters.
5. Fensterteilungen bleiben erhalten. Ein zweifluegeliges beziehungsweise zweigeteiltes Fenster behaelt seinen Mittelpfosten.

## 3. Objekt-Lock: Ersetzen ja, Umstellen nein

1. Moebel sind Stil-Platzhalter und duerfen beziehungsweise sollen durch hochwertige, passende Varianten ersetzt werden.
2. Jede Ersetzung behaelt exakt Mittelpunkt, Wandseite, Fussabdruck, Groesse, Ausrichtung und Anzahl des Ausgangsobjekts.
3. Kein Objekt wird fuer eine schoenere Komposition verschoben oder gedreht.
4. Ein Bett wird niemals eigenmaechtig um 90 oder 180 Grad gedreht. Seine Drehung kommt nur aus der `.blend`.
5. Passt ein Ersatzmodell nicht in den vorhandenen Kasten, wird ein anderes Modell gewaehlt. Der Kasten wird nicht verlassen.
6. Ein extra Objekt, das wirklich in der `.blend` steht, wird vor dem Rendern gemeldet. Es wird nicht still geloescht, verschoben oder als Fehler des Benutzers behandelt.
7. Vier Stile sind vier Material- und Atmosphaerenfassungen desselben Hauses, keine vier neuen Einrichtungen.

## 4. Tueren und Wege

1. Die `.blend` ist alleinige Autoritaet fuer Anzahl, Position und Aufschlagwinkel aller Tuerblaetter.
2. Mehrere Tuerobjekte an derselben Wand koennen verschiedene reale Oeffnungen sein. Namen mit `.001` oder `.002` werden nicht uebersehen.
3. Keine erfundenen Doppeltueren. Keine zwei Tuerblaetter in einer Oeffnung, wenn die `.blend` dort nur eines hat.
4. Kein Tuerblatt darf verschwinden, durch eine Wand ersetzt oder von einem Moebel verdeckt werden.
5. Hinter einem offenen Tuerblatt muss der reale Boden beziehungsweise Raum sichtbar bleiben; kein zweites falsches Blatt oder geschlossene Flaeche.
6. Garderobe, Schrank, Bank und Dekoration duerfen weder Tuerblatt noch Durchgang blockieren.
7. Eine Haustuer darf modern anthrazit sein und muss nicht die Farbe der Innentueren tragen. Ihre Lage und Geometrie bleiben trotzdem exakt.
8. Die Haustuer (Oeffnung mit `role: main_entrance`) rendert IMMER geschlossen -- keine Aufschlagsimulation wie bei Innentueren. Policy-Schluessel `entrance_door_closed: true` in `policies/zuhausefinder-hard-rules.v1.json`, Pflichtfeld in `render-contract.py`s `REQUIRED_RULES`.

## 5. Garderobe

1. Eine Garderobe existiert nur an ihren echten Markern. Nirgends sonst werden Haken, Maentel oder Garderobenleisten erfunden.
2. Sie steht innerhalb ihres Fussabdrucks, liegt nicht in oder durch eine Wand und steht nicht vor einer Bad- oder Haustuer.
3. Die Front zeigt von der Wand in den Raum, entsprechend dem Richtungspfeil beziehungsweise der Drehung der `.blend`.
4. Ein Garderoben-Platzhalter wird zu einer erkennbaren echten Garderobe: Bank oder Schuhablage, Haken, einige Maentel und gegebenenfalls Schirmstaender, soweit die Quellgruppe diese Bestandteile vorsieht.
5. Kein nackter Kasten und kein leeres Gestell gelten als fertige Garderobe.

## 6. `stuff` wird raumbezogen ersetzt

1. `stuff` bleibt niemals ein glatter Kasten. Es wird zu einem realen, raumgerechten Moebel beziehungsweise einer realen Ausstattung innerhalb desselben Fussabdrucks.
2. Kinderzimmer: Gaming-/Spielbereich, zum Beispiel vorhandenes Regal oder Medienmoebel mit Bildschirm, Konsole und Gamingstuhl, aber nur innerhalb des markierten Objekts.
3. Wohnzimmer: Regale, Buecher, Bilder und passende Dekoration auf oder in dem vorhandenen Stauraummoebel.
4. Buero: Regal beziehungsweise Stauraum mit Buechern, Akten und dezenter Arbeitsdekoration.
5. HWR: Vorrats-, Waesche- oder Haushaltsregal mit Koerben, Handtuechern und Flaschen.
6. Bad: Handtuecher und Badzubehoer nur auf vorhandenen Moebeln oder Ablagen.
7. Die Raumzuordnung kommt aus der `.blend` beziehungsweise floor-Raum-ID, nicht aus einer freien Vermutung.
8. Dekoration steht auf einem vorhandenen Trager. Keine zufaellige Dekoration auf leerem Boden.

## 7. Kueche

1. Kuechenzeile, Insel, Hochschrank, Kuehlschrankverkleidung und weitere Korpusse bilden pro Stil eine zusammenhaengende Materialfamilie.
2. Alle Arbeitsplatten einer Kueche haben dasselbe Material und dieselbe Farbe, sofern die `.blend` nicht nachweislich verschiedene Bauteile vorgibt.
3. Korpusse sind fertige Moebel mit Tueren, Schubladen, Fugen, Sockel und sinnvollen Griffen. Keine schwarzen oder einfarbigen Bloecke.
4. Seitenflaechen eines Hochschranks werden als Seiten behandelt: keine Griffe und keine Frontfugen auf der Seite.
5. Fronten liegen nur auf der tatsaechlichen Frontseite. Ein falsch ausgerichteter Korpus wird nicht durch erfundene Fronten auf der sichtbaren Seite kaschiert.
6. Herd, Hochschrank und Kuehlschrank bleiben exakt in ihrer Blender-Ausrichtung. Keine eigenmaechtige 90-Grad-Drehung.
7. Spuele und Kochfeld bleiben sichtbar, jeweils in der echten Anzahl. Keine zweite Spuele und kein zweites Kochfeld erfinden.
8. Keine Inselhocker oder Barstuehle, wenn sie nicht in der `.blend` stehen.

## 8. Sanitaer

1. Badewanne, beide Duschen, WCs, Waschbecken und Waschtische bleiben in Anzahl, Lage und Art erhalten.
2. Eine Badewanne wird nie durch eine Dusche ersetzt, verschoben oder in eine Duschkabine gelegt.
3. Zwei Duschen bleiben zwei getrennte Duschen an ihren jeweiligen Positionen; keine dritte Dusche erfinden.
4. Kein WC in einer Duschkabine und kein erfundenes Bidet.
5. Doppelwaschtisch bedeutet die in der `.blend` vorhandene Beckenzahl; niemals ein drittes Becken erfinden.
6. Sanitär darf stilistisch neu materialisiert werden, aber nicht fehlen oder seine Funktion wechseln.

## 9. Ess-, Wohn- und Schlafbereiche

1. Die Essgruppe hat exakt die im Auftrag genannte Stuhlzahl. Bei `essgruppe_6`: genau sechs Stuehle, alle zum Tisch ausgerichtet.
2. Keine Stuehle an die Seite schieben, wenn sie entfernt werden sollen; ueberzaehlige erfundene Stuehle werden wirklich entfernt.
3. Keine zusaetzlichen Stuehle an Inseln oder Tischenden.
4. Zusammengehoerende Sofas beziehungsweise Sofaelemente verwenden denselben Stoff und dieselbe Modellfamilie.
5. Couchtisch und Teppich bleiben an ihren Blender-Positionen; der Esstisch wird nie zwischen TV und Sofa gesetzt.
6. Fernseher sieht wie ein realistischer Fernseher aus, nicht wie eine schwarze Platte. Es gibt keinen zweiten TV ohne Quellobjekt.
7. Betten bleiben in exakter Drehung und Position. Kein Bett vor einem Kleiderschrank und kein Bett im WC/HWR.
8. Bettzeug bleibt hell genug und materiallesbar; kein schwarzer unlesbarer Block.

## 10. Vier Innenstile

1. Warm Modern: warme Eiche oder Nussbaum, Sand/Karamell, warm geaderter Stein, Keramikakzente.
2. Dark Modern: Graphit, geraeuchertes Holz und tiefes Taupe, aber helle beziehungsweise mittelhelle Waende und lesbare Raeume. Nicht alles schwarz und nicht unterbelichtet. Ein warmer Akzent wird zwei- bis dreimal wiederholt.
3. Soft Scandinavian: helle Natureiche, Warmweiss, Hafer, gedecktes Salbeigruen, heller Stein/Terrazzo und Naturfasern.
4. Classic: echte kassettierte/gerahmte Fronten, Eiche oder Kirsche, Messing/Bronze, gepolsterte Esszimmerstuehle, gemusterte Teppiche und gerahmte Bilder. Elegant, nicht kitschig und nicht bloss Warm Modern mit Braunfilter.
5. Alle vier Stile beginnen separat vom selben Blender-Baseline-Render. Kein Stil wird aus einem anderen Stil erzeugt.

## 11. Licht und fotorealistische Qualitaet

1. Ziel ist hochwertige Architekturvisualisierung, kein roher Blender-Viewport, kein Spiel-Render, kein Plastikmodell und kein Cartoon.
2. Materialien zeigen Holzmaserung, Stoffwebung, Steinstruktur, Glas, Fugen, Naehte, Griffe und realistische Reflexionen.
3. Leuchten sind sichtbar an und erzeugen warme, dezente Lichtkegel. Tageslicht bleibt ausgeglichen.
4. Jedes Moebel hat einen Kontaktschatten; nichts schwebt.
5. Boden, Wand, Korpus und Arbeitsplatte sind tonal unterscheidbar.
6. Jeder Raum wird gestaltet, auch Schlafzimmer, Kinderzimmer, Bad, HWR, Diele und Abstellraum.
7. Keine flache globale Farbtoenung als Ersatz fuer einen Stil.

## 12. Bildworkflow

1. Innenbilder: aktueller Blender-Render dieses Hauses als Grundbild plus aktuelle Objektkarte als Kontrollreferenz.
2. Ganzbild-Bearbeitung mit dem eingebauten Bildmodell ist der Normalweg fuer den ersten Stil-Durchgang.
3. Kein ComfyUI und kein alter Comfy-Workflow.
4. Ein reiner Blender-Neurender kann Geometrie pruefen, ist aber wegen fehlender Material-, Textil-, Deko- und Lichtqualitaet keine fertige Kataloglieferung.
5. Keine freie Text-zu-Bild-Neuerzeugung ohne Haus-Baseline.
6. Bei Unsicherheit wird die `.blend` erneut geoeffnet und das konkrete Objekt kontrolliert, nicht geraten.
7. Vor dem Erzeugen wird im Prompt zuerst der Architecture Lock, dann Objekt-/Anzahllock, dann Raum- und Stilbeschreibung, dann die Verbote genannt.

## 13. Korrekturen

1. Ein angenommenes Bild wird niemals komplett neu erzeugt.
2. Eine Nachbesserung beginnt auf dem beanstandeten Bild selbst.
3. Der Korrekturprompt nennt genau eine Sache und endet mit `No other changes.`
4. Wenn eine Markierung beziehungsweise Koordinate vorliegt, betrifft die Korrektur nur diesen Bereich. Andere Raeume und Objekte bleiben unveraendert.
5. Vor dem Ueberschreiben wird die alte Fassung als Review/Vorher-Version erhalten.
6. Nach jeder Korrektur wird die gesamte Pruefliste erneut kontrolliert, nicht nur die korrigierte Stelle.

## 14. Aussenbilder

1. Classic und Modern erhalten jeweils ihre eigene passende Exterior-Baseline.
2. Classic behaelt exakt sein geneigtes beziehungsweise Walmdach; Modern behaelt exakt sein Flachdach. Dachformen werden nie zwischen Varianten getauscht.
3. Architektur, Oeffnungen, Fensterteilungen, Tueren, Kamera und Gebaeudeproportionen bleiben exakt aus der jeweiligen `.blend`.
4. Keine erfundenen Doppel-, Balkon- oder Terrassentueren und keine entfernten Fenster.
5. Fotografie: waagerechte 3/4-Ansicht, etwa 24–35 mm, Stativ, gerade Senkrechten, ganzes Haus im Bild.
6. Stimmung: fruehe blaue Stunde mit interessanten, realistischen Wolken, warmen Fenstern und gut dosierten Fassadenleuchten.
7. Wandleuchten nur auf geschlossenen Wandflaechen, etwa auf Hoehe der Fensteroberkante, mit plausiblen Lichtkegeln.
8. Garten: hochwertig und interessant, aber realistisch; Rasen, Graeser, niedrige Straeucher, wenige Baeume, Kies- und Plattenflaechen.
9. Modernes hochwertiges Outdoor-Mobiliar nur auf echter Terrasse und nie vor Oeffnungen oder Wegen.
10. Kein Disney-Look, keine Bonbonfarben, kein Blumenmeer, kein Fake-HDR; zugleich nicht leer oder langweilig.

## 15. Ehrliche Selbstpruefung

1. Architektur und jede Markerposition werden im gelieferten Bild wirklich angesehen.
2. `sichtbar` oder `ersetzt` wird nur eingetragen, wenn das Objekt dort im Ergebnis erkannt wurde. Bei Zweifel steht `unklar`.
3. Markerchecks der vier Stile werden einzeln erstellt und duerfen nicht zeichengleich abgeschrieben sein.
4. Vor Rueckgabe werden insbesondere geprueft: Tueren, Fenster, Bettdrehungen, Stuhlzahl, Garderobe, `stuff`, Wanne, beide Duschen, WCs, Waschbecken, Spuele, Kochfeld, Kuechenkorpusse, Arbeitsplatten, TV und alle Raeume.
5. Ein Bild, das einen harten Punkt verletzt, wird weder als fertig bezeichnet noch unter dem finalen Namen gespeichert.

## 16. Dateien und Annahme

1. Zwischenstaende tragen `-review`, `-v2` oder einen anderen eindeutigen Zwischenstandsnamen.
2. Die geforderten finalen Namen werden erst nach ausdruecklicher Benutzerannahme belegt.
3. Ein Lieferordner enthaelt am Ende genau die verlangten Bilder plus `catalog.json`, keine Handoffs oder zusaetzlichen Vorschauen.
4. Handoffs und Beispielbilder liegen in einem separaten sibling-Ordner und werden nicht hochgeladen.
5. Endformate werden ohne Beschnitt, Letterboxing oder Seitenverhaeltnisaenderung erzeugt.
6. SHA-256 wird nach der letzten Bildaenderung neu berechnet.
7. Codex laedt nichts hoch.

