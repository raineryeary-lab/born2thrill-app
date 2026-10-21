#!/usr/bin/env python3
"""Eine Codex-Lieferung pruefen und, wenn sie besteht, annehmen.

Rainer, 2026-08-27: "wieso werden so viele unterschiedliche ordner
verwendet?" Drei Stellen im Code erfanden drei Ordnernamen, und keine kannte
die andere:

    make-codex-job.py      schreibt in den Auftrag  codex-<plan>-<datum>
    publish/route.ts       liest fuer den Bilder-Tab  codex-final-*, neuester
    codex-rueckgabe/route  kopiert nach              codex-final-<stempel>
    publish-renders.py     laedt hoch                was in --dir steht

Der Auftrag schickte Codex also in einen Ordner, den der Bilder-Tab nie
ansah. `bungalow_039` hat acht `codex-final-*`-Ordner, und "neuester gewinnt"
sortiert alphabetisch -- `codex-final-2026-08-26-v2` schlaegt das juengere
`codex-final-2026-08-26-2110`.

Ab hier gibt es eine Wahrheit je Haus: `renders/ANGENOMMEN.json`. Dort steht
genau ein Ordner, und dorthin kommt nur, was diese Pruefung besteht.

    python lieferung-pruefen.py <plan> <ordner>
    python lieferung-pruefen.py <plan> <ordner> --annehmen

Was hier NICHT geprueft werden kann: ob die Badewanne wirklich im Bild ist.
Das bleibt der Blick eines Menschen. Der Pruefer haelt nur das fest, was
messbar ist -- und genau daran ist heute jede Runde gescheitert.
"""

import argparse
import datetime
import hashlib
import json
import math
import os
import re
import struct
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
# Nicht raten. 2026-08-21: der Datenordner zog von C: nach E:; ein stiller
# Rueckfall auf den alten Nachbarordner wuerde unbemerkt gegen veraltete
# Daten arbeiten.
_konfiguriert = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR", "").strip()
if not _konfiguriert:
    sys.exit("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt -- verweigere, "
             "den Datenordner zu erraten. Siehe .env.local.")
DATA = os.path.abspath(_konfiguriert)

ZEIGER = "ANGENOMMEN.json"
STATUS_ZU_FARBE = {"ersetzt": "ersetzen", "sichtbar": "bleibt"}

# Wie weit die gemeldete Sichtstelle vom Marker abweichen darf.
#
# Der Marker sitzt im Schwerpunkt des Objekts, das Objekt hat Ausdehnung --
# eine Kuechenzeile ist breiter als ein Wasserhahn. 300 Pixel auf 2000 sind
# grosszuegig gewaehlt: die Zahl soll Erfundenes fangen, nicht Genauigkeit
# erzwingen, die niemand liefern kann. Sie gehoert nachgeschaerft, sobald
# genug echte Sichtstellen vorliegen -- bis dahin steht sie hier bewusst weit.
BELEG_RADIUS_PX = 300.0

# Um so viel muss ein Bild SCHLECHTER sein als das beste, um als Ausreisser zu
# gelten. Rainer, 2026-08-30, dritte Runde an 3_3_2: das Wohnzimmer war
# repariert, es blieben neun Beanstandungen, alle im Bad -- und im Bad kam kein
# einziges Bild je naeher als 155 Pixel an die Planstelle, waehrend das
# Wohnzimmer auf 4 bis 57 herankam. Ein gleichmaessiger Versatz ist unser
# Massstab (Objektursprung statt sichtbarer Mitte) und nicht ihre Lieferung.
# Erst wer AUS DER REIHE faellt, hat umgeraeumt.
AUSREISSER_PX = 150.0


class Beanstandet(Exception):
    """Die Lieferung besteht die Pruefung nicht und wird nicht angenommen."""

    def __init__(self, beanstandungen):
        super().__init__("; ".join(beanstandungen))
        self.beanstandungen = beanstandungen


def png_groesse(pfad):
    """Pixelmasze aus dem PNG-Header -- ohne Zusatzbibliothek."""
    magisch = bytes([137, 80, 78, 71, 13, 10, 26, 10])
    try:
        with open(pfad, "rb") as datei:
            kopf = datei.read(24)
    except OSError:
        return None
    if kopf[:8] != magisch:
        return None
    return [int.from_bytes(kopf[16:20], "big"), int.from_bytes(kopf[20:24], "big")]


def sha256(pfad):
    digest = hashlib.sha256()
    with open(pfad, "rb") as datei:
        for brocken in iter(lambda: datei.read(1 << 20), b""):
            digest.update(brocken)
    return digest.hexdigest()


def _karte_deckt_bild(karte_datei, source_blend):
    """Zeigt diese Objektkarte das Geschoss, aus dem dieses Bild stammt?

    Rainer, 2026-08-28: der Finalsatz von `onehalfstorey_020` war
    einwandfrei und fiel mit vier Beanstandungen durch. Die Karte hiess
    `OBJEKTKARTE-interior-modern-baseline.png` und zeigte das Erdgeschoss;
    die vier Bilder kamen aus `interior-modern-upper-baseline.blend`. Fuer
    sie gab es nichts zu bestaetigen -- der Auftrag hatte ausdruecklich
    verboten, etwas zu erfinden.

    Die Regel oeffnet nur, wo nachweisbar keine Karte existiert. Ohne
    `source_blend` laesst sich die Herkunft nicht bestimmen, dann bleibt der
    marker_check Pflicht: sonst genuegte ein weggelassenes Feld, um die
    Pruefung zu umgehen.
    """
    if not karte_datei or not source_blend:
        return True
    stamm = os.path.basename(karte_datei)
    for vorne in ("OBJEKTKARTE-",):
        if stamm.startswith(vorne):
            stamm = stamm[len(vorne):]
    stamm = os.path.splitext(stamm)[0]
    return stamm == os.path.splitext(os.path.basename(source_blend))[0]


def beleg_gilt(job, katalog):
    """Verlangt DIESE Lieferung einen Beleg?

    Eine neue Forderung wirkt nicht nach hinten. Der Gate stand zuerst nur am
    Auftrag (`beleg_verlangt`) -- das reicht nicht, weil `go.py` den Auftrag
    bei jedem Lauf neu erzeugt.

    Rainer, 2026-08-30: dieselbe Lieferung war am 2026-08-29 formal in
    Ordnung und bekam einen Tag spaeter 152 Beanstandungen, alle "ist als
    sichtbar gemeldet, aber ohne `bei`". Nachgesehen:

        Lieferung   job_id ...-2026-08-29
        Auftrag     job_id ...-2026-08-30   beleg_verlangt: True

    Sie antwortete auf den Auftrag von gestern und wurde gegen den von heute
    gemessen. Also wird die Kennung verglichen: nur wer denselben Auftrag
    beantwortet, wird an ihm gemessen.

    Verschont wird nur, wo BEIDE Kennungen dastehen und sich unterscheiden.
    Fehlt eine, zaehlt die Forderung -- alles andere waere zu grosszuegig: die
    Pruefung liesse sich dann abschalten, indem man die Kennung weglaesst.
    """
    if not job.get("beleg_verlangt"):
        return False
    auftrag_id = job.get("job_id")
    lieferung_id = (katalog or {}).get("job_id")
    if auftrag_id and lieferung_id and auftrag_id != lieferung_id:
        return False
    return True


def _marker_beanstandungen(name, geprueft, karte, gedeckt=True, bildmasz=None,
                           beleg_verlangt=False, quergeprueft=()):
    """Der marker_check aus Abschnitt 11.1 des Regelwerks.

    Vollstaendigkeit ist die Untergrenze, nicht der Beweis: am 2026-08-27 wies
    ein Bild die Badewanne als "sichtbar" aus, obwohl sie fehlte. Eine
    vollstaendige Liste kann gelogen sein -- eine unvollstaendige ist schon
    formal keine Lieferung.
    """
    if not karte:
        return []
    if not geprueft:
        # Ausserhalb der Karte gibt es nichts zu bestaetigen.
        return ["%s: marker_check fehlt" % name] if gedeckt else []
    schlecht = []
    nummern = [eintrag.get("n") for eintrag in geprueft]
    fehlend = sorted(set(karte) - set(nummern))
    doppelt = sorted({n for n in nummern if nummern.count(n) > 1})
    fremd = sorted(n for n in set(nummern) - set(karte) if n is not None)
    if fehlend:
        schlecht.append("%s: Marker fehlen im marker_check %s" % (name, fehlend))
    if doppelt:
        schlecht.append("%s: Marker doppelt im marker_check %s" % (name, doppelt))
    if fremd:
        schlecht.append("%s: unbekannte Marker im marker_check %s" % (name, fremd))
    for eintrag in geprueft:
        status = eintrag.get("status")
        if status not in STATUS_ZU_FARBE:
            schlecht.append("%s: Marker %s hat den Status '%s' -- erlaubt sind "
                            "sichtbar und ersetzt" % (name, eintrag.get("n"), status))
            continue
        marker = karte.get(eintrag.get("n"))
        if marker and marker.get("farbe") != STATUS_ZU_FARBE[status]:
            schlecht.append(
                "%s: Marker %s (%s) ist %s, Status sagt '%s' -- passt nicht zur Farbe"
                % (name, eintrag.get("n"), marker.get("name"),
                   "blau/bleibt" if marker.get("farbe") == "bleibt" else "rot/ersetzen",
                   status))
            continue
        if status == "sichtbar" and marker and beleg_verlangt:
            schlecht += _beleg_beanstandungen(
                name, eintrag, marker, bildmasz,
                # Ueber dieses Objekt urteilt `verschobene_objekte` gegen das
                # beste Bild -- ein zweites Urteil gegen den Plan allein waere
                # derselbe Vorwurf mit dem schlechteren Massstab.
                abstand_pruefen=marker.get("name") not in quergeprueft)
    return schlecht


def _beleg_beanstandungen(name, eintrag, marker, bildmasz,
                          abstand_pruefen=True):
    """Die Sichtstelle zu einem blauen Marker pruefen.

    Rainer, 2026-08-29: bevor ein geschlossener Kreis mit Codex Sinn ergibt,
    muss die Fehlerklasse weg -- "ein Objekt, das bleiben muss, ist
    verschwunden, und der marker_check meldete sichtbar". Dreimal in drei
    Tagen: Badewanne, Schreibtisch, Waschmaschine und Trockner.

    Eine Behauptung laesst sich nicht pruefen, eine Koordinate schon. `bei`
    ist der Pixel, an dem Codex das Objekt IM GELIEFERTEN BILD sieht. Wer sie
    hinschreibt, muss hinsehen.

    Ohne `px` am Marker (aeltere Auftraege) gibt es nichts zu vergleichen, und
    dann wird auch nichts verlangt.
    """
    if not marker.get("px"):
        return []
    bei = eintrag.get("bei")
    if not bei:
        return ["%s: Marker %s (%s) ist als sichtbar gemeldet, aber ohne `bei` "
                "-- wo genau im Bild?" % (name, eintrag.get("n"), marker.get("name"))]
    try:
        x, y = float(bei[0]), float(bei[1])
    except (TypeError, ValueError, IndexError):
        return ["%s: Marker %s hat ein unlesbares `bei`: %r"
                % (name, eintrag.get("n"), bei)]
    if bildmasz and not (0 <= x < bildmasz[0] and 0 <= y < bildmasz[1]):
        return ["%s: Marker %s (%s) wird bei %d,%d gemeldet -- ausserhalb des "
                "Bildes (%d x %d)" % (name, eintrag.get("n"), marker.get("name"),
                                      x, y, bildmasz[0], bildmasz[1])]
    if not abstand_pruefen:
        return []
    mx, my = marker["px"]
    abstand = math.hypot(x - mx, y - my)
    if abstand > BELEG_RADIUS_PX:
        return ["%s: Marker %s (%s) wird %d Pixel weit von seinem Marker "
                "gemeldet (bei %d,%d, Marker %d,%d) -- entweder ist das ein "
                "anderes Objekt oder die Zahl ist erfunden"
                % (name, eintrag.get("n"), marker.get("name"), abstand,
                   x, y, mx, my)]
    return []


# Zwischenstandsnamen, die Codex vergeben darf: `-review`, `-review-2`, `-v3`.
# Regelwerk Abschnitt 12 verlangt sie sogar, damit ein ungeprueftes Bild nicht
# den geforderten Namen belegt.
ZWISCHENSTAND = re.compile(r"-(?:review|v\d+)(?:-\d+)?$", re.IGNORECASE)

# Die beiseitegelegte alte Fassung. Regelwerk Abschnitt 12 verlangt sie bei
# einer Nachbesserung -- sie ist der Beleg, wogegen nachgebessert wurde.
VORHER = re.compile(r"-vorher-\d+", re.IGNORECASE)
VORHER_ORDNER = "vorher"


def _grundname(dateiname):
    """Der geforderte Name hinter einem Zwischenstandsnamen.

    Rainer, 2026-08-28: "das muss jetzt endlich vorbei sein." Zweimal in
    Folge hing eine sonst fehlerfreie Lieferung allein am Suffix --
    `onehalfstorey_020` mit `-review` und `-review-2`,
    `german_catalog_review_bungalow_3_2_4_b_100_1` mit `-review`. Jedes Mal
    eine ganze Runde bei Codex, nur damit sechs Dateien anders heissen.

    Der Name zaehlt an genau einer Stelle: `publish-renders.py` macht aus ihm
    den WordPress-Slug. Das laesst sich hier loesen. Dass Codex die
    angenommenen Bilder danach nie wieder anfasst, ist der eigentliche
    Gewinn -- ein Bild, das niemand neu rendert, kann nichts mehr verlieren.
    """
    stamm, endung = os.path.splitext(dateiname)
    return ZWISCHENSTAND.sub("", stamm) + endung


def zuordnung(job, ordner):
    """Gefordeter Name -> Datei, die im Ordner dafuer dasteht."""
    soll = {eintrag["filename_hint"] for eintrag in job.get("required_outputs", [])}
    gefunden = {}
    for name in sorted(os.listdir(ordner)):
        if VORHER.search(name):
            continue
        grund = _grundname(name)
        if grund in soll and grund not in gefunden:
            gefunden[grund] = name
    return gefunden


# Ein Platzhalter ist ein glatter grauer Quader. War er im Baseline-Render so
# flach und ist er es in der Lieferung immer noch, wurde er nicht eingerichtet.
# Beide Schwellen sind an onehalfstorey_020 gemessen (siehe Test).
KASTEN_WAR_FLACH = 50.0     # darunter war es nie ein Kasten -- nichts zu sagen
KASTEN_BLEIBT_FLACH = 65.0  # darueber ist es in der Lieferung immer noch einer


def kasten_verdacht(gemessen):
    """Welche `ersetzen`-Marker sehen noch nach Platzhalter aus?

    Rainer, 2026-08-28: "you have to force the rendering of deco stuff for the
    'stuff', often it just creates a large box."

    Das Regelwerk verlangt das Ersetzen seit Wochen, und der `marker_check`
    fragt es ab -- aber der ist eine Selbstauskunft, und die war schon falsch
    (die Badewanne stand als "sichtbar" drin und fehlte). Hier wird gemessen
    statt gefragt.

    `gemessen` ist {name: (farbe, flachanteil_baseline, flachanteil_lieferung)}
    in Prozent. Gefragt wird zweimal: war die Stelle im Baseline-Render ein
    glatter Quader, UND ist sie es in der Lieferung immer noch.

    Der erste Anlauf fragte statt der zweiten Bedingung nach dem Abfall und
    schlug bei zwei fertig eingerichteten Stellen an -- einmal hatte ein
    Tuerblatt den Kasten ersetzt, einmal eine Wand mit Bild. Beide sind selbst
    flach, fallen aber deutlich unter 65 %. Ueber die zwei angenommenen
    Lieferungen vom 2026-08-28 meldet die schaerfere Fassung genau einen
    Marker, und der steht wirklich noch leer.

    Bleibt eine WARNUNG, keine Beanstandung: ein echter Treffer als Beleg ist
    zu wenig, um eine fertige Lieferung zu blockieren.
    """
    verdaechtig = []
    for name, werte in (gemessen or {}).items():
        try:
            farbe, vorher, nachher = werte
        except (TypeError, ValueError):
            continue
        if farbe != "ersetzen":
            continue
        if vorher < KASTEN_WAR_FLACH:
            # Verdeckt, angeschnitten oder nie ein Quader gewesen.
            continue
        # `nachher` ist die Messung aus JEDEM Lieferbild, nicht nur aus dem
        # ersten. Der Docstring hier behauptete bis zum 2026-09-01: "ein
        # Platzhalter, der in einem Stil ein Kasten blieb, ist es in allen
        # vieren." An 3_3_4 widerlegt -- stuff-9 war in 03 und 06 ein glatter
        # Kasten und in 04 und 05 eine fertige Kuechenzeile. Die Warnung kam
        # nur, weil 03 zufaellig das erste Bild ist.
        #
        # Eine Zahl statt einer Liste bleibt gueltig: alte Messungen und alte
        # Aufrufer sollen nicht daran scheitern.
        werte_nachher = nachher if isinstance(nachher, (list, tuple)) else [nachher]
        if any(w >= KASTEN_BLEIBT_FLACH for w in werte_nachher):
            verdaechtig.append(name)
    return sorted(verdaechtig)


# Ab so vielen Bildern ist ein zeichengleicher Befund kein Zufall mehr. Zwei
# Bilder koennen gleich ausfallen; vier nicht.
GLEICHE_BEFUNDE_AB = 3


def abgeschriebene_marker(katalog):
    """Vier verschieden gestylte Bilder mit demselben Befund.

    Rainer, 2026-08-30, an german_catalog_review_bungalow_3_3_2_b_100_2: in
    DREI von vier Grundrissen standen Sitz- und Essgruppe woanders als im
    Bauplan -- zweimal vertauscht, einmal quer durch den Raum gewandert.
    Trotzdem meldete die catalog.json in allen vier Bildern 34 von 34 Markern
    als sichtbar, mit `bei`-Koordinaten, die untereinander zeichengleich und
    pixelgenau die `px` aus dem Auftrag waren.

    Der aeltere Beleg (`_beleg_beanstandungen`: `bei` nahe am Marker) belohnt
    genau das -- wer die Zahl aus dem Auftrag abschreibt, besteht ihn immer.
    Er faengt eine erfundene Zahl, aber keine abgeschriebene.

    Diese Pruefung behauptet NICHT, dass die Bilder falsch sind. Sie sagt, dass
    der Befund keiner ist. Vier getrennt gerenderte Bilder mit anderem Stil,
    anderem Licht und anderer Ausstattung ergeben nicht denselben Pixelbefund;
    wer das meldet, hat einmal hingesehen und dreimal abgeschrieben, oder
    keinmal. Und ein falsch abgehakter Marker wiegt schwerer als der Fehler
    selbst, weil er ihn verdeckt (Regelwerk 10.7).

    Ohne `bei` gibt es nichts zu vergleichen: aeltere Auftraege verlangen keine
    Koordinate, und vier gleiche Statuslisten sind dann normal.
    """
    bilder = katalog.get("images") or katalog.get("entries") or []
    fingerabdruecke = {}
    for bild in bilder:
        geprueft = bild.get("marker_check")
        if not geprueft:
            continue
        if not any(eintrag.get("bei") for eintrag in geprueft):
            continue
        abdruck = json.dumps(
            [[eintrag.get("n"), eintrag.get("status"), eintrag.get("bei")]
             for eintrag in geprueft], sort_keys=True)
        fingerabdruecke.setdefault(abdruck, []).append(
            bild.get("filename") or "(ohne Namen)")
    for namen in fingerabdruecke.values():
        if len(namen) >= GLEICHE_BEFUNDE_AB:
            return ["%d Bilder haben einen zeichengleichen marker_check (%s) -- "
                    "verschieden gestylte Bilder ergeben nicht denselben "
                    "Pixelbefund. Der Befund ist abgeschrieben, nicht geprueft "
                    "(Regelwerk 10.7)." % (len(namen), ", ".join(sorted(namen)))]
    return []


def verschobene_objekte(job, katalog):
    """Jedes Objekt gegen das BESTE der Bilder messen, nicht gegen den Plan.

    Rainer, 2026-08-30, nachdem Codex aufgehoert hatte abzuschreiben: der
    Pruefer meldete 14 Beanstandungen an 3_3_2. Ueber alle vier Bilder je
    Objekt nachgerechnet zerfielen sie in zwei Gruppen:

        essgruppe_6-5        233   10  226  262   Bild 04 trifft, drei nicht
        doppelwaschtisch-23  308  346  347  511   KEINES trifft

    Trifft ein Bild, ist die Planstelle gut und die anderen haben wirklich
    umgeraeumt. Trifft keines, liegt es nicht an den Bildern, sondern an
    unserem Massstab: `px` ist in make-codex-job.py der projizierte URSPRUNG
    des fuehrenden Netzes, nicht die sichtbare Mitte. Am Baseline-Render
    nachgesehen -- an der Planstelle von `wand_wc-24` ist gar kein WC, dort
    ist eine Wandecke. Bei einem wandhaengenden oder zweiteiligen Objekt
    (`teile: 2` beim Doppelwaschtisch) sitzt der Ursprung neben dem Sichtbaren.

    Ein systematischer Versatz kuerzt sich so heraus; echtes Umraeumen bleibt.

    Bei EINEM Bild gibt es kein "bestes" -- dann bleibt die aeltere Regel
    gegen den Plan (`_beleg_beanstandungen`) die einzige, die es gibt.

    Gibt drei Dinge zurueck: die Beanstandungen; die Objekte, bei denen kein
    Bild traf; und die Namen, ueber die hier ueberhaupt geurteilt wurde. Die
    zweite Liste ist KEINE Beanstandung -- sie ist unser eigenes Problem und
    gehoert trotzdem gesagt, statt lautlos zu verschwinden. Die dritte sagt
    der aelteren Regel gegen den Plan, wo sie zurueckzutreten hat: sonst steht
    jedes verschobene Moebel zweimal in der Liste, einmal richtig und einmal
    mit dem schiefen Massstab gemessen.
    """
    if not job.get("beleg_verlangt"):
        return [], [], set()
    rohe = job.get("object_map") or []
    karten = rohe if isinstance(rohe, list) else [rohe]
    plan = {}
    for karte in karten:
        for m in karte.get("markers") or []:
            if m.get("px"):
                plan[m.get("name")] = m["px"]
    if not plan:
        return [], [], set()

    # Je Objekt: (Abstand, Bildname) fuer jedes Bild, das es gemeldet hat.
    gesehen = {}
    for bild in katalog.get("images") or katalog.get("entries") or []:
        name = bild.get("filename") or "(ohne Namen)"
        for eintrag in bild.get("marker_check") or []:
            if eintrag.get("status") != "sichtbar":
                continue
            px = plan.get(eintrag.get("name"))
            bei = eintrag.get("bei")
            if not px or not bei:
                continue
            try:
                abstand = math.hypot(float(bei[0]) - px[0], float(bei[1]) - px[1])
            except (TypeError, ValueError, IndexError):
                continue
            gesehen.setdefault(eintrag["name"], []).append((abstand, name))

    schlecht, unklar, beurteilt = [], [], set()
    for objekt, treffer in sorted(gesehen.items()):
        if len(treffer) < 2:
            continue                      # kein "bestes Bild" ohne zweites
        beurteilt.add(objekt)
        bestes = min(a for a, _ in treffer)
        if bestes > BELEG_RADIUS_PX:
            # Kein Bild an der Planstelle. Das ist unser Massstab -- gesagt
            # wird es trotzdem, und die Bilder werden UNTEREINANDER weiter
            # verglichen: ein Ausreisser bleibt einer, auch wenn das Lineal
            # schief ist.
            unklar.append(objekt)
        for abstand, bild in sorted(treffer, key=lambda t: t[1]):
            # ZWEI Bedingungen. Absolut weit weg reicht nicht -- sonst meldet
            # ein gleichmaessiger Versatz drei von vier Bildern, obwohl keines
            # umgeraeumt hat. Und relativ allein reicht auch nicht: wer 40
            # Pixel daneben liegt, waehrend ein anderes Bild auf 5 kommt, hat
            # nichts verschoben, sondern nur anders geschaetzt.
            if abstand <= BELEG_RADIUS_PX or abstand <= bestes + AUSREISSER_PX:
                continue
            schlecht.append(
                "%s: %s steht %d Pixel von seinem Platz -- in %s sitzt es "
                "richtig (%d Pixel). Dasselbe Haus, dieselbe Moeblierung, "
                "nur ein anderer Stil (Regelwerk 10.6)."
                % (bild, objekt, abstand,
                   min(treffer, key=lambda t: t[0])[1], bestes))
    return schlecht, unklar, beurteilt


NACHWEIS_MARKE = "NACHWEIS:"


def nachweis_beanstandungen(job, katalog):
    """Hat Codex die .blend nachweislich geoeffnet?

    Rainer, 2026-08-31: "hes guessing again", "the asshole is not reading the
    blender files". Codex hatte am 2026-08-30 selbst gesagt: "Bei meinen
    bisherigen Auftraegen in diesem Projekt habe ich keine .blend
    tatsaechlich geoeffnet." Der Auftrag verlangte es da schon.

    make-codex-job.py legt die Zahl der MESH-Objekte in codex-job.json unter
    `nachweis` ab und druckt sie NICHT in den Auftragstext -- die Objektliste
    dort nennt nur Moebel, nicht Waende, Boeden, Fenster und Dach. Wer die
    Summe richtig nennt, hat die Datei ausgelesen.

    Gesucht wird im GANZEN catalog.json, nicht in einem festen Feld: Codex
    hat den Rueckgabeschluessel am 2026-08-27 schon einmal anders benannt,
    und der Nachweis zaehlt, nicht das Feld.

    Auftraege ohne `nachweis` -- die zwoelf vom 28. bis 30. August -- gelten
    unveraendert. Eine Regel darf nicht rueckwirkend Lieferungen kippen, die
    unter der alten Fassung entstanden sind.
    """
    erwartet = ((job or {}).get("nachweis") or {}).get("mesh_objekte")
    if not erwartet:
        return []
    text = json.dumps(katalog or {}, ensure_ascii=False)
    genannt = None
    for stueck in text.split(NACHWEIS_MARKE)[1:]:
        zahlen = re.findall(r"\d+", stueck[:40])
        if zahlen:
            genannt = int(zahlen[0])
            if genannt == int(erwartet):
                return []
    if genannt is None:
        return ["Nachweis fehlt: catalog.json nennt keine Zeile \"%s <zahl> "
                "MESH-Objekte\". Ohne sie ist nicht belegt, dass die .blend "
                "geoeffnet wurde." % NACHWEIS_MARKE]
    return ["Nachweis falsch: %d MESH-Objekte genannt, die .blend hat %d. "
            "Die Zahl stammt nicht aus der Datei."
            % (genannt, int(erwartet))]


def pruefe(job, ordner):
    """Alle Beanstandungen gegen diesen Lieferordner. Leere Liste = in Ordnung."""
    beanstandungen = []
    contract_meta = job.get("contract") or {}
    contract_hash = contract_meta.get("contract_sha256")
    if contract_hash:
        baseline = os.path.join(DATA, "corrections", job.get("plan_id", ""),
                                "renders", "go-baseline")
        contract_path = os.path.join(baseline,
                                     contract_meta.get("effective_contract",
                                                       "effective-contract.json"))
        try:
            with open(contract_path, encoding="utf-8-sig") as datei:
                effective = json.load(datei)
        except (OSError, ValueError) as fehler:
            return ["effective-contract.json fehlt oder ist unlesbar: %s" % fehler]
        payload = dict(effective)
        recorded = payload.pop("contract_sha256", None)
        canonical = json.dumps(payload, ensure_ascii=False, sort_keys=True,
                               separators=(",", ":")).encode("utf-8")
        calculated = hashlib.sha256(canonical).hexdigest()
        if recorded != contract_hash or calculated != contract_hash:
            return ["effective-contract.json: contract_sha256 stimmt nicht"]
    katalog_pfad = os.path.join(ordner, "catalog.json")
    if not os.path.exists(katalog_pfad):
        return ["catalog.json fehlt in %s" % ordner]
    try:
        with open(katalog_pfad, encoding="utf-8") as datei:
            katalog = json.load(datei)
    except (OSError, ValueError) as fehler:
        return ["catalog.json ist nicht lesbar: %s" % fehler]

    soll = {eintrag["filename_hint"]: eintrag
            for eintrag in job.get("required_outputs", [])}
    # Eine Karte je Geschoss. `make-codex-job.py` legt seit dem 2026-08-28
    # eine je Innen-.blend an; aeltere Auftraege tragen ein einzelnes Objekt.
    rohe = job.get("object_map") or []
    karten = rohe if isinstance(rohe, list) else [rohe]
    # Codex nannte die Liste am 2026-08-27 einmal `images` und einmal
    # `entries`. Der Inhalt war beide Male richtig; sechs Beanstandungen wegen
    # eines Wortes helfen niemandem. Das Regelwerk legt `images` fest, hier
    # zaehlen beide.
    bilder = katalog.get("images") or katalog.get("entries") or []
    if not bilder:
        return ["catalog.json hat weder 'images' noch 'entries' mit Eintraegen"]
    # Der Zwischenstandsname ist kein Fehler -- er wird beim Annehmen hier
    # abgeschnitten, nicht bei Codex nachbestellt. Siehe _grundname().
    geliefert = {_grundname(bild.get("filename") or "") for bild in bilder}

    for name in sorted(set(soll) - geliefert):
        beanstandungen.append("%s: im catalog.json nicht aufgefuehrt" % name)

    quer, pruefe.ohne_treffer, quergeprueft = verschobene_objekte(job, katalog)

    for bild in bilder:
        geliefert_name = bild.get("filename") or "(ohne Namen)"
        name = _grundname(geliefert_name)
        eintrag = soll.get(name)
        if not eintrag:
            beanstandungen.append("%s: nicht gefordert" % geliefert_name)
            continue
        if contract_hash:
            if bild.get("contract_sha256") != contract_hash:
                beanstandungen.append(
                    "%s: fehlt oder falscher contract_sha256" % geliefert_name)
            if bild.get("state") != "approved":
                beanstandungen.append(
                    "%s: state muss approved sein" % geliefert_name)
        pfad = os.path.join(ordner, geliefert_name)
        if not os.path.exists(pfad):
            beanstandungen.append("%s: Datei fehlt" % name)
            continue
        ziel = eintrag.get("target_px")
        ist = png_groesse(pfad)
        if ziel and ist and list(ist) != list(ziel):
            beanstandungen.append(
                "%s: %d x %d statt %d x %d" % (name, ist[0], ist[1], ziel[0], ziel[1]))
        if bild.get("sha256") and sha256(pfad) != bild["sha256"]:
            beanstandungen.append(
                "%s: sha256 stimmt nicht mit catalog.json ueberein" % name)
        if eintrag.get("kind") == "interior":
            # Die Karte des Geschosses, aus dem dieses Bild stammt. Ohne diese
            # Wahl haelt der Pruefer OG-Marker gegen die EG-Karte und meldet
            # jeden davon als unbekannt.
            quelle = bild.get("source_blend")
            passend = next((k for k in karten
                            if _karte_deckt_bild(k.get("file"), quelle)), None)
            gedeckt = passend is not None
            gewaehlt = passend if passend else (karten[0] if karten else {})
            marker = {m["n"]: m for m in (gewaehlt.get("markers") or [])}
            beanstandungen += _marker_beanstandungen(
                name, bild.get("marker_check"), marker, gedeckt,
                gewaehlt.get("image") if passend else None,
                beleg_gilt(job, katalog), quergeprueft)

    beanstandungen += nachweis_beanstandungen(job, katalog)
    beanstandungen += abgeschriebene_marker(katalog)
    beanstandungen += quer

    # publish-renders.py laedt JEDE Bilddatei des Ordners hoch. Am 2026-08-26
    # standen so drei graue Blender-Kloetze im Kundenkatalog.
    # `-vorher-<zeit>` ist Archiv, keine Lieferung. Am 2026-08-28 fiel eine
    # regelkonforme Nachbesserung genau daran durch; sie wandert beim Annehmen
    # in einen Unterordner, statt hier beanstandet zu werden.
    erlaubt = set(soll) | {"catalog.json", VORHER_ORDNER}
    fremd = sorted(f for f in os.listdir(ordner)
                   if _grundname(f) not in erlaubt and not VORHER.search(f))
    if fremd:
        beanstandungen.append(
            "Zusatzdateien im Lieferordner, der Upload wuerde sie mitnehmen: %s"
            % ", ".join(fremd))
    return beanstandungen


def _auf_geforderte_namen(job, ordner):
    """Zwischenstandsnamen abschneiden -- Dateien und catalog.json.

    Umbenennen, nicht neu erzeugen: die Bytes und damit die sha256 bleiben,
    wie Codex sie geliefert hat. Genau das macht diesen Weg sicherer als eine
    zweite Runde -- was niemand neu rendert, kann nichts verlieren.
    """
    beiseite = [f for f in os.listdir(ordner) if VORHER.search(f)]
    if beiseite:
        archiv = os.path.join(ordner, VORHER_ORDNER)
        os.makedirs(archiv, exist_ok=True)
        for name in beiseite:
            os.replace(os.path.join(ordner, name), os.path.join(archiv, name))
    for grund, geliefert in zuordnung(job, ordner).items():
        if geliefert != grund:
            os.replace(os.path.join(ordner, geliefert), os.path.join(ordner, grund))
    katalog_pfad = os.path.join(ordner, "catalog.json")
    with open(katalog_pfad, encoding="utf-8") as datei:
        katalog = json.load(datei)
    schluessel = "images" if katalog.get("images") else "entries"
    for bild in katalog.get(schluessel) or []:
        if bild.get("filename"):
            bild["filename"] = _grundname(bild["filename"])
    katalog["state"] = "final"
    with open(katalog_pfad, "w", encoding="utf-8") as datei:
        json.dump(katalog, datei, ensure_ascii=False, indent=2)


RUNDEN = "RUNDEN.jsonl"


def notiere_runde(job, ordner, renders_ordner, beanstandungen, auge=None):
    """Eine Zeile je Pruefung. Die Zahl, an der spaeter entschieden wird.

    Rainer, 2026-08-29, ueber einen geschlossenen Kreis mit Codex: erst wenn
    wir "mehr oder weniger sicher sein koennen, dass nicht viele Fehler und
    Endlosschleifen auftreten". Das ist messbar statt Gefuehl -- wie oft geht
    eine Lieferung im ERSTEN Durchlauf durch. In den zwei Tagen davor: keine
    einzige von vier.

    `auge` haelt fest, was der Pruefer NICHT gefunden hat, sondern ein Mensch
    im Bild. Ohne diese Unterscheidung sieht die Statistik besser aus als die
    Lage: die Badewanne, der Schreibtisch und die Waschmaschinen sind alle am
    Pruefer vorbeigegangen.

    Eine Statistik darf nie eine Lieferung aufhalten -- deshalb schluckt diese
    Funktion ihre eigenen Fehler.
    """
    zeile = {
        "plan_id": job.get("plan_id"),
        "job_id": job.get("job_id"),
        "contract_sha256": (job.get("contract") or {}).get("contract_sha256"),
        "ordner": os.path.basename(os.path.normpath(ordner)),
        "geprueft_am": datetime.datetime.now().isoformat(timespec="seconds"),
        "beanstandungen": len(beanstandungen),
        "was": list(beanstandungen),
    }
    if auge:
        zeile["auge"] = auge
    try:
        with open(os.path.join(renders_ordner, RUNDEN), "a", encoding="utf-8") as datei:
            datei.write(json.dumps(zeile, ensure_ascii=False) + chr(10))
    except OSError:
        pass


def annehmen(job, ordner, renders_ordner):
    """Den Ordner als DEN angenommenen festhalten. Nur ohne Beanstandung."""
    beanstandungen = pruefe(job, ordner)
    if beanstandungen:
        # Erst pruefen, dann anfassen. Sonst stuenden nach einer abgelehnten
        # Lieferung halb umbenannte Dateien im Ordner.
        raise Beanstandet(beanstandungen)
    _auf_geforderte_namen(job, ordner)
    dateien = []
    for eintrag in job.get("required_outputs", []):
        name = eintrag["filename_hint"]
        pfad = os.path.join(ordner, name)
        dateien.append({"name": name, "sha256": sha256(pfad),
                        "px": png_groesse(pfad)})
    zeiger = {
        "schema": "zf-angenommen-v1",
        "plan_id": job.get("plan_id"),
        "job_id": job.get("job_id"),
        "ordner": os.path.basename(os.path.normpath(ordner)),
        "angenommen_am": datetime.datetime.now().isoformat(timespec="seconds"),
        "dateien": dateien,
    }
    ziel = os.path.join(renders_ordner, ZEIGER)
    with open(ziel, "w", encoding="utf-8") as datei:
        json.dump(zeiger, datei, ensure_ascii=False, indent=2)
    return ziel


def _flachanteil(bild, px, radius=55):
    """Anteil der Pixel um `px`, die sich von ihrer Umgebung nicht abheben.

    Ein glatter Quader liegt hoch, ein eingerichtetes Moebel niedrig.
    """
    from PIL import ImageFilter
    x, y = px
    fenster = bild.crop((max(0, x - radius), max(0, y - radius),
                         min(bild.width, x + radius), min(bild.height, y + radius)))
    weich = fenster.filter(ImageFilter.GaussianBlur(2))
    # get_flattened_data() gibt es erst in neueren Pillow-Fassungen.
    hole = getattr(fenster, "get_flattened_data", None) or fenster.getdata
    hole_weich = getattr(weich, "get_flattened_data", None) or weich.getdata
    scharf = list(hole())
    unscharf = list(hole_weich())
    if not scharf:
        return 0.0
    flach = sum(1 for a, b in zip(scharf, unscharf) if abs(a - b) <= 1)
    return 100.0 * flach / len(scharf)


def messe_platzhalter(job, ordner):
    """{name: (farbe, flach_baseline, flach_lieferung)} fuer das erste Innenbild.

    Fehlt Pillow, die Objektkarte oder der Baseline-Render, kommt {} zurueck --
    dann gibt es eben keine Warnung. Ein Pruefer, der an einer Zusatzbibliothek
    scheitert, blockiert die ganze Lieferkette.
    """
    # Dieselbe Kartenliste wie in pruefe(). Rainer, 2026-08-29: die erste
    # Lieferung nach der Umstellung stuerzte hier ab -- `pruefe()` war auf die
    # Liste umgestellt, diese Funktion nicht.
    rohe = job.get("object_map") or []
    karten = rohe if isinstance(rohe, list) else [rohe]
    if not karten:
        return {}
    try:
        from PIL import Image
    except ImportError:
        return {}
    # Gemessen wird an ALLEN Innenbildern dieser Karte.
    #
    # Bis zum 2026-09-01 stand hier nur das erste, mit der Begruendung "ein
    # Platzhalter, der in einem Stil ein Kasten blieb, ist es in allen
    # vieren". An german_catalog_review_bungalow_3_3_4_b_100_2 widerlegt:
    # stuff-9 blieb in 03-warm-modern und 06-classic ein glatter Kasten, in
    # 04-dark-modern und 05-soft-scandinavian war eine Kuechenzeile mit
    # Fronten und Griffen daraus geworden. Die Warnung kam nur, weil 03
    # zufaellig das erste Bild ist.
    karte = karten[0]
    marker = karte.get("markers") or []
    if not marker:
        return {}
    quelle = karte.get("file", "")
    basis_name = quelle.replace("OBJEKTKARTE-", "").replace(".png", "") + ".png"
    basis_pfad = os.path.join(os.path.dirname(os.path.normpath(ordner)),
                              "go-baseline", basis_name)
    innen = [eintrag["filename_hint"] for eintrag in job.get("required_outputs", [])
             if eintrag.get("kind") == "interior"]
    zuordnung_ = zuordnung(job, ordner)
    bild_namen = [zuordnung_[n] for n in innen if n in zuordnung_]
    if not os.path.exists(basis_pfad) or not bild_namen:
        return {}
    try:
        basis = Image.open(basis_pfad).convert("L")
    except OSError:
        return {}
    lieferungen = []
    for name in bild_namen:
        try:
            bild = Image.open(os.path.join(ordner, name)).convert("L")
        except OSError:
            continue
        # Ohne gleiche Masze zeigt derselbe Pixel nicht dieselbe Stelle.
        if bild.size == basis.size:
            lieferungen.append(bild)
    if not lieferungen:
        return {}
    gemessen = {}
    for eintrag in marker:
        if not eintrag.get("px"):
            continue
        gemessen[eintrag["name"]] = (
            eintrag.get("farbe"),
            _flachanteil(basis, eintrag["px"]),
            [_flachanteil(bild, eintrag["px"]) for bild in lieferungen])
    return gemessen


def lade_job(plan):
    pfad = os.path.join(DATA, "corrections", plan, "renders", "go-baseline",
                        "codex-job.json")
    with open(pfad, encoding="utf-8") as datei:
        return json.load(datei)


def main():
    zerleger = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    zerleger.add_argument("plan")
    zerleger.add_argument("ordner", help="Lieferordner, absolut oder unter renders/")
    zerleger.add_argument("--annehmen", action="store_true",
                          help="bei null Beanstandungen ANGENOMMEN.json schreiben")
    zerleger.add_argument("--auge", metavar="SATZ",
                          help="was ein Mensch im Bild fand, das der Pruefer "
                               "nicht sieht -- kommt in RUNDEN.jsonl")
    argumente = zerleger.parse_args()

    renders = os.path.join(DATA, "corrections", argumente.plan, "renders")
    ordner = (argumente.ordner if os.path.isabs(argumente.ordner)
              else os.path.join(renders, argumente.ordner))
    if not os.path.isdir(ordner):
        sys.exit("Lieferordner nicht gefunden: %s" % ordner)

    job = lade_job(argumente.plan)
    pruefe.ohne_treffer = []
    beanstandungen = pruefe(job, ordner)
    notiere_runde(job, ordner, renders, beanstandungen, argumente.auge)
    # Objekte, die KEIN Bild an der Planstelle zeigt. Das ist unser Massstab
    # und keine Beanstandung -- aber lautlos verschwinden darf es nicht,
    # sonst haelt man die Stille fuer ein Ergebnis.
    if pruefe.ohne_treffer:
        print("Nicht beurteilt, weil KEIN Bild diese Objekte an ihrer "
              "Planstelle zeigt --")
        print("die px im Auftrag ist der Objektursprung, nicht die sichtbare "
              "Mitte:")
        for name in pruefe.ohne_treffer:
            print("  ~ " + name)
        print("")
    if beanstandungen:
        print("%d Beanstandung(en):" % len(beanstandungen))
        for satz in beanstandungen:
            print("  - " + satz)
        sys.exit(1)

    print("Lieferung ist formal in Ordnung: %s" % os.path.basename(ordner))

    verdacht = kasten_verdacht(messe_platzhalter(job, ordner))
    if verdacht:
        print("")
        print("Sieht noch nach Platzhalter-Kasten aus -- bitte ansehen:")
        for name in verdacht:
            print("  ? " + name)
        print("  (Warnung, keine Beanstandung -- der Blick eines Menschen")
        print("   entscheidet.)")
        print("")

    print("Nicht geprueft: ob jedes Objekt WIRKLICH im Bild ist. Das bleibt "
          "der Blick eines Menschen.")
    if argumente.annehmen:
        ziel = annehmen(job, ordner, renders)
        print("angenommen -> %s" % ziel)


if __name__ == "__main__":
    main()
