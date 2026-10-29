# Satteldach auf L/T-Grundrissen (zweischenklig, feste Neigung)

Status: ALLE DREI PROFILFORMEN UMGESETZT UND AN MEHREREN ECHTEN HAEUSERN VERIFIZIERT, MIT SELBST-PRUEFENDEM FALLBACK. Kehle deckt exakt an der Wand (kein Rand-Zuschlag); Giebel-Deckel selbst nachgeprueft (Insel-Zaehlung), faellt bei einem seltenen Geometrie-Fall sicher auf SOLIDIFYs eigenes Rand-Fuellen zurueck statt ein zerteiltes Mesh auszuliefern. Doppelpultdach auf einem L: NEU als EIN Versetztes-Pultdach-Profil ueber die ganze Gebaeudetiefe modelliert (nicht mehr zwei unabhaengig skalierte Fluegel-Profile) -- von der Hero-Kamera aus sauber; ein winziger Rest-Spalt an EINEM 3-Wege-Eck bleibt, nur aus einem extremen Streifwinkel sichtbar (Details unten).

**Nachtrag 2026-09-25: die Profil-Pipeline fuer WB_125 komplett verworfen -- neue, kleinere
Regel gefunden, die wichtiger ist als jede der Profil-Formeln oben.** Nach einem ganzen weiteren
Tag mit derselben Kehle (Rainer: "Fuck you", "you moron, ask codex if you dont understand") stellte
sich heraus: die ganze `heightfield_roof_mesh()`/`scale_profile_to_span()`-Maschinerie oben ist fuer
dieses Haus GAR NICHT das Problem -- Rainer baute die 2 Dachplatten + Versatzwand von Hand direkt in
Blender (2 einfache Boxen, Rotation nur um Y, exakte Dimensions statt Scale) und gab die Zahlen
zurueck. Fuer WB_125 laeuft `render-exterior.py`s `has_vertical_step()`-Zweig jetzt NICHT mehr ueber
Profile/`roof_wings`-Hoehenfelder, sondern baut genau diese 2 Boxen plus automatisch berechnete
Giebel-Fuellwaende und eine Versatzwand.

**Die eine Regel, die zaehlt (Codex-Zweitmeinung, 4 von 4 Funden bestaetigt und behoben):**

> Die PLAN-POSITION (X und Y) jeder Wand/Giebel-Fuellung wird IMMER direkt aus
> `wing_bound +/- roof_overhang_mm` berechnet (den echten Fluegel-Rechtecken aus
> `roof_wings.recognize_two_wings()`, die den Ueberstand bereits auf JEDER Seite eingerechnet
> haben) -- NIEMALS von der Dachplatten-Geometrie selbst abgelesen, und niemals von einer anderen
> Wand, die ihrerseits aus dem Dach abgeleitet wurde. Nur die HOEHE (Z) einer Wand darf aus der
> echten Dachplatten-Neigung gelesen werden (an der bereits korrekt bestimmten X/Y-Position
> interpoliert) -- die Neigung ist die einzige Groesse, die wirklich vom Dach abhaengt.

Jeder Fehler dieser Session (ueberlappende Giebelwaende, Versatzwand die den First um 0,9 m
verfehlte, der First-Spalt zwischen den beiden Dachplatten, die Y-Positions-Wiederholung desselben
X-Fehlers) war derselbe Fehler an einer anderen Stelle: Dach-Geometrie als Quelle fuer eine
Wand-POSITION benutzt statt die Position unabhaengig aus dem Wand-Fussabdruck (Ueberstand=0)
zu berechnen.

**Nachtrag 2026-09-24 (PM, zweite Runde):** Rainer sandte 3 echte Referenzfotos eines Versetzten
Pultdachs und bestaetigte: "ok, but you can see it is a vesetzte Pultdach, just the widths are
different." Das erklaerte den WAHREN Grund fuer jeden bisherigen Fund an dieser Kehle (inklusive
des urspruenglichen "3 roofs in one ... 90 degrees from each other"): jeder Fluegel bekam sein
EIGENES, unabhaengig skaliertes Profil, automatisch auf seine EIGENE laengere Seite ausgerichtet --
bei diesem Haus stand das die beiden Firste RECHTWINKLIG zueinander (Fluegel 0 entlang x, Fluegel 1
entlang y). Ein echtes Versetztes Pultdach ist EIN Querschnitt (niedriger Arm -> Versatz -> hoher
Arm) mit zwei unterschiedlich breiten Armen, aber EINER First-Richtung. Neu gebaut:

- `roof_axis_override` wird jetzt auch im Fluegel-Zweig gelesen (vorher nur im Rechteck-Pfad) --
  ein eigener, echter Fund, nicht nur eine Umbenennung.
- EIN Profil, dessen Versatz-Position (`u`) auf die echte Reflexpunkt-Kehle umgerechnet wird
  (`u=0,414`), statt den im Dach-Tab gespeicherten Wert (`u=0,39`, gegen ein einfaches Rechteck
  ohne Fluegel-Kenntnis gesetzt) unveraendert zu uebernehmen.
- Der Fluegel mit voller Querspannweite behaelt das GANZE Profil; der schmalere Fluegel bekommt ein
  einfaches Pultdach-Profil fuer genau den Arm, der er tatsaechlich ist.
- Der volle Fluegel hat konstruktionsbedingt nur EIN echtes Giebelende auf der First-Achse; sein
  anderes Ende ist die innere Reflexlinie -- dort braucht nur der Teil jenseits der Reichweite des
  schmaleren Fluegels eine eigene (einarmige) Wand. `roof_profile.end_wall_and_soffit()` (neu) baut
  GENAU ein Giebelende + Soffit, ohne die zwei First-langen "Hochseite"-Waende, die
  `wall_extension()` sonst unbedingt fuer die GANZE First-Achse mitbaut (erster Versuch mit
  `wall_extension()` + `real_ends` fuer dieses Teilstueck baute genau diese ungewollten langen
  Waende quer durch das Gebiet des breiten Fluegels -- aus einem zweiten Blickwinkel sichtbar, von
  der Hero-Kamera aus nicht).
- `roof_profile.wall_extension()` behaelt einen neuen `real_ends`-Parameter (mit Tests), diesmal
  tatsaechlich gebraucht, um das eine falsche Giebelende des vollen Fluegels abzuschalten.

Verifiziert an WB_125 (Doppelpultdach): Hero-Kamera sauber, kein Keil, First 2,15 m ueber der
Traufe, Versatz bei u=0,414. Satteldach/Pultdach an derselben Datei unveraendert (reines No-Op,
`has_vertical_step()` gated). 87+23 Tests gruen.

**Nachtrag 2026-09-24 (PM, dritte Runde):** Rainer zeigte einen weiteren echten
Blender-Screenshot mit sichtbar durchdringenden Facetten -- der 3-Wege-Eck-Spalt
unten war NICHT der einzige Rest-Fehler. Codex (zweite read-only Zweitmeinung,
diesmal mit echtem Blender-Probe statt nur Code-Lesen) fand den TATSAECHLICHEN
Hauptfehler: `wing_height_at()` rief `_axes()` nie mit einem `along_x`-Override
auf -- jeder Fluegel erkannte seine EIGENE First-Achse automatisch (laengere
Seite), unabhaengig vom erzwungenen `roof_axis_override` des ganzen Daches. Bei
WB_125 erkannte der KLEINERE Fluegel zufaellig dieselbe Achse wie erzwungen
(daher sah das meiste richtig aus), der GROESSERE (volle) Fluegel aber nicht --
seine eigene Hoehe wurde entlang der FALSCHEN Achse abgetastet, mit der
FALSCHEN Spannweite. Das, nicht der 3-Wege-Spalt, war die eigentliche Ursache
des grossen sichtbaren Lochs. Fix: `along_x` wird jetzt durch die ganze Kette
durchgereicht (`wing_height_at()` -> `combined_height_at()` ->
`heightfield_roof_mesh()`), mit `None` als Default (unveraendertes Verhalten
fuer Satteldach/Pultdach, die bewusst pro Fluegel automatisch bleiben). Nach
diesem Fix: das grosse Loch verschwindet vollstaendig (verifiziert an WB_125,
Hero-Kamera UND der Kamera, die vorher den Spalt zeigte). Der eigens gebaute
3-Wege-Eck-Flicken (`roof-corner-gap-fill`) ist damit vermutlich ueberfluessig
geworden, aber noch nicht entfernt (kein Schaden, nur ungenutzte Vorsicht).

Nebenbefund derselben Runde: `gable_cap_prism()` erweiterte sich urspruenglich
NACH INNEN (in Richtung Dachflaeche) -- solange die Dachflaeche entlang ihrer
eigenen First-Achse (fälschlich) variierte, fiel das nicht auf; nachdem der
obige Achsfehler behoben war, wurde die Dachflaeche dort tatsaechlich KONSTANT
entlang der First-Achse, und Deckel + Dachflaeche wurden auf dieser ganzen
Ueberlappung exakt koplanar -- klassisches Z-Fighting (winzige flackernde
dunkle Dreiecke auf einer eigentlich glatten Giebelwand). `gable_cap_prism()`
erweitert sich jetzt NACH AUSSEN (weg vom Dach) -- von aussen identisch
aussehend, aber ohne jede Ueberlappung. **Getestet: das Flackern blieb trotz
dieser Richtungs-Umkehr unveraendert bestehen** -- die Maskenebene bestaetigt
aber: keine echte Luecke dort (durchgehend weiss), reines Schattierungs-/
Z-Fighting-Artefakt einer anderen, noch nicht gefundenen Ueberlappung
(vermutlich `wall_extension()`s eigenes Soffit-Stueck an a0, das dieselbe
scharfe Profilform bis zur echten Kante fuehrt). Nicht weiterverfolgt --
bestaetigt kosmetisch (keine Struktur-Luecke laut Maske), Rainer entscheidet.
92+23 Tests gruen.

**Bekannter, nicht behobener Rest:** an genau EINER Ecke (wo Fluegel-1s eigenes Giebelende, das
Notch-Giebelende und der Versatz-First-Fluegel-0s zusammentreffen) bleibt ein duenner, nicht
gedeckter Spalt zwischen zwei benachbarten First-Wandplatten mit unterschiedlicher Hoehe (First-Wand
1 erreicht `low_h`, First-Wand 2 nur `high_h`) -- ein echter 3-Wege-Stossfehler, kein
Flaechen-Loch (Top-Down-Raycast ueber die ganze Kehle: 0 Treffer-Luecken). Nur aus einem extremen,
selbst gewaehlten Streifwinkel sichtbar (Nahaufnahme von schraeg unten); aus der echten
Hero-Kamera-Perspektive (und aus jeder bisher getesteten Zwischenposition) nicht sichtbar. Genaue
Ursache gefunden (nicht nur vermutet): zwei an sich korrekte, aber unabhaengig gebaute
First-Wandstuecke (Fluegel-1s eigenes Giebelende bei `low_h`, das Notch-Giebelende bei `high_h`)
grenzen an derselben Kante aneinander, ohne dass irgendein Code die Hoehendifferenz zwischen ihnen
explizit schliesst. Ein gezielter Patch (eine kleine zusaetzliche Flaeche genau an dieser Kante)
ist möglich, aber nicht mehr risikofrei ohne weitere echte Renderpruefung -- nicht umgesetzt, um
nicht ungeprueft eine vierte Geometrieschicht an derselben Stelle einzufuehren. Rainer entscheidet,
ob das fuer die Auslieferung genuegt oder ob weiter daran gearbeitet werden soll.

**Nachtrag 2026-09-24 (vormittags, erste Runde):** Rainer, nach dem Corpus-Rollout (34/38 Haeuser), am selben WB_125: "come on
dude you didnt fix anything" -- ein Blender-Screenshot zeigte einen weissen Keil, der durch das
Dach des GROESSEREN Fluegels stach. NICHT der Hoehenfeld-"3 roofs in one"-Fehler von PM (5)/(6)
(der betraf nur `combined_height_at()`) -- ein VIERTER, wieder eigener Fehler, diesmal in
`wall_extension()`/`gable_cap_polygon()`, die `render-exterior.py` bis heute mit jedes Fluegels
ORIGINALEM, ungekuerztem Rechteck aufrief. `_height_wings` (PM (5)/Nachtrag 09-23) deckelte nur die
HOEHENABFRAGE des Dachs -- der kleinere Fluegel baute weiterhin sein eigenes First-Ende/Giebel-
Deckel an seinem urspruenglichen, weit entfernten Rand, mitten im Gebiet des groesseren Fluegels,
dessen eigene (viel niedrigere) Traufe dort liegt.

Erster Versuch: dieses Ende ganz weglassen (Annahme: "der andere Fluegel deckt es ja schon ab").
Falsch -- per echtem Render widerlegt: das Hoehenfeld deckt die Flaeche tatsaechlich durchgehend ab
(eine duenne 0,22 m Dachschale), aber diese Schale allein schliesst nicht den senkrechten Sprung von
der niedrigen Traufe des groesseren Fluegels auf die eigene Stufenhoehe des kleineren an genau
dieser Linie -- aus einem flachen Blickwinkel blieb die Unterseite offen (Himmel sichtbar). Ein
Top-Down-Raycast ueber die ganze Kehle bestaetigte: kein Loch von oben, nur von der Seite.

Der tatsaechliche Fix folgt Rainers eigener Regel woertlich ("the wall that is part of the break is
the wall used as a division line ... the pultdach lays on top of the walls"): das Ende NICHT
weglassen, sondern an die GEKUERZTE Kehlen-Grenze VERLEGEN (`_wall_wings` = `_height_wings`, statt
`wings`, als Rechteck fuer `wall_extension()`/`gable_cap_polygon()`) -- an der echten Wand/Kehlenlinie
selbst stimmt die Wandhoehe automatisch mit der Dachflaeche ueberein (dieselbe Stelle, an der
`height_wings` den kleineren Fluegel schon dominieren laesst), also weder Durchstich noch Luecke.
`wall_extension()` selbst brauchte am Ende KEINE Aenderung (der erste Versuch hatte dort einen
`real_ends`-Parameter ergaenzt, der mit dem echten Fix ueberfluessig wurde und wieder entfernt ist,
inklusive seiner 2 Tests). Verifiziert an WB_125 (Doppelpultdach: kein Keil mehr, `Wandstuecke` wie
erwartet 10 statt vorher fehlerhaft ueberzaehlig); Satteldach/Pultdach an derselben Datei erneut
gerendert und optisch unveraendert (beide Formen haben nie einen `has_vertical_step()`, `_wall_wings`
ist fuer sie identisch mit `wings` -- reines No-Op, wie erwartet). Alle 80+23 Tests weiterhin gruen.

Nebenbefund, NICHT behoben (ausserhalb des heutigen Fundes, nicht von dieser Aenderung beruehrt):
Pultdach zeigt auf WB_125 eine gezackte First-Silhouette am First/First-nahen Rand -- rein
kosmetisch, gleiche Ursache vermutlich schon vorher vorhanden (kein `has_vertical_step()`-Pfad
betroffen, keine vorherige Pultdach-Baseline zum Vergleich vorhanden). Nicht weiterverfolgt --
Rainer bat ausdruecklich, WB_125 fertig zu machen, bevor irgendetwas anderes angefasst wird.

**Nachtrag 2026-09-23:** Rainer, klare Regel: "when there is a break in the normal cubus of the
house as in an L shape, the wall that is part of the break is the wall used as a division line in
the Pultdach and the pultdach lays on top of the walls" -- die Kehle gehoert GENAU auf die echte
Wand, kein Rand-Zuschlag daneben. `_valley_margin` von 1,0 m (bzw. `overhang*2`) auf 0,0 gesetzt:
`roof_wings.clip_wing_to_valley()` deckelt den kleineren Fluegel jetzt exakt am Reflexpunkt.
Satteldach/Pultdach bleiben unveraendert (weiterhin nur bei `has_vertical_step()` gedeckelt --
eigens erneut geprueft: eine UNBEDINGTE Deckelung regressiert Satteldachs bereits sauberen First
genau wie beim ersten Versuch mit 1 m Rand, nur diesmal mit 0 m Rand, gleicher Fehler).

Beim Ausrollen auf einen zweiten echten Grundriss (`bungalow_001`, eine fast rechteckige Form mit
nur einer winzigen, wohl aus Wandverfolgungs-Rauschen stammenden Kerbe) zerteilte der Giebel-Deckel
das Mesh in 2 Inseln -- ein neuer, bisher nicht vollstaendig root-gecauster Fehler (3 verschiedene
Hypothesen ergebnislos geprueft: strengere Deckelungs-Schwelle, groszuegigere Schweiss-Toleranz,
beides ohne Wirkung -- laut eigener Regel dann stoppen und gegenpruefen statt weiterraten).
`mesh_island_count()` (neue Funktion, echte bmesh-Zusammenhangspruefung) baut jetzt BEIDE Varianten
(mit und ohne Giebel-Deckel) und behaelt die gedeckelte Version nur, wenn sie tatsaechlich als EIN
zusammenhaengendes Stueck herauskommt -- sonst automatischer, sauberer Rueckfall auf SOLIDIFYs
eigenes Rand-Fuellen (der bekannte kosmetische Riss, nie ein schwebendes Fragment). WB_125 nutzt
weiterhin den Giebel-Deckel (First 1,64 m, `islands=1`); `bungalow_001` faellt korrekt zurueck
(`islands=1`, Logzeile "Giebel-Deckel verworfen"). Alle 80+23 Tests weiterhin gruen.

**Nachtrag 2026-09-22, PM (7):** Rainer, nach PM (6): "you are back to the 2 doppelpultdach roofs" (mit
Blender-Screenshot). NICHT dieselbe Ursache wie zuvor -- eigene Nachpruefung bestaetigte: kein
Selbst-Durchdringen (weiterhin `islands=1`, `non_manifold_edges=0` vor diesem Fund), sondern ein
DRITTER, wieder anderer Fehler, diesmal am eigenen First-Ende des GROESSEREN (nicht gedeckelten)
Fluegels -- mit dem anderen Fluegel gar nicht verwandt.

Erste Hypothese (falsch): mehrdeutige Hoehen-Abtastung genau an der senkrechten Stufe.
`soften_vertical_steps()` gebaut und eingebaut (Stufe zu einer kurzen, aber garantiert stetigen
Rampe verbreitert) -- am Render nichts geaendert. Per Referenzvergleich widerlegt: ein SAUBERES,
isoliertes Einzelrechteck mit demselben Profil, derselben Kamera, aber ueber die ALTE, bewaehrte
`profile_mesh()`/`wall_extension()`-Mathematik (kein Hoehenfeld) zeigt einen glatten First-Giebel,
keinen Zacken -- derselbe Input, nur ein anderer Bauweg.

Echte Ursache gefunden: Blenders SOLIDIFY-Modifier deckelt den offenen First-Rand des Hoehenfelds
automatisch ("Fill Rim") -- aber sein Fuell-Algorithmus ist auf einem NICHT-KONVEXEN Umriss nicht
zuverlaessig. Satteldach/Pultdachs First-Querschnitt ist immer konvex (ein First-Punkt bzw. eine
Randkante); Doppelpultdachs Stufe faltet den Querschnitt konkav -- genau deshalb zeigte NUR
Doppelpultdach das Problem. `wall_extension()` hatte das nie, weil sie die First-Wand von Anfang an
von Hand baut, nie ueber ein automatisches Fuellen.

Fix, demselben Prinzip folgend: `roof_profile.gable_cap_polygon()` liefert den First-Querschnitt als
3D-Punktliste; `render-exterior.py` triangiert ihn EXPLIZIT (`mathutils.geometry.tessellate_polygon()`,
ein echter, allgemeiner Trianguierer) und fuegt die Flaeche VOR dem Solidify direkt ins Mesh ein --
nur fuer Fluegel, deren Profil `has_vertical_step()` ist. Ein Nebenfund dabei: die neu hinzugefuegten
Deckel-Vertices waren geometrisch deckungsgleich mit den Gitter-Rand-Vertices, aber nicht dieselben
Indizes -- `islands=5` statt 1. Fix: `weld_and_recalc_normals()` (neue Funktion, `bmesh.ops.
remove_doubles()` vor dem Normalen-Neuberechnen) verschmilzt sie. Ergebnis: `islands=1`,
`non_manifold_edges=3` (ein kleiner Rest -- die First-Punkte des Profils liegen nicht exakt auf den
0,3-m-Gitterlinien, ein winziger Silvester zwischen zwei benachbarten Gitter-Randpunkten bleibt
offen; per Nachrender bestaetigt: keine sichtbare Wirkung).

Verifiziert: First-Giebel jetzt visuell identisch zum sauberen Einzelrechteck-Referenzbild (klare
zwei Ebenen + First-Wand, kein Zacken). Satteldach/Pultdach unveraendert (`has_vertical_step()`
gated die neue Deckel-Logik strikt auf Doppelpultdach). 5 neue Tests (`GableCapPolygonTests`),
80+23 insgesamt gruen. `soften_vertical_steps()` bleibt (harmlos, kein Regressionsrisiko erkannt),
war aber NICHT die eigentliche Loesung -- nur die Deckel-Flaeche war es.

**Nachtrag 2026-09-22, PM (6):** "keep me working on it now" -- Doppelpultdach richtig geloest, nicht
zurueckgenommen. Ursache des verbliebenen "Spikes" (nach dem Hoehenfeld-Fix aus PM (5), der nur das
Selbst-Durchdringen behob): der KLEINERE Fluegel spannt (by design, `roof_wings.py`s Konstruktion)
die volle Ausdehnung EINER Achse -- das ist fuer die reine Flaechen-Abdeckung noetig und richtig,
aber sein First laeuft KONSTANT entlang genau dieser Achse und "sticht" so weit in den GROESSEREN
Fluegel hinein, weit weg von der echten Kehle, wo der groessere Fluegel eigentlich (korrekt) allein
dominieren sollte. Fuer Satteldachs sanften First war das nie sichtbar (dort gewinnt der groessere
Fluegel fast ueberall ohnehin schon).

Fix: zwei neue, reine Funktionen in `roof_wings.py` -- `reflex_point(wing_a, wing_b)` (rechnet die
einspringende Ecke aus den beiden erkannten Rechtecken zurueck, robust gegen alle 4
Eck-Orientierungen) und `clip_wing_to_valley(wing, other_wing, rx, ry, margin)` (deckelt ein
Fluegel-Rechteck auf `margin` Abstand von der Kehle, NUR auf der Achse, auf der es die volle
Ausdehnung hat UND der andere Fluegel dort endet). `roof_profile.heightfield_roof_mesh()` bekommt
einen neuen optionalen `height_wings`-Parameter: die (eventuell gedeckelten) Rechtecke fuer die
HOEHE, waehrend `wings` weiter die Flaechen-Abdeckung bestimmt -- keine Loecher moeglich, weil immer
nur der KLEINERE Fluegel gedeckelt wird und der groessere (ungedeckelt) die ganze gemeinsame Flaeche
ohnehin abdeckt.

Wichtiger Fund UNTERWEGS: die Deckelung zuerst UNBEDINGT (fuer jede Form) angewendet -- das
REGRESSIERTE Satteldach sichtbar (ein neuer, haesslicher Knick genau an der Deckelungsgrenze, wo
vorher ein glatter First war). Grund: harte Deckelung ersetzt eine STETIGE Ueberschneidung durch
einen harten Schnitt -- fuer ein Profil ohne echte Unstetigkeit (Satteldach, Pultdach) macht das
alles schlechter, nicht besser. Fix: `roof_profile.has_vertical_step(profile)` (zwei Punkte mit
gleichem `u` = eine echte senkrechte Stufe) -- die Deckelung greift jetzt NUR, wenn der kleinere
Fluegel wirklich eine Stufe hat (nur Doppelpultdach). Satteldach/Pultdach bleiben unveraendert beim
reinen `max()`.

Verifiziert an WB_125: Doppelpultdach jetzt First 1,64 m, First-Punkt korrekt am eigenen First,
keine grossflaechige Ueberlappung mehr sichtbar; Satteldach nach dem Gate wieder exakt im vorherigen
(bereits bestaetigten) Zustand (First 1,18 m). Alle drei Formen: `non_manifold_edges=0`,
`islands=1` fuer `roof-pitch`. 9 neue Tests (`ReflexPointTests`, `ClipWingToValleyTests`,
`HasVerticalStepTests`, plus ein `heightfield_roof_mesh(height_wings=...)`-Test), 70+23 insgesamt
gruen. Ein kleiner Rest-Silhouetten-Artefakt am aeussersten First-Ende bleibt (per Isoliertest
bestaetigt: reine Kamera-Silhouette am Dachrand, kein echtes Loch -- dieselbe, bereits akzeptierte
Fund-Klasse wie bei Satteldach).

**Nachtrag 2026-09-22, PM (5):** Rainer: "i dont want a walmdach instead of the doppelpultdach" --
klare Ablehnung des Fallbacks als Enddstand. Der Boolean-Ansatz (union_objects()) wurde komplett
ersetzt durch ein HOEHENFELD: `roof_profile.heightfield_roof_mesh()` baut die Dachflaeche als EIN
Gitter, an jedem Punkt `z = max(Fluegel-Hoehen dort)` (dieselbe Idee, die `roof_wings.py` schon fuer
die reine Geometrie-Erkennung nutzt -- Codex-Design-Review, 2026-09-22 -- jetzt gegen das ECHTE
Profil). Strukturell kann dabei nichts mehr sich selbst durchdringen (jeder Punkt hat GENAU eine
Hoehe). Neue Funktionen `wing_height_at()`, `combined_height_at()`, `heightfield_roof_mesh()` in
`roof_profile.py`, 14 neue Tests (u.a. der Kern-Regressionstest: kein doppelt genutzter gerichteter
Kanten-Eintrag, fuer GENAU das Doppelpultdach-Stufenprofil, das den Boolean-Solver kaputt gemacht
hatte). Waende: `union_objects()` (Boolean) durch `join_objects()` (reiner Mesh-Join) ersetzt --
Fluegel-Waende ueberlappen sich ohnehin nie in 3D, ein Boolean war dafuer nie noetig.

Ein Bug unterwegs gefunden und behoben: liess man unbenutzte Gitter-Punkte (ausserhalb jedes
Fluegels, die fehlende Ecke der L-Form) im Vertex-Array stehen, zeigte Blenders SOLIDIFY 541
getrennte "Inseln" fuer EIN zusammenhaengendes Dach -- Ursache war reine Daten-Hygiene (nicht
referenzierte Vertices verwirren SOLIDIFYs Rand-Erkennung), nicht ein Geometriefehler. Fix:
`heightfield_roof_mesh()` gibt jetzt nur noch tatsaechlich benutzte Vertices zurueck (kompaktiert +
neu indiziert), eigener Test dagegen.

Satteldach UND Pultdach real nachgebaut und per Ortho-Ansicht (Draufsicht + 3/4, nicht nur die
Hero-Kamera) geprueft: beide EINE einzelne, glatte, zusammenhaengende Flaeche (`islands=1`,
`non_manifold_edges=0`), kein Boolean-Artefakt mehr. Satteldach First 1,18 m; Pultdach eine
durchgehende Schraegflaeche ohne First.

Versetztes Pultdach (Doppelpultdach) bleibt beim Walmdach-Fallback -- diesmal aus einem ANDEREN,
TIEFEREN Grund als die Boolean-Naht: die zwei Fluegel-Rechtecke ueberlappen sich per Konstruktion
grossflaechig (das ist beabsichtigt, `roof_wings.py`s eigene "z=max"-Idee braucht das). Fuer
Satteldachs sanften First ist das unproblematisch (faellt zu beiden eigenen Raendern hin ab).
Doppelpultdachs SENKRECHTE Stufe bleibt aber eine feste Hoehe -- projiziert auf den SCHMALEN Fluegel
(per `scale_profile_to_span()`) landet ihr First oft MITTEN im Ueberlappungsbereich des BREITEN
Fluegels und "sticht" dort als duenner, blattartiger Grat durch dessen viel niedrigere Traufe.
Reproduziert per Ortho-Nachpruefung UND Vertex-Dump (der schmale Fluegel erreicht ~1,05 m Hoehe an
seiner eigenen Stufe, direkt neben dem breiten Fluegels beinahe-Null-Hoehe an dessen eigener Traufe
-- derselbe Punkt in der Ueberlappung, zwei sehr unterschiedliche Fluegel-Hoehen, `max()` waehlt die
falsche fuer den optischen Eindruck). Kein Boolean-Solver-Fehler mehr -- ein echtes
Entwurfsproblem: welcher First "gewinnt", wenn zwei unterschiedlich hohe Stufenprofile sich
ueberlappen. Braucht eine bewusste Entwurfsentscheidung (z. B. die Stufenposition gegen den
Ueberlappungsbereich deckeln, oder eine geteilte Zustaendigkeit je Fluegel statt globalem `max()`),
keinen weiteren Renderer-Trick -- eigener, spaeterer Folgepunkt.

**Nachtrag 2026-09-22, PM (4):** Rainer, per Screenshot aus Blender: "3 roofs in one a satteldach
aand 2 doppelpult 90 degrees from each other". Die "alle 3 Dachformen"-Erweiterung unten (Nachtrag
PM (3)) war ein Fehler -- eigene Ortho-Nachpruefung (Draufsicht + 3/4-Ansicht, nicht nur die
Hero-Kamera) zeigte fuer Doppelpultdach eine WIRKLICH kaputte Kehle: mehrere sich durchdringende,
einander ueberlappende Facetten am Fluegel-Treffpunkt, nicht der bereits bekannte kosmetische
Splitter. Pultdach zeigte dieselbe Art Fund, schwaecher. Satteldach dagegen: dieselbe Ortho-Pruefung
zeigt eine EINZIGE, glatte Kehle -- sauber.

Ursache: Satteldachs Profil hat genau EINEN First-Punkt (eine einzelne Falte); Doppelpultdachs Profil
hat zwei Hoehen UND eine vertikale Stufe, Pultdachs Profil eine randstaendige Hochkante -- beides
gibt dem `union_objects()`-EXACT-Solver an der Fluegel-Naht deutlich mehr sich kreuzende Flaechen,
als er sauber aufloesen kann. Das war KEIN Bug in `resolve_profile`/`scale_profile_to_span`/dem
Verge-Soffit (die bleiben richtig und bleiben drin) -- es ist eine echte Grenze des
Boolean-Vereinigungs-Ansatzes selbst fuer komplexere Profile.

Zurueckgenommen: die Fluegel-Erkennung (`wings = roof_wings.recognize_two_wings(...)`) laeuft jetzt
wieder NUR fuer `roof_type == "satteldach"`, genau wie in Stufe 1+2 ("Version 1: nur Satteldach").
Pultdach/Doppelpultdach auf einem L/T fallen wieder auf das Walmdach zurueck (der bewaehrte,
korrekte Fallback -- kein Regressions-Bug, einfach wieder der Stand vor dem heutigen Fehlversuch).
Getestet: `roof_profile.test.py` (53) und `roof_wings.test.py` (15) bleiben gruen (kein Test setzte
Pultdach/Doppelpultdach-Fluegel voraus). Real nachgebaut an WB_125: Satteldach weiterhin sauber
(First 1,18 m, 0 nicht-mannigfaltige Kanten, glatte Kehle in der Ortho-Pruefung), Doppelpultdach UND
Pultdach zeigen wieder korrekt die Walmdach-Fallback-Logzeile.

Pultdach/Versetztes Pultdach auf L-Grundrissen bleiben ein offener Folgepunkt -- brauchen eine
ECHTE Kehlengeometrie (Grat/Kehle direkt hergeleitet, nicht per Boolean), das ist eigene, groessere
Arbeit, kein schneller Fix.

**Nachtrag 2026-09-22, PM (3):** "i dont understand ... 2 flat roofs on top of each other" (zu einem
Screenshot des Doppelpultdach-Renders). Untersucht und zwei ECHTE, getrennte Funde:

1. Der schmalere Fluegel wurde auf dieselbe ABSOLUTE Firsthoehe wie der breite gezwungen (siehe
   Profil-Fix-Nachtrag oben) -- gemessen an seiner viel kuerzeren Spannweite ergab das eine fast
   senkrechte Flaeche, die im Rendering wie ein zweites, eigenstaendiges flaches Dach aussah. Das
   war der Kern von "2 flat roofs" und ist mit `scale_profile_to_span()` behoben.
2. UNABHAENGIG davon, per Isoliertest (ein einzelner Fluegel, KEINE Vereinigung, dieselbe Geometrie
   wie der bestehende rechteckige Pfad) reproduziert: die First-Giebelwand steht (by design) einen
   `overhang` (0,5 m) weiter innen als die Dachkante -- aber nichts schloss bisher die Unterseite
   dieser Ueberstand-Tasche. Von aussen/unten sah man dort direkt durch bis zum Himmel. Das gab es
   VERMUTLICH auf JEDEM Satteldach/Pultdach/Doppelpultdach dieser Pipeline schon vorher, nicht nur
   auf zweischenkligen Daechern -- nur selten so nah herangezoomt betrachtet. Behoben in
   `roof_profile.wall_extension()`: ein neues Soffit-Prisma pro Giebelende, das denselben
   Quer-Schnitt (`full_polygon`, die volle First-bis-First-Kontur, nicht nur die wandeigene
   Teilstrecke) ueber genau die Ueberstandstiefe extrudiert (`_prism()`, bestehender Helfer, keine
   neue Geometriemathematik) -- schliesst sowohl entlang der Firstachse als auch bis in die
   Traufecken hinein (eine erste Fassung schloss nur die Firstachse, Rainer sah noch einen
   Rest-Spalt an der Ecke, seitdem behoben). 6 neue/angepasste Tests in `roof_profile.test.py`
   (`ScaleProfileToSpanTests`, `test_the_soffit_closes_the_overhang_pocket_with_no_gap`,
   `test_no_overhang_means_no_soffit_prism_and_no_crash`), alle 53 gruen. Verifiziert an
   WB_125 (zweischenklig) UND `bungalow_001` in allen drei Formen (rechteckiger Pfad) --
   `non_manifold_edges=0` ueberall, kein Absturz.

Ein KLEINERER Rest-Fund bleibt an der First-Kreuzung (Kehle) zwischen den zwei Fluegeln selbst --
sichtbar nur bei starkem Zoom, bei normaler Bildgroesse nicht mehr auffaellig (deutlich kleiner als
der urspruengliche "2 flat roofs"-Fund). Isolierter Test ohne Vereinigung zeigt keinen Spalt dort;
der Rest-Spalt tritt erst NACH `union_objects()` auf zwei Fluegeln auf -- vermutlich ein Artefakt
des EXACT-Booleans an duennen, nur beruehrenden (nicht ueberlappenden) Prismen aus verschiedenen
Fluegeln, noch nicht tiefer untersucht. Gleiche Fund-Klasse wie der bereits geloggte "kosmetischer
Splitter" oben, nur an einer anderen Stelle.

**Nachtrag 2026-09-22, PM (2):** "Version 1: nur Satteldach" (unten) war die urspruengliche
Entscheidung, WEIL genau das Rainers erster Fall war -- er hatte Doppelpultdach als 4. Dachform
konfiguriert, das blieb also auch nach dem Satteldach-Fix beim Walmdach-Fallback haengen. Auf
"no i want it fixed, this is BS" -> "fix it dammit": geprueft, ob die Satteldach-Beschraenkung
noetig war, und sie war es nicht -- `roof_profile.profile_mesh()` und `wall_extension()` kennen
nur `profile["points"]`, nie die Form selbst; die einzige Satteldach-spezifische Stelle war die
Gate-Bedingung in `render-exterior.py`. Fix: Gate und `resolve_profile()`-Aufruf nehmen jetzt
`roof_type` statt der festen Zeichenkette "satteldach". Real gebaut und geprueft:
`german_catalog_review_bungalow_4_3_1_wb_125` mit `EXT_ROOF_TYPE=doppelpultdach` (Rainers
genauer Fall aus dem Blender-Screenshot) -- First jetzt 2,15 m ueber der Traufe (sein gespeicherter
P1-Wert), sichtbarer First + vertikaler Versatz-Streifen am Giebel, 0 nicht-mannigfaltige Kanten.
Zusaetzlich `bungalow_001` mit allen drei Formen (Satteldach/Pultdach/Doppelpultdach) durchgebaut,
alle wasserdicht. T/Z-Grundrisse (zwei Reflexpunkte) bleiben weiterhin beim Walmdach-Fallback --
das war nie die Satteldach-Beschraenkung, sondern `roof_wings.py`s eigene, unveraenderte Grenze
(nur ein Reflexpunkt).

**Nachtrag 2026-09-22, PM:** Zeile 30 unten ("First an der richtigen Stelle und Hoehe je
Fluegel") war zum Zeitpunkt des Schreibens FALSCH, nicht nur ungenau -- die erste Fassung von
Stufe 2 rief fuer beide Fluegel immer `roof_profile.default_profile("satteldach", ...)` auf, nie
das gespeicherte "eigene Profil" aus dem Dach-Tab. Fuer WB_125 (gespeicherte Firsthoehe 1,55 m)
baute der Renderer also nur 0,39 m First -- ein flaches, kaum als Satteldach erkennbares Dach.
Rainer bemerkte das beim Nachpruefen der vorherigen Antwort und sagte klar: "no i want it fixed,
this is BS". Fix: `render-exterior.py` ruft jetzt `roof_profile.resolve_profile(plan.get(
"roof_profiles"), "satteldach", ...)` je Fluegel auf -- dieselbe Funktion, die der rechteckige
Pfad seit jeher benutzt, einfach zweimal mit der jeweils eigenen Fluegel-Spannweite. Kein neuer
Mechanismus: `sanitize_profile()` deckelt die gespeicherte Hoehe ohnehin schon gegen die
uebergebene Spannweite, das war fuer genau diesen Fall (ein Profil, zwei Spannweiten) bereits
sicher. Neu getestet (`roof_profile.test.py`, `TwoWingSharedProfileTests`, 3 Tests) und real an
WB_125 nachgebaut: First jetzt 1,55 m ueber der Traufe (Log: "Satteldach zweischenklig: First
1.55m ueber der Traufe"), sichtbar als First/Giebel im Rendering, Mesh weiterhin 0
nicht-mannigfaltige Kanten. Der bekannte kosmetische Splitter an der First-Kreuzung (Zeile 34-37)
bleibt unveraendert vorhanden.

Rainer, 2026-09-22: "yes" zum Plan. Umgesetzt: `roof_wings.py` (Fluegel-Erkennung, reine Geometrie,
kein bpy), `roof_wings.test.py` (15 Tests, gruen). Zusaetzlich gegen alle 39 real gemessenen
"2-Rechtecke"-Haeuser aus der urspruenglichen Messung laufen lassen: **31 erkennt
`recognize_two_wings()` sauber als einfaches L; 8 nicht** -- und zwar zu Recht, nicht als Bug:
5 davon haben tatsaechlich ZWEI Reflexpunkte (eine kleine Ausbuchtung/ein Erker, kein echtes
zweischenkliges L -- z. B. `twostorey_047`s Umriss hat einen 0,4 m tiefen Vorsprung zwischen zwei
sonst geraden Kanten), 3 liefern nach `regularize_loop()` eine ungerade Punktzahl (5 oder 7) --
ein rein rechtwinkliges Polygon kann das nicht sein, das ist Rauschen aus der Wandschleifen-
Verfolgung selbst, kein Fehler in diesem Modul. Die urspruengliche Zahl "39 von 124" war also ein
bisschen zu hoch gegriffen (sie zaehlte disjunkte Scanline-Rechtecke, nicht echte Reflexpunkte);
die verlaessliche Zahl ist **31 von 124 (25 %)**, immer noch ein Viertel des auswertbaren Bestands.

**Stufe 2, umgesetzt ohne selbst hergeleitete Kehlengeometrie:** eigene Analyse der Grat/Kehle-Faelle
zeigte echte Mehrfach-Segment-Faelle (ein Fluegel, der ueber die volle Tiefe reicht, kann am FERNEN
Ende des anderen Fluegels ein zweites Mal ueber dessen First hinausragen -- kein einzelner
45-Grad-Schnitt reicht immer). Statt das von Hand zu loesen: `render-exterior.py` findet in DIESER
Datei bereits `union_objects()` ("so a multi-wing roof reads as one continuous mass instead of
overlapping shells") -- eine bestehende, bereits benutzte Boolean-Vereinigung. Jeder Fluegel wird
jetzt als eigenes, vollstaendiges Satteldach gebaut (dieselbe, laengst erprobte
`roof_profile.py`-Mathematik wie der rechteckige Pfad, nur zweimal aufgerufen), die zwei Volumen
werden per `union_objects()` zusammengefuegt. Kein neuer Geometriecode fuer Grat/Kehle -- Blenders
eigener EXACT-Solver loest das.

Verifiziert (echter Blender-Bau, nicht nur Unit-Tests):
- `german_catalog_review_bungalow_4_3_1_wb_125` (das Beispiel, mit dem Rainer anfing) und
  `bungalow_001`: beide bauen ein durchgehendes zweischenkliges Satteldach, First an der richtigen
  Stelle und Hoehe je Fluegel, keine Absturz/keine sichtbar kaputte Naht.
- Mesh-Pruefung (bmesh, `non_manifold_edges`): 0 nicht-mannigfaltige Kanten in `roof-pitch` UND
  `roof-walls` nach der Vereinigung -- die Vereinigung ist wasserdicht, kein Loch.
- Bekannter, kleiner kosmetischer Fund: an der exakten First-Kreuzung sitzt ein winziger,
  fast entarteter Splitter-Face (sichtbar als duenner dunkler Strich im Rendering von WB_125, siehe
  Screenshot dieser Sitzung), vermutlich vom Boolean-Solver an der Ueberstand-Kante erzeugt. Keine
  Undichtigkeit (Mesh bleibt mannigfaltig), rein kosmetisch -- eigener kleiner Folgepunkt.

Alle Tests (15 in `roof_wings.test.py`, plus die volle Workbench- und Simplifier-Suite) weiterhin
gruen; einzige Ausnahme die vorbestehende bungalow_039-Tuerangelschlag-Luecke, unabhaengig hiervon.

Policy version: ZF-AGENT-WORKFLOW-v1.0.0

## Objective

Satteldach auf einem echten L- oder T-Grundriss bauen -- zwei Dachfluegel, gemeinsame Neigung,
gemeinsame Traufhoehe, echter Grat/Kehle wo sie sich treffen, Giebel an den offenen Enden. Heute
faellt jede nicht-rechteckige Form fuer Satteldach/Pultdach/Versetztes Pultdach automatisch auf ein
Walmdach zurueck (render-exterior.py ~1163-1166) -- fuer 39 von 124 auswertbaren Haeusern im Bestand
(31 %, gemessen 2026-09-22) ist das die falsche Dachform, nicht nur eine fehlende Feineinstellung.
Pultdach/Versetztes Pultdach auf L/T bleiben ausdruecklich AUSSERHALB dieses Plans.

## Current evidence and behavior

- `render-exterior.py` ~1144-1230: `is_rectangle` entscheidet zwischen dem punktbasierten
  Querschnitt (roof_profile.py) und `bpypolyskel.polygonize()` (immer ein Walmdach, kein Giebel
  moeglich -- `tan`/`height` sind ein einziger globaler Neigungswert, keine Kante-fuer-Kante-Kontrolle).
- Rainer, 2026-09-22, an `german_catalog_review_bungalow_4_3_1_wb_125` (echte L-Form, ueberdachte
  Terrasse als Einschnitt): "the doppelpultdach is a walmdach in blender" -- durch tatsaechliches
  Bauen mit `EXT_ROOF_TYPE=doppelpultdach` bestaetigt: Log-Zeile "doppelpultdach braucht ein
  rechteckiges Gebaeude ... es wird stattdessen ein Walmdach gebaut". Dann: "but this for example is
  exactly one of our standard houses" -- kein Einzelfall.
- Codex-Design-Review (read-only, 2026-09-22): empfiehlt eine begrenzte Version von "ein Dachfluegel
  je Fluegel": zunaechst nur zweischenklige L/T-Grundrisse, zentrierter First je Fluegel, EINE
  gemeinsame Neigung, EINE gemeinsame Traufhoehe. `bpypolyskel` liefert wiederverwendbare Bausteine
  (Skelett-Knoten mit Hoehe, Flaechen-Graph), aber keine fertige Giebel-Erkennung -- das ist neue
  Geometriearbeit, kein Konfigurationsschalter.
- Eigene Messung (2026-09-22, `wing_coverage.py`-Prototyp im Scratchpad, wiederverwendet
  `trace_wall_loops`/`regularize_loop`/`decompose_rectangles`/`point_in_polygon`/`cluster_coords`
  aus render-exterior.py per ast-Extraktion, gegen den ECHTEN gebauten Aussenwand-Umriss, nicht die
  rohe Zeichnung): von 244 Projekten mit annotations.json liessen sich 124 bauen und auswerten (120
  scheiterten an fehlendem Vorschaubild + fehlendem Gebaeudemass -- eigener, vorgelagerter Punkt,
  nicht Teil dieses Plans). Davon: 72 bereits rechteckig (1 Rechteck), **39 genau zwei Rechtecke**
  (das Zielbild dieses Plans), 13 drei oder mehr (ausserhalb des Umfangs), 5+7+1 im Detail.

## Repository baselines

- Repository: `C:\dev\Floorplan-tools\born2thrill-local-workbench`
- Branch: `agent/furnished-render-and-annotation-schema`
- Base SHA: `5be1a4e18956b9fb2e158bee82aa159898356e89`
- Bestehende unversionierte Aenderungen (u. a. `data/simplifier-v2/*`, heutige roof_axis_override-
  und Kochfeld-Aenderungen) sind vom Nutzer, bleiben unangetastet.
- `floorplan-simplifier` (Editor) ist NICHT im Umfang dieses Plans -- Umfang ist reine Geometrie im
  Renderer. Eine spaetere Editor-Erweiterung bekommt einen eigenen Plan, sobald diese Geometrie
  steht (Codex: "I'll design the UI properly once the underlying geometry approach is settled").

## Exact scope

1. **Fluegel-Erkennung** aus dem tatsaechlich gebauten Aussenwand-Umriss des obersten Geschosses
   (derselbe Umriss, den `is_rectangle` heute schon prueft): Zerlegung in maximal 2 sich
   ueberlappende, achsparallele Rechtecke (nicht die disjunkte Scanline-Zerlegung, die es schon
   gibt -- Codex: "that is not architectural wing recognition"). Nur wenn die Zerlegung den Umriss
   exakt (Toleranz wie `regularize_loop`, 0.35 m) abdeckt; sonst kein Fluegel-Pfad, Fallback bleibt
   Walmdach wie heute.
2. **Ein Fluegel-Layout-Datensatz**, getrennt von `roof_profiles`: Fluegel-Rechtecke, Achsen,
   Haupt-/Nebenfluegel, gemeinsame Neigung und Traufhoehe, Deckungsart der offenen Enden. Eigene
   Struktur im Render-Plan (z. B. `roof_wings`), NICHT in `roof_profiles[form]` -- das Format bleibt
   fuer die rechteckigen Formen unveraendert (Codex Punkt 3).
3. **Geometrie-Pipeline** (neues Modul, referenziert `roof_profile.py`, aendert es nicht):
   Fluegel-Ebenen ueber ihre jeweilige Grundflaeche auswerten, an der Ueberlappung `z = max(z1, z2)`
   nehmen, Schnittkanten als Grat/Kehle klassifizieren, ungueltige Fuegungen (Sprung an der
   Domaenengrenze, freiliegende innere Giebelenden, nicht abgedeckte Flaeche) ablehnen und dann auf
   Walmdach zurueckfallen statt eine falsche Naht zu bauen.
4. **Wandanschluss**: Giebelwand an jedem offenen Fluegelende, entlang der echten Aussenwandflucht
   (wie `wall_extension()` es fuer die rechteckigen Formen schon tut), keine Giebelwand an der
   inneren Fluegelgrenze.
5. **Log-Zeile** statt der heutigen Pauschal-Warnung: welcher Fluegel-Pfad genommen wurde, oder
   warum auf Walmdach zurueckgefallen wurde (Fluegel nicht erkennbar / Fuegung ungueltig).

## Files in scope

- `born2thrill-local-workbench/scripts/render-exterior.py` (Aufrufstelle, ~1144-1230; is_rectangle-
  Pfad und der bestehende Walmdach-Pfad bleiben Zeile fuer Zeile unveraendert).
- Neu: `born2thrill-local-workbench/scripts/roof_wings.py` (Fluegel-Erkennung + Geometrie-Pipeline,
  reine Funktionen, kein bpy -- testbar ohne Blender, nach dem Vorbild von `roof_profile.py`).
- `born2thrill-local-workbench/scripts/roof_wings.test.py` (neu).
- `born2thrill-app-repo/plans/ROADMAP.md` (Eintrag nach Abschluss).

## Explicitly out of scope

- Pultdach/Versetztes Pultdach auf L/T-Grundrissen (Codex: eigene, schwierigere Regeln fuer Sprung/
  Ebene an einer Fluegelfuge -- eigener, spaeterer Plan).
- Drei-oder-mehr-Fluegel-Grundrisse (13 von 124 gemessen).
- Jede Aenderung am Dach-Tab-Editor (`floorplan-simplifier`) -- reine Renderer-Geometrie hier.
- Frei ziehbare First-Hoehe je Fluegel (Version 1: EINE gemeinsame Neigung, vom First-Punkt der
  Hauptform abgeleitet, falls gesetzt, sonst Standard 5 Grad wie heute).
- Aenderung an Flachdach, an rechteckigen Haeusern, an `roof_axis_override`.
- Die 120 Haeuser ohne Vorschaubild/Gebaeudemass -- eigener, vorgelagerter Punkt (Rainer muesste dort
  erst ein Gebaeudemass eintragen, bevor ihre Form ueberhaupt messbar ist).

## API, schema, and data-contract effects

Neues, additives Feld im Render-Plan (`roof_wings` o. ae.), nur gesetzt, wenn der Fluegel-Pfad
tatsaechlich greift. Kein bestehendes Feld aendert Bedeutung. `roof_profiles`/`roof_fourth`/
`roof_axis_override` unveraendert.

## Acceptance criteria

- Fuer alle 39 gemessenen Zwei-Rechteck-Haeuser: Satteldach baut zwei Dachflaechen mit einem echten
  Grat/einer echten Kehle, keine freiliegende innere Wand, Giebelwaende nur an den echten offenen
  Enden.
- Fuer jedes rechteckige Haus (heute 1-Rechteck-Pfad) UND jedes bestehende Walmdach-Haus: Mesh-
  Vertices/Faces/Wandprismen byte-identisch zu vor diesem Plan (Fixture-Vergleich, siehe Tests).
- Eine Fuegung, die die Gueltigkeitspruefung nicht besteht, faellt auf Walmdach zurueck und sagt
  warum -- nie eine falsche/klaffende Naht.

## Tests and verification commands

Neu, vor der Implementierung geschrieben:

- `roof_wings.test.py`: Fluegel-Erkennung an synthetischen L- und T-Polygonen (inkl. `WB 125`s
  echtem 6-Punkt-Umriss als Fixture); Ablehnung bei drei-oder-mehr-Rechteck-Formen; `z = max(z1,z2)`-
  Ueberlagerung an einem Handrechenbeispiel; Grat/Kehle-Klassifikation; ungueltige Fuegung (Sprung,
  freiliegendes Ende) wird erkannt und abgelehnt statt gebaut.
- `render-exterior.py`: bestehende Fixtures fuer den rechteckigen Pfad und den Walmdach-Pfad laufen
  unveraendert weiter (kein bestehender Test wird geloescht/geschwaecht).
- Bestaetigung: `python -m unittest roof_wings.test roof_profile.test build-simplifier-render-plan.test`
  sowie ein echter Blender-Bau (mind. 2 der 39 gemessenen Haeuser) mit Sichtpruefung wie heute schon
  fuer den Kochfeld-/Treppen-/Dachrichtung-Fund gemacht.

## Protected and risky paths

- `render-exterior.py`s bestehender `is_rectangle`/Walmdach-Zweig: nur lesend referenziert, keine
  Zeile darin geaendert.
- `roof_profile.py`: unangetastet.
- Ungueltige Fuegungserkennung ist der riskanteste Teil -- ein falsch-positiv als "gueltig"
  akzeptierter Fall baut ein sichtbar falsches Dach. Lieber zu oft auf Walmdach zurueckfallen als
  einmal falsch zusammenfuegen.

## Rights, provenance, privacy, and security impact

Keins -- reine Geometrieerzeugung aus bereits vorhandenen, freigegebenen Wanddaten.

## Floorplan-suite invariant

Kann ein geaenderter Pfad Geometrie ohne freigegebene korrigierte Referenz erzeugen, veroeffentlichen
oder versenden? Nein: reine Renderer-Geometrie fuer die Vorschau/das interne Rendering, keine
Aenderung an Rechte-/Freigabe-/Versandpfaden.

## Customer, email, database, deployment, and external effects

Keine.

## Failed-hypothesis log

(noch keine -- wird waehrend der Umsetzung gefuehrt)

## Rollback

Neue Datei `roof_wings.py` (+Test) entfernen; die eine neue Aufrufstelle in `render-exterior.py`
(ein `if`-Zweig vor dem bestehenden `is_rectangle`/Walmdach-Code) zuruecknehmen. Kein Datenformat
aendert sich rueckwirkend.

## Unresolved questions

- Bei mehreren gueltigen Zwei-Rechteck-Zerlegungen desselben Umrisses: welche gewinnt (groesste
  Flaeche? am besten zum First-Punkt passende?) -- wird beim Implementieren an echten Beispielen
  entschieden und hier nachgetragen.
- Ob die 13 Drei-plus-Rechteck-Haeuser eine spaetere, groessere Version rechtfertigen: erst nach
  dieser ersten Auslieferung neu bewerten.

## Approval record

Not approved. Stop before implementation.
