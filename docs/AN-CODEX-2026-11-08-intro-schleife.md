# An Codex: Intro und Warteschleife auf /konfigurator (2026-11-08)

Von Claude, auf Rainers Bitte. Dies ist eine Information, kein neuer Auftrag. Was davon gebaut wird, entscheidet Rainer.

## Stand live
- Intro: konfigurator-intro-watercolor-v1.mp4 (Mediathek 1741), läuft einmal.
- Danach die Schleife: konfigurator-grundstueck-schleife-v4.mp4 (Mediathek 1742, aus wait-loop-pivot-v4.mp4), endlos, stumm.
- Das sind zwei getrennte Dateien. Beim Wechsel ersetzt die Seite das Intro durch die Schleife.

## Rainers Frage
Kann man auch nur einen Film abspielen und dessen letzte Sekunden endlos wiederholen?

## Antwort
Beides geht.

1. **Ein Film:** Die Seite springt nach dem Ende immer wieder ein paar Sekunden zurück, zum Beispiel von 15,4 s auf 12,0 s. Dafür müssen zwei Bedingungen erfüllt sein:
   - Das Bild an der Sprungstelle ist identisch mit dem letzten Bild. Die letzten Sekunden des Intros müssen also selbst eine saubere Schleife sein.
   - An der Sprungstelle liegt ein Schlüsselbild (Keyframe). Beim Export also an dieser Stelle einen Keyframe erzwingen oder mit kurzer GOP exportieren. Sonst ruckelt der Sprung.
2. **Zwei Filme (so ist es jetzt):** Das ist flexibler, weil sich Intro und Schleife unabhängig tauschen lassen. Den Übergang kann ich unsichtbar machen: Die Schleife lädt schon während des Intros und übernimmt im letzten Bild.

Empfehlung: bei zwei Filmen bleiben. Ein einzelner Film lohnt sich nur, wenn du das Intro-Ende ohnehin als Schleife baust.

## Was du in jedem Fall beachten solltest
- **Hintergrund:** Die Schleife v4 hat einen leicht grauen Hintergrund, das Intro-Ende und die Seite sind weiß. Auf dem Desktop sieht man deshalb einen hellen Kasten um das Bild, und beim Wechsel springt die Farbe. Bitte den Hintergrund der Schleife exakt auf den des Intro-Endes bringen, am besten reines Weiß #ffffff.
- **Anschluss:** Das erste Bild der Schleife sollte genau dem letzten Bild des Intros entsprechen, also gleiche Position von Vater, Hund und Karte und gleicher Bildausschnitt.
- **Format:** gleiche Größe wie das Intro (854×480), 24 fps, stumm, H.264 MP4.
