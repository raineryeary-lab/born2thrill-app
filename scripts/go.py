#!/usr/bin/env python3
"""EIN Befehl. Er treibt ein Haus so weit wie es ohne dich geht.

    python go.py bungalow_039
    python go.py --alle
    python go.py --alle --hochladen        auch in den Katalog schieben

Er laeuft die Kette selbst ab und hoert erst auf, wenn er wirklich dich braucht:

    Massstab   -> rechnet ihn aus der Katalog-Seitengeometrie, wenn moeglich
    Dachform   -> setzt sie, wenn keine da ist
    Bauen      -> ruft run_project fuer beide Stile
    Pruefen    -> Verifier laeuft im Bau mit
    Zertifikat -> schreibt run_project, wenn alles sauber ist
    Hochladen  -> nur mit --hochladen
    Freigeben  -> NIE automatisch, das ist deine Entscheidung

Am Ende sagt er pro Haus genau einen Satz: fertig, oder was fehlt und mit
welchem Befehl du es loest. Kein Suchen in Logs.
"""

import argparse
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)
# Eine Wahrheit fuer Dachform und Massstab (siehe scripts/hausdaten.py).
import hausdaten  # noqa: E402
import dachboden  # noqa: E402
import os_sperre  # noqa: E402  -- ein Lauf je Haus (ZUVERLAESSIGKEIT-001 Runde 4)

SUITE = os.path.dirname(os.path.dirname(HERE))
PROJECTS = os.path.join(SUITE, "floorplan-simplifier", "projects")
# Nicht raten. 2026-08-21: der Datenordner zog von C: nach E:; ein Skript,
# das ohne gesetzte Variable still auf den alten C:-Nachbarordner
# zurueckfiele, wuerde unbemerkt gegen veraltete Daten arbeiten -- exakt
# der root-merge-Fehler vom 18.08., nur seitenverkehrt. Gleiches Muster wie
# build-simplifier-render-plan.py.workbench_data_root().
_konfiguriert = os.environ.get("FLOORPLAN_WORKBENCH_DATA_DIR", "").strip()
if not _konfiguriert:
    sys.exit("FLOORPLAN_WORKBENCH_DATA_DIR ist nicht gesetzt -- verweigere, "
            "den Datenordner zu erraten. Siehe .env.local.")
DATA = os.path.abspath(_konfiguriert)
PY = sys.executable


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8-sig") as handle:
            return json.load(handle)
    except Exception:
        return default


def run(cmd, quiet=True, log=None, timeout=None):
    """Einen Schritt ausfuehren; mit `log` bleibt seine Ausgabe erhalten.

    Rainer, 2026-08-28: "Bau fehlgeschlagen -- Log in renders/go-baseline/",
    und in keinem dieser Logs stand der Grund. Er stand in der Ausgabe von
    run_project.py, die hier verworfen wurde -- die FAIL-Zeilen des Verifiers
    mussten von Hand nachgestellt werden. Wer auf ein Log verweist, schreibt
    es auch.

    `timeout` (Sekunden): ein haengender Schritt endet mit Code 124 und einer
    Zeile "Zeitlimit" im Log, statt die Hausakte ewig auf "laeuft" zu lassen
    (ZUVERLAESSIGKEIT-001 B5).
    """
    fassen = quiet or log is not None
    try:
        result = subprocess.run(cmd, capture_output=fassen, text=True,
                                errors="replace", cwd=HERE, timeout=timeout)
    except subprocess.TimeoutExpired as abbruch:
        def _text(teil):
            if isinstance(teil, bytes):
                return teil.decode("utf-8", "replace")
            return teil or ""
        result = subprocess.CompletedProcess(
            cmd, 124, _text(abbruch.stdout),
            _text(abbruch.stderr) + "\nZeitlimit von %d s ueberschritten -- abgebrochen.\n" % timeout)
    if log is not None:
        ausgabe = (result.stdout or "") + (result.stderr or "")
        try:
            os.makedirs(os.path.dirname(log), exist_ok=True)
            with open(log, "w", encoding="utf-8", errors="replace") as handle:
                handle.write(ausgabe)
        except OSError:
            pass
        if not quiet:
            print(ausgabe, end="")
    return result.returncode


HOCHLADEN_ZEITLIMIT = 25 * 60   # nur publish-renders.py, nicht der Bau davor
HOCHLADEN_FEHLER = []           # (haus, letzte Zeilen von publish-renders.py)


def log_ende(pfad, zeilen=20):
    """Die letzten Zeilen eines Logs -- dort steht bei einem Abbruch der Grund."""
    try:
        with open(pfad, encoding="utf-8", errors="replace") as handle:
            text = handle.read().splitlines()
    except OSError:
        return ["(kein Log: %s)" % pfad]
    text = [z for z in text if z.strip()]
    return text[-zeilen:] or ["(Log leer)"]


def fails_aus_log(pfad):
    """Die FAIL-Zeilen samt ihrer Begruendung aus einem Bau-Log.

    Nicht nur der Regelname: "R9_stair_access" allein sagt nicht, WAS im Weg
    stand. Die eingerueckten Zeilen darunter tragen die Messung, und genau die
    beantwortet die Frage.
    """
    if not os.path.exists(pfad):
        return []
    treffer = []
    with open(pfad, encoding="utf-8", errors="replace") as handle:
        zeilen = handle.read().splitlines()
    for i, zeile in enumerate(zeilen):
        if not zeile.startswith("FAIL "):
            continue
        regel = zeile.split()[1] if len(zeile.split()) > 1 else zeile[5:]
        gruende = []
        for weiter in zeilen[i + 1:]:
            if not weiter.startswith("  - "):
                break
            gruende.append(weiter[4:].strip())
        treffer.append((regel, gruende))
    # Dieselbe Regel faellt in mehreren Ausfuehrungen -- einmal nennen genuegt.
    gesehen, eindeutig = set(), []
    for regel, gruende in treffer:
        if regel in gesehen:
            continue
        gesehen.add(regel)
        eindeutig.append((regel, gruende))
    return eindeutig


def abbruchgrund(pfad):
    """Die erste echte Fehlermeldung aus einem Bau-Log, oder None.

    Rainer, 2026-08-29: `3_3_1_b_100_2` meldete nur "Bau fehlgeschlagen --
    Log in renders/go-baseline/bau.log". Der Grund stand vollstaendig im Log:
    die Raeume des Geschosses waren umgezeichnet worden, seit die Moebel
    gesetzt wurden, und der Plan-Builder verweigert deshalb.

    `fails_aus_log()` findet das nicht -- es sucht die "FAIL "-Zeilen des
    Verifiers, und das hier ist ein Abbruch DAVOR. Dieselbe Lehre wie bei
    `run(log=...)` eine Ebene hoeher: wer auf ein Log verweist, schreibt es
    auch. Und wer den Grund hat, sagt ihn auch.

    Alles mit `[go] ` davor ist unsere eigene Fortschrittsausgabe und
    erklaert nichts.
    """
    if not os.path.exists(pfad):
        return None
    with open(pfad, encoding="utf-8", errors="replace") as handle:
        for zeile in handle:
            text = zeile.strip()
            if not text or text.startswith("[go] "):
                continue
            # Info-Zeilen des Plan-Builders erklaeren auch nichts -- ausser
            # sie melden selbst einen Fehler (Rainer, 2026-10-24,
            # twostorey_053: "registered onto groundfloor ..." stand als
            # Grund in der Hausliste, der echte zwei Zeilen tiefer).
            # Die Startzeile von Blender ("Blender 5.0.0 (hash ...)") ist auch
            # kein Grund (other_vito, 2026-10-24).
            if text.startswith("Blender ") and "(hash " in text:
                continue
            if text.startswith(("[plan] ", "[dollhouse] ", "[exterior] ")) and not any(
                    w in text for w in ("REFUSED", "FEHL", "Fehler", "Error", "WARNUNG", "verweiger")):
                continue
            text = ohne_pfad(text)
            # Die Hausliste ist eine Zeile, kein Absatz.
            return text[:197] + "..." if len(text) > 200 else text
    return None


def ohne_pfad(text):
    r"""Den Datenordner vorn abschneiden.

    "E:\born2thrill-local-workbench-data\corrections\german_catalog_review_
    bungalow_3_3_1_b_100_2\furniture\floor-0.json: ..." frisst 130 Zeichen,
    bevor die Meldung anfaengt -- der Handgriff am Ende ("einmal speichern")
    fiele der Kuerzung zum Opfer. Der Dateiname genuegt: WELCHES Haus steht
    ohnehin in der Zeile davor.

    Der Docstring ist ein r-String: ohne das liest Python `\c` und `\b` im
    Beispielpfad als Escape-Sequenzen und warnt bei jedem Lauf.
    """
    kopf, doppelpunkt, rest = text.partition(": ")
    if not doppelpunkt or os.sep not in kopf:
        return text
    return os.path.basename(kopf) + ": " + rest


def hat_massstab(name):
    return hausdaten.hat_massstab(os.path.join(PROJECTS, name))


def hat_dach(name):
    """Beide Stile zaehlen.

    Frueher sah diese Pruefung im Sidecar NUR nach roof_type_classic: ein Haus
    mit ausschliesslich moderner Dachform galt als dachlos. hausdaten.py
    fuehrt beide Dateien nach derselben Regel zusammen wie der Bau.
    """
    return hausdaten.hat_dach(os.path.join(PROJECTS, name))


def zertifikat(name):
    return read_json(os.path.join(DATA, "corrections", name, "renders",
                                  "go-baseline", "delivery-manifest.json"))


_batch_build = None


def _lade_batch_build():
    global _batch_build
    if _batch_build is None:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "batch_build", os.path.join(HERE, "batch-build.py"))
        modul = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(modul)
        _batch_build = modul
    return _batch_build


def ist_aktuell(name):
    """True nur, wenn das vorhandene Zertifikat wirklich noch zur heutigen
    Zeichnung, zum Moebelstand UND zur aktuellen Renderer-Toolchain passt --
    nicht bloss, ob eine Datei existiert.

    zertifikat() allein pruefte nur "gibt es ein delivery-manifest.json" --
    einmal gebaut, hielt jede spaetere Zeichnungs-Aenderung "Bauen" fuer
    erledigt und uebersprang run_project.py stillschweigend. Rainer,
    2026-08-22: "i just saved it and codex says the last save is an hour
    ago and you say the last save was 6 hours ago ... we need a good and
    secure save and a new build when 'Bauen' is clicked" -- die Speicherung
    war echt, nur hat sie nie zu einem neuen Bau gefuehrt.

    Dieselbe Pruefung existiert schon, bewaehrt, in batch-build.py
    (annotation_state/built_hash) -- hier importiert statt ein zweites Mal
    geschrieben, damit die beiden nie auseinanderlaufen.
    """
    modul = _lade_batch_build()
    # Unlesbares Zertifikat oder unlesbare Zeichnung (Runde 4, R1): nicht
    # aktuell -- der Bau laeuft dann und meldet selbst, woran er scheitert.
    try:
        aktuell, grund = modul.annotation_state(name)
        if grund or not aktuell:
            return False
        return modul.built_hash(name) == aktuell
    except (OSError, ValueError):
        return False


def bau_log(name):
    return os.path.join(DATA, "corrections", name, "renders", "go-baseline",
                        "bau.log")


def verifier_fails(name):
    """Was der letzte Bau DIESES Laufs beanstandet hat.

    Frueher stand hier `batch-build.log` -- eine Datei, die go.py nie
    schreibt. Sie stammte vom letzten Lauf ueber batch-build.py und war am
    2026-08-28 sechs Tage alt: der Grund fehlte, und im schlechteren Fall
    haette sie einen laengst behobenen Fehler gemeldet.
    """
    fails = fails_aus_log(bau_log(name))
    if fails:
        return fails
    return fails_aus_log(os.path.join(DATA, "corrections", name, "renders",
                                      "go-baseline", "batch-build.log"))


def storeys(name):
    a = read_json(os.path.join(PROJECTS, name, "annotations.json")) or {}
    lv = {x.get("floor_level") for x in (a.get("annotations") or []) if x.get("floor_level")}
    # Ein Dachboden (Ausbaureserve) ist kein Geschoss (dachboden-ausbaureserve-v1).
    import dachboden
    # Ein Dachgeschoss MIT Wohnraeumen zaehlt (DG-MIT-KNIESTOCK-001).
    return max(1, len(dachboden.geschoss_ebenen(lv, a.get("annotations") or [])))


def bilderordner(name):
    """Der Ordner mit den AKTUELLSTEN Bildern dieses Hauses.

    Unter renders/ liegen mehrere: `go-baseline` mit den Rohbildern aus dem
    Bau, und die Rueckgaben von Codex (`codex-correction-...`,
    `codex-final-...`) mit den fertigen. Hochgeladen wurde bisher immer
    go-baseline -- also die weissen Kaesten, waehrend die guten Bilder
    danebenlagen. Rainer hat die Baselines geloescht, auf Hochladen gedrueckt,
    und sie waren wieder da (2026-08-20).

    Genommen wird der Ordner mit dem juengsten Bild. Technische Paesse
    (-depth/-edge/-mask) zaehlen nicht mit, die gehoeren nicht in den Katalog.
    """
    wurzel = os.path.join(DATA, "corrections", name, "renders")
    if not os.path.isdir(wurzel):
        return None
    # go-baseline ist der ROHBAU-Nachweis, nie die Lieferung. "Juengstes Bild
    # gewinnt" allein reicht nicht: jeder neue Bau schreibt die Baselines neu
    # und macht sie damit juenger als jede Codex-Rueckgabe. Genau so landeten
    # am 2026-08-23 zwei graue Rohbau-Bilder im Katalog, obwohl die fertigen
    # danebenlagen. Gibt es Codex-Rueckgaben, wird NUR unter denen gewaehlt.
    codex = [e for e in sorted(os.listdir(wurzel))
             if e.startswith("codex-") and os.path.isdir(os.path.join(wurzel, e))]
    # KEIN Rueckfall auf go-baseline. Gibt es keine Codex-Lieferung, gibt es
    # keine Bilder -- und dann wird nicht hochgeladen.
    #
    # Der Docstring oben sagt es seit jeher ("go-baseline ist der
    # ROHBAU-Nachweis, nie die Lieferung"), aber `codex or
    # sorted(os.listdir(wurzel))` nahm ihn genau dann doch, wenn Codex noch
    # nichts geliefert hatte. Rainer, 2026-09-01, an
    # german_catalog_review_bungalow_3_4_5_b_120: "es heisst ich muss die
    # bilder freigeben das sind aber keine Bilder." Drei graue Rohbauten
    # standen zum Hochladen bereit.
    kandidaten = codex
    bester, jung = None, -1
    for eintrag in kandidaten:
        ordner = os.path.join(wurzel, eintrag)
        if not os.path.isdir(ordner):
            continue
        bilder = [x for x in os.listdir(ordner)
                  if x.lower().endswith(".png")
                  and not any(x.lower().endswith(s + ".png")
                              for s in ("-depth", "-edge", "-mask"))]
        if not bilder:
            continue
        # Auch die Zeit des ORDNERS zaehlt: beim Einlesen behalten kopierte
        # Dateien ihre alten Zeitstempel, also war eine frisch eingelesene
        # Lieferung nach Dateizeit "aelter" als eine vorherige -- und es wurde
        # wieder die alte hochgeladen (2026-08-23, zweimal hintereinander).
        neuestes = max([os.path.getmtime(ordner)]
                       + [os.path.getmtime(os.path.join(ordner, b)) for b in bilder])
        if neuestes > jung:
            bester, jung = ordner, neuestes
    return bester


def _pruefer(job, ordner):
    """Die volle Pruefung aus lieferung-pruefen.py (Masse, sha, Marker, Zusatzdateien)."""
    import importlib.util
    spec = importlib.util.spec_from_file_location(
        "lieferung_pruefen", os.path.join(HERE, "lieferung-pruefen.py"))
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    modul.pruefe.ohne_treffer = []
    return modul.pruefe(job, ordner)


def online_namen(plan, site=None):
    """Die Bildnamen, die WordPress fuer diesen Plan schon hat -- oder None.

    Dieselbe oeffentliche Route wie publish-renders.py existing_slugs(), ohne
    Zugangsdaten. None heisst: nicht erreichbar, also weiter wie bisher.
    Plan hochladen-schon-online-v1.
    """
    import urllib.parse
    import urllib.request
    site = site or os.environ.get("B2T_SITE", "https://born2thrill.de")
    url = "%s/wp-json/b2t/v1/bilder?plan=%s" % (site, urllib.parse.quote(plan))
    try:
        with urllib.request.urlopen(url, timeout=20) as antwort:
            return {b.get("name") for b in json.loads(antwort.read().decode("utf-8")) if b.get("name")}
    except Exception:
        return None


def lieferung_fehlt(job, ordner):
    """Was an der Codex-Lieferung noch fehlt. Leere Liste = hochladen.

    Erst das Zaehlbare in einem Satz ("6 von 9 Bildern fehlen: 03, 04 ..."),
    dann die volle Pruefung. Plan codex-ein-ordner-ein-knopf-v1.
    """
    soll = [r.get("filename_hint") for r in job.get("required_outputs") or []
            if r.get("filename_hint")]
    da = set(os.listdir(ordner)) if os.path.isdir(ordner) else set()
    fehlend = [n for n in soll if n not in da]
    saetze = []
    if fehlend and len(fehlend) == len(soll):
        saetze.append("alle %d Bilder fehlen noch" % len(soll))
    elif fehlend:
        saetze.append("%d von %d Bildern fehlen: %s"
                      % (len(fehlend), len(soll),
                         ", ".join(n.split("-")[0] for n in fehlend)))
    if "catalog.json" not in da:
        saetze.append("catalog.json fehlt")
    if saetze:
        return saetze
    return _pruefer(job, ordner)


def treibe(name, hochladen=False, laut=False, trotz_treppe=False):
    """Push one house as far as it goes. Returns (fertig, satz)."""
    a = read_json(os.path.join(PROJECTS, name, "annotations.json"))
    if not a or not (a.get("annotations") or []):
        return False, "nicht annotiert -- im Annotator die Raeume zeichnen"

    # --- Massstab -------------------------------------------------------
    if not hat_massstab(name):
        run([PY, os.path.join(HERE, "gebaeudemass.py"), "--aus-katalog"])
        if not hat_massstab(name):
            folder = os.path.join(PROJECTS, name)
            bild = any(x.lower().endswith((".png", ".jpg", ".jpeg", ".pdf"))
                       and "room_concept" not in x.lower()
                       for x in os.listdir(folder))
            if bild:
                return False, "Massstab fehlt -- im Annotator das Gebaeudemass ziehen"
            return False, ("Massstab fehlt -- python gebaeudemass.py %s "
                           "--breite B --tiefe T" % name)

    # --- Geschoss-Ausrichtung (HARTE REGEL, Rainer 2026-08-23) ------------
    # Ein Obergeschoss ohne Ausrichtungsmarken stapelt sich um Hunderte
    # Millimeter versetzt aufs Erdgeschoss (029: 463mm). Ohne Marken auf
    # BEIDEN Geschossen geht es nicht weiter -- der Plan-Builder verweigert
    # ohnehin; hier kommt die Erklaerung in die Hausliste statt eines
    # nackten "Bau fehlgeschlagen".
    levels = dachboden.geschoss_reihenfolge({r.get("floor_level") for r in a.get("annotations", [])
                     if r.get("floor_level")})
    if len(levels) > 1:
        ground = "groundfloor" if "groundfloor" in levels else levels[0]
        marken = a.get("floor_alignment") or {}
        fehlend = [lv for lv in levels
                   if len(marken.get(lv) or []) != 2 or len(marken.get(ground) or []) != 2]
        if fehlend:
            return False, ("Ausrichtung fehlt -- im Annotator auf %s und %s die zwei "
                           "diagonalen Aussenecken markieren (Floor alignment)"
                           % (ground, ", ".join(lv for lv in fehlend if lv != ground) or "Obergeschoss"))

    # --- Dachform -------------------------------------------------------
    if not hat_dach(name):
        run([PY, os.path.join(HERE, "dachform.py"), name])

    # --- Bauen ----------------------------------------------------------
    if not ist_aktuell(name):
        # Treppe zugesperrt? Vor dem Bauen fragen, nicht hinterher im Bild
        # finden (Rainer, 2026-10-17, twostorey_058: Wand quer vor dem
        # Antritt). Mit --trotz-treppe wird trotzdem gebaut.
        if not trotz_treppe:
            import treppe_zugang
            befunde = treppe_zugang.pruefe_haus(name) or []
            if befunde:
                return False, (treppe_zugang.stair_access_message(befunde[0])
                               + " -- oder mit --trotz-treppe bauen")
        floors = ",".join(str(i) for i in range(storeys(name)))
        code = run([PY, os.path.join(HERE, "run_project.py"), name,
                    "--styles", "modern,classic", "--floors", floors],
                   quiet=not laut, log=bau_log(name))
        if code == 2:
            return False, "wird gerade von einem anderen Lauf gebaut"
        if not zertifikat(name):
            fails = verifier_fails(name)
            if fails:
                regel, gruende = fails[0]
                weitere = (" (+%d weitere Regel(n))" % (len(fails) - 1)
                           if len(fails) > 1 else "")
                grund = (": " + gruende[0]) if gruende else ""
                return False, "Verifier %s%s%s" % (regel, grund, weitere)
            grund = abbruchgrund(bau_log(name))
            if grund:
                return False, grund
            return False, ("Bau fehlgeschlagen -- Log in renders/go-baseline/bau.log")

    # --- Hochladen ------------------------------------------------------
    if hochladen:
        # Kein zweiter Rueckfall auf go-baseline. Gibt es keine
        # Codex-Lieferung, wird nichts hochgeladen -- die Rohbauten sind
        # keine Bilder eines Hauses (Rainer, 2026-09-01: "das sind aber
        # keine Bilder").
        # Der Ordner steht im Auftrag (codex-job.json). Gibt es ihn dort,
        # gilt NUR er, und nur vollstaendig (codex-ein-ordner-ein-knopf-v1).
        # Alte Auftraege ohne delivery_folder: wie bisher bilderordner().
        job = read_json(os.path.join(DATA, "corrections", name, "renders",
                                     "go-baseline", "codex-job.json")) or {}
        ordner = job.get("delivery_folder")
        if ordner:
            # Erst nachsehen, was schon online ist (hochladen-schon-online-v1,
            # Rainer 2026-10-22, vm2: "why cant i upload it?" -- Codex hatte
            # alle 10 laengst selbst hochgeladen).
            soll = [os.path.splitext(r["filename_hint"])[0]
                    for r in job.get("required_outputs") or [] if r.get("filename_hint")]
            online = online_namen(name)
            schon = [n for n in soll if online is not None and n in online]
            if soll and len(schon) == len(soll):
                return True, "schon online (%d/%d)" % (len(schon), len(soll))
            vorab = ("%d/%d schon online; " % (len(schon), len(soll))) if schon else ""
            fehlt = lieferung_fehlt(job, ordner)
            if fehlt:
                weitere = (" (+%d weitere)" % (len(fehlt) - 1)
                           if len(fehlt) > 2 else "")
                return False, (vorab + "nicht hochgeladen -- Codex-Lieferung unvollstaendig: "
                               + "; ".join(fehlt[:2]) + weitere)
        else:
            ordner = bilderordner(name)
        if not ordner:
            return False, ("noch keine Codex-Lieferung -- nur der Rohbau ist "
                           "da, und der geht nicht in den Katalog")
        # Die Ausgabe von publish-renders.py bleibt im Log, und ihr Ende geht
        # mit nach oben: vorher war hier nur "Hochladen fehlgeschlagen" zu
        # lesen, der eigentliche Grund (z. B. HTTP 400 vom Katalog) war weg
        # (ZUVERLAESSIGKEIT-001 B2).
        log = os.path.join(DATA, "corrections", name, "renders", "hochladen.log")
        code = run([PY, os.path.join(HERE, "publish-renders.py"),
                    "--plan", name, "--dir", ordner], quiet=not laut,
                   log=log, timeout=HOCHLADEN_ZEITLIMIT)
        if code != 0:
            HOCHLADEN_FEHLER.append((name, log_ende(log)))
            return False, "gebaut und zertifiziert, Hochladen fehlgeschlagen"
        # Freigeben hat ZWEI Haelften. `approve-plan.py` schreibt die Rechte
        # ins lokale Ledger, `freigeben.py` schaltet die Bilder im
        # WordPress-Katalog scharf. Wer nur die erste laeuft, hat einen
        # freigegebenen Plan mit leerer Karte -- genau das stand bei
        # bungalow_001 am 2026-08-30: 9 Bilder hochgeladen, im=0.
        # Der Knopf in der Hausakte macht beides; die Kommandozeile sagte
        # bis hierher nur die Haelfte.
        return False, ("hochgeladen -- jetzt freigeben, BEIDE Schritte:"
                       "\n      python approve-plan.py %s --reason \"...\""
                       "\n      python freigeben.py %s" % (name, name))

    return True, "gebaut und zertifiziert -- mit --hochladen in den Katalog"


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("haeuser", nargs="*")
    parser.add_argument("--alle", action="store_true")
    parser.add_argument("--hochladen", action="store_true")
    parser.add_argument("--laut", action="store_true", help="Ausgaben der Teilschritte zeigen")
    parser.add_argument("--trotz-treppe", action="store_true",
                        help="bauen, auch wenn eine Wand die Treppe zusperrt")
    args = parser.parse_args()

    namen = args.haeuser
    if args.alle:
        namen = sorted(n for n in os.listdir(PROJECTS)
                       if os.path.exists(os.path.join(PROJECTS, n, "annotations.json")))
    if not namen:
        sys.exit("Welches Haus? Oder --alle")

    fertig, offen, besetzt = [], [], []
    for i, name in enumerate(namen, 1):
        print("[%d/%d] %-46s " % (i, len(namen), name[:46]), end="", flush=True)
        # Ein Bauen/Hochladen je Haus zur selben Zeit. Die Sperre haelt DIESER
        # Prozess fuer den ganzen Lauf des Hauses (Bau + Hochladen), als
        # Betriebssystem-Sperre: ein Neustart des Next-Servers gibt sie nicht
        # frei, solange go.py laeuft (Codex Runde 4, N1/N2). Kindprozesse erben
        # das Handle nicht (os_sperre.py) -- keine Selbstblockade.
        sperr_ordner = os.path.join(DATA, "corrections", name)
        os.makedirs(sperr_ordner, exist_ok=True)
        sperr_pfad = os.path.join(sperr_ordner, "pipeline.lock")
        sperre = os_sperre.nehmen(sperr_pfad)
        if sperre is None:
            print("LAEUFT SCHON: %s%s -- nicht noch einmal klicken, warten bis er fertig ist"
                  % (name, os_sperre.besitzer_text(sperr_pfad)))
            besetzt.append(name)
            continue
        try:
            ok, satz = treibe(name, hochladen=args.hochladen, laut=args.laut,
                              trotz_treppe=args.trotz_treppe)
        finally:
            os_sperre.freigeben(sperre)
        # "schon online (10/10)" ist auch fertig, soll aber so dastehen
        # (hochladen-schon-online-v1).
        zeile = satz if (not ok or satz.startswith("schon online")) else "fertig"
        print(zeile[:96] if ok or not satz.startswith("Treppe") else satz)
        (fertig if ok else offen).append((name, satz))

    print("")
    print("%d fertig, %d brauchen dich" % (len(fertig), len(offen)))
    if offen:
        gruppen = {}
        for name, satz in offen:
            schluessel = satz.split("--")[0].strip()
            gruppen.setdefault(schluessel, []).append(name)
        print("")
        for schluessel, liste in sorted(gruppen.items(), key=lambda x: -len(x[1])):
            print("  %4d  %s" % (len(liste), schluessel))
    # Ein gescheitertes Hochladen ist ein Fehler, kein "braucht dich": Exit
    # ungleich 0, damit die Pipeline-Route nicht "ok" meldet (B2).
    if HOCHLADEN_FEHLER:
        for name, ende in HOCHLADEN_FEHLER:
            print("")
            print("Hochladen fehlgeschlagen: %s" % name)
            for zeile in ende:
                print("  " + zeile)
        return 3
    # 75 (EX_TEMPFAIL): mindestens ein Haus lief schon in einem anderen
    # Prozess. Die Pipeline-Route macht daraus HTTP 409.
    if besetzt:
        return 75
    return 0


if __name__ == "__main__":
    sys.exit(main())
