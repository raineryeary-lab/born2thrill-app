"""Eine Lieferung wird geprueft, bevor sie irgendwo als fertig gilt.

Rainer, 2026-08-27: "wieso werden so viele unterschiedliche ordner
verwendet?" -- drei Stellen im Code erfanden drei Ordnernamen, und keine
kannte die andere. `bungalow_039` hat acht `codex-final-*`-Ordner; der
Bilder-Tab nahm den alphabetisch letzten, also `codex-final-2026-08-26-v2`
statt des juengeren `codex-final-2026-08-26-2110`.

Ab jetzt gibt es eine Wahrheit je Haus: `renders/ANGENOMMEN.json`, und dorthin
kommt nur, was diese Pruefung besteht.
"""

import hashlib
import importlib.util
import io
import json
import os
import struct
import tempfile
import unittest
import zlib
from pathlib import Path

HERE = Path(__file__).resolve().parent
os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR", str(HERE))


def load_module():
    spec = importlib.util.spec_from_file_location(
        "lieferung_pruefen", HERE / "lieferung-pruefen.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def png(breite, hoehe):
    """Ein winziges, gueltiges PNG mit genau diesen Maszen.

    Der Pruefer liest die Masze aus dem Header, also muss der Header echt
    sein -- eine erfundene Bytefolge wuerde die Pruefung an einer anderen
    Stelle scheitern lassen als gemeint.
    """
    def chunk(typ, daten):
        roh = typ + daten
        return (struct.pack(">I", len(daten)) + roh
                + struct.pack(">I", zlib.crc32(roh) & 0xFFFFFFFF))
    ihdr = struct.pack(">IIBBBBB", breite, hoehe, 8, 2, 0, 0, 0)
    zeilen = b"".join(b"\x00" + b"\x00\x00\x00" * breite for _ in range(hoehe))
    return (bytes([137, 80, 78, 71, 13, 10, 26, 10])
            + chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(zeilen))
            + chunk(b"IEND", b""))


MARKER = [
    {"n": 1, "name": "badewanne-15", "rolle": "Sanitaer", "farbe": "bleibt"},
    {"n": 2, "name": "garderobe-25", "rolle": "Garderobe", "farbe": "ersetzen"},
    {"n": 3, "name": "wall-12-door", "rolle": "Tuer", "farbe": "bleibt"},
]


class Aufbau(unittest.TestCase):
    """Legt eine vollstaendige, fehlerfreie Lieferung an, die jeder Test bricht."""

    def setUp(self):
        self.mod = load_module()
        self.tmp = tempfile.TemporaryDirectory()
        self.ordner = os.path.join(self.tmp.name, "codex-2026-08-27")
        os.makedirs(self.ordner)
        self.job = {
            "job_id": "haus-2026-08-27",
            "plan_id": "haus",
            "required_outputs": [
                {"filename_hint": "01-exterior-classic.png", "kind": "exterior",
                 "target_px": [1920, 1080]},
                {"filename_hint": "02-floorplan-warm-modern.png", "kind": "interior",
                 "target_px": [200, 150]},
            ],
            "object_map": {"markers": MARKER},
        }
        bilder = []
        for eintrag in self.job["required_outputs"]:
            name = eintrag["filename_hint"]
            breite, hoehe = eintrag["target_px"]
            daten = png(breite, hoehe)
            with open(os.path.join(self.ordner, name), "wb") as datei:
                datei.write(daten)
            bild = {"filename": name, "width": breite, "height": hoehe,
                    "sha256": hashlib.sha256(daten).hexdigest()}
            if eintrag["kind"] == "interior":
                bild["marker_check"] = [
                    {"n": m["n"], "name": m["name"],
                     "status": "ersetzt" if m["farbe"] == "ersetzen" else "sichtbar"}
                    for m in MARKER]
            bilder.append(bild)
        self.katalog = {"schema": "visual-catalog-v1", "images": bilder}
        self.schreibe_katalog()

    def schreibe_katalog(self):
        with open(os.path.join(self.ordner, "catalog.json"), "w", encoding="utf-8") as datei:
            json.dump(self.katalog, datei)

    def tearDown(self):
        self.tmp.cleanup()

    def pruefe(self):
        return self.mod.pruefe(self.job, self.ordner)


class VollstaendigeLieferung(Aufbau):
    def test_a_complete_delivery_has_nothing_to_complain_about(self):
        self.assertEqual(self.pruefe(), [])


class SchluesselName(Aufbau):
    """`images` oder `entries` -- der Inhalt zaehlt, nicht das Wort darum.

    Am 2026-08-27 lieferte Codex fuer ein Haus `images`, fuer das naechste
    `entries`. Sechs Beanstandungen wegen eines Wortes helfen niemandem; das
    Regelwerk legt `images` fest, der Pruefer nimmt beide.
    """

    def test_entries_is_accepted_like_images(self):
        self.katalog["entries"] = self.katalog.pop("images")
        self.schreibe_katalog()
        self.assertEqual(self.pruefe(), [])

    def test_a_catalog_without_either_key_is_named(self):
        self.katalog.pop("images")
        self.schreibe_katalog()
        self.assertTrue(any("images" in b for b in self.pruefe()))


class FehlendesUndFalsches(Aufbau):
    def test_a_missing_file_is_named(self):
        os.remove(os.path.join(self.ordner, "01-exterior-classic.png"))
        self.assertTrue(any("01-exterior-classic" in b for b in self.pruefe()))

    def test_wrong_pixel_size_is_named(self):
        """1672 x 941 statt 1920 x 1080 kam am 2026-08-27 wirklich vor.

        Das ist nicht einmal dasselbe Seitenverhaeltnis, laesst sich also
        nicht durch Hochskalieren heilen.
        """
        with open(os.path.join(self.ordner, "01-exterior-classic.png"), "wb") as datei:
            datei.write(png(1672, 941))
        beanstandet = self.pruefe()
        self.assertTrue(any("1672" in b for b in beanstandet), beanstandet)

    def test_a_wrong_sha256_is_named(self):
        """Der Hash schuetzt davor, dass catalog.json ein anderes Bild meint.

        Er wird zum Schluss berechnet; passt er nicht, wurde die Datei nach
        dem Eintrag noch einmal ersetzt.
        """
        self.katalog["images"][0]["sha256"] = "0" * 64
        self.schreibe_katalog()
        self.assertTrue(any("sha256" in b for b in self.pruefe()))

    def test_an_extra_file_is_named(self):
        """Der Upload nimmt jede Bilddatei des Ordners.

        Am 2026-08-26 standen so drei graue Blender-Kloetze im Kundenkatalog.
        """
        with open(os.path.join(self.ordner, "zwischenstand.png"), "wb") as datei:
            datei.write(png(10, 10))
        self.assertTrue(any("zwischenstand" in b for b in self.pruefe()))


class MarkerPruefung(Aufbau):
    def test_a_missing_marker_check_is_named(self):
        del self.katalog["images"][1]["marker_check"]
        self.schreibe_katalog()
        self.assertTrue(any("marker_check" in b for b in self.pruefe()))

    def test_an_incomplete_marker_check_is_named(self):
        """Jeder Marker der Objektkarte genau einmal.

        Am 2026-08-27 verschwand die Badewanne aus einem Bild, dessen
        marker_check sie als "sichtbar" auswies -- die Liste war vollstaendig,
        aber gelogen. Vollstaendigkeit ist trotzdem die Untergrenze.
        """
        self.katalog["images"][1]["marker_check"].pop()
        self.schreibe_katalog()
        self.assertTrue(any("Marker" in b for b in self.pruefe()))

    def test_a_duplicated_marker_is_named(self):
        eintraege = self.katalog["images"][1]["marker_check"]
        eintraege.append(dict(eintraege[0]))
        self.schreibe_katalog()
        self.assertTrue(any("doppelt" in b for b in self.pruefe()))

    def test_a_status_that_contradicts_the_colour_is_named(self):
        """Blau heisst sichtbar, rot heisst ersetzt.

        "Tuerblatt ersetzt" ist keine gueltige Aussage -- ein blauer Marker
        bleibt stehen.
        """
        for eintrag in self.katalog["images"][1]["marker_check"]:
            if eintrag["n"] == 3:
                eintrag["status"] = "ersetzt"
        self.schreibe_katalog()
        self.assertTrue(any("Farbe" in b or "Status" in b for b in self.pruefe()))

    def test_an_unknown_status_word_is_named(self):
        self.katalog["images"][1]["marker_check"][0]["status"] = "vielleicht"
        self.schreibe_katalog()
        self.assertTrue(any("vielleicht" in b or "Status" in b for b in self.pruefe()))

    def test_exteriors_need_no_marker_check(self):
        """Die Objektkarte gilt fuer das Geschoss, nicht fuer die Fassade."""
        self.assertNotIn("marker_check", self.katalog["images"][0])
        self.assertEqual(self.pruefe(), [])


class KarteGiltNurFuerIhrGeschoss(unittest.TestCase):
    """Eine Objektkarte zeigt ein Geschoss, nicht das Haus.

    Rainer, 2026-08-28: `codex-onehalfstorey_020-2026-08-28-final` war
    sachlich einwandfrei -- zehn Bilder unter den geforderten Namen, alle
    sha256 byte-identisch mit dem angenommenen Review-Satz -- und fiel
    trotzdem mit vier Beanstandungen durch:

        07..10-floorplan-*-og.png: marker_check fehlt

    Die Karte des Auftrags war `OBJEKTKARTE-interior-modern-baseline.png`,
    also das Erdgeschoss. Die vier Bilder stammen aus
    `interior-modern-upper-baseline.blend`. Fuer sie gab es nichts zu
    bestaetigen, und der Auftragstext hatte ausdruecklich verboten, etwas zu
    erfinden. Codex hielt sich daran und fiel dafuer durch.

    Wichtig ist, wo die Regel NICHT oeffnet: ohne `source_blend` laesst sich
    die Herkunft nicht bestimmen, dann bleibt der `marker_check` Pflicht.
    Sonst genuegte ein weggelassenes Feld, um die Pruefung zu umgehen.
    """

    def setUp(self):
        self.mod = load_module()

    def deckt(self, karte, quelle):
        return self.mod._karte_deckt_bild(karte, quelle)

    def test_the_map_covers_the_blend_it_was_drawn_from(self):
        self.assertTrue(self.deckt("OBJEKTKARTE-interior-modern-baseline.png",
                                   "interior-modern-baseline.blend"))

    def test_the_ground_floor_map_does_not_cover_the_upper_floor(self):
        """Der echte Fall vom 2026-08-28."""
        self.assertFalse(self.deckt("OBJEKTKARTE-interior-modern-baseline.png",
                                    "interior-modern-upper-baseline.blend"))

    def test_without_a_source_the_image_counts_as_covered(self):
        """Faellt geschlossen: keine Herkunft, keine Ausnahme."""
        self.assertTrue(self.deckt("OBJEKTKARTE-interior-modern-baseline.png", None))
        self.assertTrue(self.deckt("OBJEKTKARTE-interior-modern-baseline.png", ""))

    def test_a_map_without_a_filename_covers_everything(self):
        """Aeltere Auftraege nennen die Datei nicht -- fuer sie gilt das Alte."""
        self.assertTrue(self.deckt(None, "interior-modern-upper-baseline.blend"))


class ZweiGeschosse(Aufbau):
    """Dieselbe Lieferung wie sonst, aber mit zwei Geschossen und einer Karte."""

    def setUp(self):
        super().setUp()
        self.job["object_map"] = {
            "file": "OBJEKTKARTE-interior-modern-baseline.png",
            "markers": MARKER,
        }
        self.job["required_outputs"].append(
            {"filename_hint": "03-floorplan-warm-modern-og.png", "kind": "interior",
             "target_px": [200, 150]})
        daten = png(200, 150)
        with open(os.path.join(self.ordner, "03-floorplan-warm-modern-og.png"), "wb") as datei:
            datei.write(daten)
        self.katalog["images"][1]["source_blend"] = "interior-modern-baseline.blend"
        self.obergeschoss = {
            "filename": "03-floorplan-warm-modern-og.png",
            "source_blend": "interior-modern-upper-baseline.blend",
            "width": 200, "height": 150,
            "sha256": hashlib.sha256(daten).hexdigest(),
        }
        self.katalog["images"].append(self.obergeschoss)
        self.schreibe_katalog()

    def test_an_upper_floor_image_needs_no_marker_check(self):
        """Der Fall, an dem der Finalsatz vom 2026-08-28 scheiterte."""
        self.assertEqual(self.pruefe(), [])

    def test_the_ground_floor_image_still_needs_one(self):
        del self.katalog["images"][1]["marker_check"]
        self.schreibe_katalog()
        self.assertTrue(any("marker_check" in b for b in self.pruefe()))

    def test_an_interior_without_a_source_still_needs_one(self):
        """Ohne Herkunft keine Ausnahme -- sonst waere das Feld ein Schalter."""
        del self.katalog["images"][2]["source_blend"]
        self.schreibe_katalog()
        self.assertTrue(any("03-floorplan-warm-modern-og" in b for b in self.pruefe()))

    def test_a_marker_check_outside_the_map_is_still_checked(self):
        """Wer ausserhalb der Karte etwas behauptet, wird beim Wort genommen.

        Ein erfundener `marker_check` fuer das Obergeschoss darf nicht
        deshalb durchgehen, weil dort keiner verlangt war.
        """
        self.obergeschoss["marker_check"] = [{"n": 99, "name": "erfunden",
                                              "status": "sichtbar"}]
        self.schreibe_katalog()
        self.assertTrue(any("unbekannte Marker" in b for b in self.pruefe()))


class AnnahmeSchreiben(Aufbau):
    def test_nothing_is_written_without_acceptance(self):
        self.pruefe()
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, "ANGENOMMEN.json")))

    def test_acceptance_records_folder_and_files(self):
        pfad = self.mod.annehmen(self.job, self.ordner, self.tmp.name)
        self.assertTrue(os.path.exists(pfad))
        with open(pfad, encoding="utf-8") as datei:
            daten = json.load(datei)
        self.assertEqual(daten["ordner"], "codex-2026-08-27")
        self.assertEqual(daten["job_id"], "haus-2026-08-27")
        self.assertEqual(len(daten["dateien"]), 2)

    def test_a_faulty_delivery_is_never_accepted(self):
        """Sonst waere der Knopf ein Stempel statt einer Pruefung."""
        os.remove(os.path.join(self.ordner, "01-exterior-classic.png"))
        with self.assertRaises(self.mod.Beanstandet):
            self.mod.annehmen(self.job, self.ordner, self.tmp.name)
        self.assertFalse(os.path.exists(os.path.join(self.tmp.name, "ANGENOMMEN.json")))


class ZwischenstandsnamenSindKeineBeanstandung(unittest.TestCase):
    """Der Suffix wird hier abgeschnitten, nicht bei Codex nachbestellt.

    Rainer, 2026-08-28: "ich habe echt keine Lust hier immer wieder zu
    eiern -- aaaa, Codex hat wieder eine Tuer vergessen und eine Datei
    falsch benannt, das muss jetzt endlich vorbei sein."

    Zweimal in Folge hat eine Lieferung nur am Dateinamen gehangen:
    `onehalfstorey_020` mit `-review` und `-review-2`,
    `german_catalog_review_bungalow_3_2_4_b_100_1` mit `-review`. Jedes Mal
    war der Inhalt richtig, jedes Mal kostete es eine ganze Runde bei Codex
    und einen handgeschriebenen Auftrag.

    Der Name zaehlt nur an einer einzigen Stelle: `publish-renders.py` macht
    aus ihm den WordPress-Slug. Das laesst sich hier loesen, auf der eigenen
    Platte, ohne dass Codex die angenommenen Bilder noch einmal anfasst --
    und das ist zugleich sicherer, denn ein Bild, das niemand neu rendert,
    kann auch nichts mehr verlieren.
    """

    def setUp(self):
        self.mod = load_module()

    def test_the_review_suffix_is_stripped(self):
        self.assertEqual(self.mod._grundname("03-floorplan-warm-modern-review.png"),
                         "03-floorplan-warm-modern.png")

    def test_a_numbered_review_round_is_stripped(self):
        """`-review-2` kam am 2026-08-28 wirklich vor."""
        self.assertEqual(self.mod._grundname("01-exterior-classic-review-2.png"),
                         "01-exterior-classic.png")

    def test_a_version_suffix_is_stripped(self):
        self.assertEqual(self.mod._grundname("02-exterior-modern-v3.png"),
                         "02-exterior-modern.png")

    def test_a_plain_name_stays_as_it_is(self):
        self.assertEqual(self.mod._grundname("01-exterior-classic.png"),
                         "01-exterior-classic.png")

    def test_a_name_that_only_looks_like_a_suffix_is_kept(self):
        """`-review` mitten im Namen ist kein Suffix.

        Sonst wuerde aus einem Haus namens `catalog-review-...` stillschweigend
        etwas anderes.
        """
        self.assertEqual(self.mod._grundname("03-floorplan-review-modern.png"),
                         "03-floorplan-review-modern.png")


class ZwischenstandWirdAngenommenUndUmbenannt(Aufbau):
    """Dieselbe Lieferung, nur mit `-review` an jedem Dateinamen."""

    def setUp(self):
        super().setUp()
        for bild in self.katalog["images"]:
            alt = bild["filename"]
            stamm, endung = os.path.splitext(alt)
            neu = stamm + "-review" + endung
            os.rename(os.path.join(self.ordner, alt), os.path.join(self.ordner, neu))
            bild["filename"] = neu
        self.schreibe_katalog()

    def test_a_review_set_passes_the_check(self):
        """Der Fall, der zweimal eine Runde gekostet hat."""
        self.assertEqual(self.pruefe(), [])

    def test_acceptance_renames_the_files_on_disk(self):
        self.mod.annehmen(self.job, self.ordner, self.tmp.name)
        vorhanden = sorted(os.listdir(self.ordner))
        self.assertIn("01-exterior-classic.png", vorhanden)
        self.assertIn("02-floorplan-warm-modern.png", vorhanden)
        self.assertNotIn("01-exterior-classic-review.png", vorhanden)

    def test_acceptance_repairs_the_catalog_too(self):
        """Sonst zeigt `catalog.json` auf Dateien, die es nicht mehr gibt."""
        self.mod.annehmen(self.job, self.ordner, self.tmp.name)
        with open(os.path.join(self.ordner, "catalog.json"), encoding="utf-8") as datei:
            katalog = json.load(datei)
        self.assertEqual(sorted(bild["filename"] for bild in katalog["images"]),
                         ["01-exterior-classic.png", "02-floorplan-warm-modern.png"])

    def test_the_pointer_records_the_required_names(self):
        pfad = self.mod.annehmen(self.job, self.ordner, self.tmp.name)
        with open(pfad, encoding="utf-8") as datei:
            zeiger = json.load(datei)
        self.assertEqual(sorted(eintrag["name"] for eintrag in zeiger["dateien"]),
                         ["01-exterior-classic.png", "02-floorplan-warm-modern.png"])

    def test_the_bytes_are_untouched(self):
        """Umbenennen, nicht neu erzeugen -- die sha256 muss halten."""
        vorher = self.mod.sha256(os.path.join(self.ordner, "01-exterior-classic-review.png"))
        self.mod.annehmen(self.job, self.ordner, self.tmp.name)
        nachher = self.mod.sha256(os.path.join(self.ordner, "01-exterior-classic.png"))
        self.assertEqual(vorher, nachher)

    def test_a_faulty_review_set_is_not_renamed(self):
        """Erst pruefen, dann anfassen.

        Sonst stuenden nach einer abgelehnten Lieferung halb umbenannte
        Dateien im Ordner.
        """
        os.remove(os.path.join(self.ordner, "01-exterior-classic-review.png"))
        with self.assertRaises(self.mod.Beanstandet):
            self.mod.annehmen(self.job, self.ordner, self.tmp.name)
        self.assertIn("02-floorplan-warm-modern-review.png", os.listdir(self.ordner))


class KastenVerdacht(unittest.TestCase):
    """Ist der Stuff-Platzhalter noch ein Kasten?

    Rainer, 2026-08-28: "you have to force the rendering of deco stuff for the
    'stuff', often it just creates a large box."

    Das Regelwerk verlangt das seit Wochen (Abschnitt 2.9 und 11), und der
    `marker_check` fragt es ab -- aber er ist eine Selbstauskunft. Codex meldet
    "ersetzt" und im Bild steht der Kasten.

    Messbar ist es ueber die flache Flaeche. Ein Platzhalter ist ein glatter
    grauer Quader: im Umkreis des Markers sind ueber 60 % der Pixel von ihrer
    eigenen Umgebung nicht zu unterscheiden. Ein eingerichtetes Moebel hat
    Kanten, Stoff, Griffe, Deko -- der Anteil faellt deutlich.

    Die Zahlen unten sind an `onehalfstorey_020` gemessen, Baseline gegen die
    angenommene Lieferung `03-floorplan-warm-modern-eg.png`.

    Gefragt wird zweimal: war die Stelle ein glatter Quader, UND ist sie es
    immer noch. Der erste Anlauf fragte stattdessen nach dem Abfall und schlug
    bei `stuff-23` an -- dort ersetzte ein Tuerblatt den Kasten, und ein
    Tuerblatt ist selbst flach. Es faellt aber auf 51 %, also unter die
    zweite Schwelle.

    Bleibt eine WARNUNG, keine Beanstandung: ein einziger belegter Treffer ist
    zu wenig, um eine fertige Lieferung zu blockieren.
    """

    def setUp(self):
        self.mod = load_module()
        # name -> (farbe, flachanteil baseline, flachanteil Lieferung)
        self.gemessen = {
            "garderobe-16": ("ersetzen", 81.5, 31.0),
            "garderobe-17": ("ersetzen", 83.1, 21.4),
            "stuff-20": ("ersetzen", 72.9, 36.2),
            "stuff-21": ("ersetzen", 81.6, 72.2),   # steht wirklich noch leer
            "stuff-22": ("ersetzen", 80.4, 22.6),
            "stuff-23": ("ersetzen", 59.8, 51.1),   # Tuerblatt -- Fehlalarm
            "stuff-24": ("ersetzen", 85.7, 41.3),
            "stuff-25": ("ersetzen", 61.4, 20.4),
            "stuff-26": ("ersetzen", 68.2, 35.9),
            "handwaschbecken-15": ("bleibt", 74.9, 61.7),
            "kochfeld-5": ("bleibt", 15.9, 19.1),
            "wall-1-door": ("bleibt", 95.9, 78.5),
            "wall-2-door": ("bleibt", 78.5, 71.3),
            "wall-5-door": ("bleibt", 38.5, 35.7),
            "wall-6-door": ("bleibt", 77.6, 71.1),
            "wall-9-door": ("bleibt", 11.1, 26.6),
            "wand_wc-14": ("bleibt", 54.3, 47.5),
        }

    def verdaechtig(self):
        return self.mod.kasten_verdacht(self.gemessen)

    def test_the_placeholder_that_really_stayed_empty_is_flagged(self):
        """stuff-21: Baseline 81.6 % flach, Lieferung 72.2 % -- nichts passiert."""
        self.assertIn("stuff-21", self.verdaechtig())

    def test_replaced_placeholders_are_not_flagged(self):
        """Sieben der neun sind sauber ersetzt und muessen still bleiben."""
        for name in ("garderobe-16", "garderobe-17", "stuff-20", "stuff-22",
                     "stuff-24", "stuff-25", "stuff-26"):
            self.assertNotIn(name, self.verdaechtig())

    def test_nothing_that_must_stay_is_ever_flagged(self):
        """Tueren, Sanitaer und Kueche sollen sich ja gerade nicht aendern.

        Waeren sie dabei, kaeme bei jeder Lieferung eine Liste von acht
        Namen -- und nach der zweiten liest sie niemand mehr.
        """
        for name, (farbe, _, _) in self.gemessen.items():
            if farbe == "bleibt":
                self.assertNotIn(name, self.verdaechtig())

    def test_the_door_leaf_that_used_to_trip_it_stays_quiet(self):
        """stuff-23 war der Fehlalarm des ersten Anlaufs.

        Ein Tuerblatt ersetzte dort den Kasten. Es ist selbst flach, faellt
        aber auf 51 % -- unter die zweite Schwelle. Der Test haelt fest, dass
        die Verschaerfung genau das erledigt hat.
        """
        self.assertNotIn("stuff-23", self.verdaechtig())

    def test_the_wall_with_a_picture_stays_quiet_too(self):
        """Der zweite Fehlalarm, gemessen an
        `german_catalog_review_bungalow_3_2_4_b_100_1`: aus dem Kasten wurde
        eine Wand mit Bild und Regal, 67.7 % -> 48.8 %."""
        self.gemessen["stuff-wand"] = ("ersetzen", 67.7, 48.8)
        self.assertNotIn("stuff-wand", self.verdaechtig())

    def test_only_one_marker_fires_across_both_real_deliveries(self):
        """Der Stand, auf den die Schwellen eingestellt sind.

        Mehr als eine Meldung je Lieferung, und die Liste wird ueberblaettert.
        """
        self.assertEqual(self.verdaechtig(), ["stuff-21"])

    def test_a_marker_that_was_never_flat_is_left_alone(self):
        """Verdeckt oder angeschnitten -- dann laesst sich nichts sagen.

        `kochfeld-5` liegt bei 15.9 % und war nie ein Kasten.
        """
        self.gemessen["stuff-99"] = ("ersetzen", 22.0, 21.0)
        self.assertNotIn("stuff-99", self.verdaechtig())

    def test_the_result_is_sorted_so_two_runs_read_the_same(self):
        self.assertEqual(self.verdaechtig(), sorted(self.verdaechtig()))

    def test_without_measurements_there_is_no_warning(self):
        """Ohne Pillow oder ohne Baseline wird nicht geraten."""
        self.assertEqual(self.mod.kasten_verdacht({}), [])


class VorherFassungenStoerenNicht(Aufbau):
    """Die beiseitegelegte alte Fassung ist Archiv, keine Lieferung.

    Regelwerk Abschnitt 12: "Eine bereits angenommene Datei wird nicht
    ueberschrieben. Verlangt der Auftrag ausdruecklich eine neue Fassung,
    wandert die alte vorher unter `-vorher-<uhrzeit>` zur Seite."

    Am 2026-08-28 tat Codex bei
    `german_catalog_review_bungalow_3_2_5_b_100_1` genau das -- und der
    Pruefer wies die Nachbesserung ab: "Zusatzdateien im Lieferordner, der
    Upload wuerde sie mitnehmen." Regelkonform geliefert und trotzdem
    durchgefallen, zum zweiten Mal an einem Dateinamen.

    Beide Sorgen stimmen: das Archiv soll bleiben, und `publish-renders.py`
    laedt jede Bilddatei des Ordners hoch. Also wandert es beim Annehmen in
    einen Unterordner, statt geloescht oder beanstandet zu werden.
    """

    def setUp(self):
        super().setUp()
        self.alt = "01-exterior-classic-vorher-214552.png"
        with open(os.path.join(self.ordner, self.alt), "wb") as datei:
            datei.write(png(1920, 1080))

    def test_a_previous_version_is_not_a_complaint(self):
        self.assertEqual(self.pruefe(), [])

    def test_acceptance_moves_it_out_of_the_upload_folder(self):
        self.mod.annehmen(self.job, self.ordner, self.tmp.name)
        self.assertNotIn(self.alt, os.listdir(self.ordner))

    def test_it_is_kept_not_deleted(self):
        """Der Beleg, wogegen nachgebessert wurde, bleibt erhalten."""
        self.mod.annehmen(self.job, self.ordner, self.tmp.name)
        archiv = os.path.join(self.ordner, "vorher")
        self.assertTrue(os.path.isdir(archiv))
        self.assertIn(self.alt, os.listdir(archiv))

    def test_the_delivered_files_stay_where_they_are(self):
        self.mod.annehmen(self.job, self.ordner, self.tmp.name)
        self.assertIn("01-exterior-classic.png", os.listdir(self.ordner))

    def test_a_genuinely_stray_file_is_still_named(self):
        """Die Lockerung gilt nur fuer `-vorher-`, nicht fuer alles."""
        with open(os.path.join(self.ordner, "zwischenstand.png"), "wb") as datei:
            datei.write(png(10, 10))
        self.assertTrue(any("zwischenstand" in b for b in self.pruefe()))


class ZweiKartenZweiGeschosse(Aufbau):
    """Je Geschoss eine Karte, und jedes Bild wird gegen seine geprueft.

    Rainer, 2026-08-28: `make-codex-job.py` legt seit heute eine Objektkarte je
    Innen-.blend an. Der Pruefer muss die passende waehlen -- sonst wuerde er
    die OG-Marker gegen die EG-Karte halten und jeden davon als "unbekannt"
    melden.
    """

    def setUp(self):
        super().setUp()
        self.job["object_map"] = [
            {"file": "OBJEKTKARTE-interior-modern-baseline.png", "markers": MARKER},
            {"file": "OBJEKTKARTE-interior-modern-upper-baseline.png",
             "markers": [{"n": 1, "name": "eckbadewanne-9", "rolle": "Sanitaer",
                          "farbe": "bleibt"}]},
        ]
        self.job["required_outputs"].append(
            {"filename_hint": "03-floorplan-warm-modern-og.png", "kind": "interior",
             "target_px": [200, 150]})
        daten = png(200, 150)
        with open(os.path.join(self.ordner, "03-floorplan-warm-modern-og.png"), "wb") as datei:
            datei.write(daten)
        self.katalog["images"][1]["source_blend"] = "interior-modern-baseline.blend"
        self.obergeschoss = {
            "filename": "03-floorplan-warm-modern-og.png",
            "source_blend": "interior-modern-upper-baseline.blend",
            "width": 200, "height": 150,
            "sha256": hashlib.sha256(daten).hexdigest(),
            "marker_check": [{"n": 1, "name": "eckbadewanne-9", "status": "sichtbar"}],
        }
        self.katalog["images"].append(self.obergeschoss)
        self.schreibe_katalog()

    def test_each_image_is_checked_against_its_own_map(self):
        self.assertEqual(self.pruefe(), [])

    def test_an_upper_floor_marker_missing_is_named(self):
        """Der Fall, fuer den die zweite Karte gebaut wurde."""
        self.obergeschoss["marker_check"] = []
        self.schreibe_katalog()
        self.assertTrue(any("marker_check" in b for b in self.pruefe()))

    def test_a_ground_floor_marker_on_an_upper_floor_image_is_foreign(self):
        """Wer die falsche Karte abarbeitet, faellt auf."""
        self.obergeschoss["marker_check"] = [
            {"n": 2, "name": "garderobe-25", "status": "ersetzt"}]
        self.schreibe_katalog()
        self.assertTrue(any("unbekannte Marker" in b or "Marker fehlen" in b
                            for b in self.pruefe()))

    def test_an_older_job_with_one_map_still_works(self):
        """Auftraege von vorher tragen ein einzelnes Objekt statt einer Liste."""
        self.job["object_map"] = {"markers": MARKER}
        del self.obergeschoss["marker_check"]
        self.schreibe_katalog()
        self.assertTrue(any("marker_check" in b for b in self.pruefe()))


class KastenWarnungMitZweiKarten(unittest.TestCase):
    """Die Kasten-Warnung muss die Kartenliste genauso lesen wie die Pruefung.

    Rainer, 2026-08-29: die erste Lieferung nach der Umstellung auf eine Karte
    je Geschoss lief in einen Absturz --

        AttributeError: 'list' object has no attribute 'get'
        in messe_platzhalter: marker = karte.get("markers")

    `pruefe()` war umgestellt, `messe_platzhalter()` nicht. Die formale
    Pruefung war da schon durch; abgestuerzt ist erst die Warnung danach.
    """

    def setUp(self):
        self.mod = load_module()
        self.job = {
            "plan_id": "haus",
            "required_outputs": [{"filename_hint": "01.png", "kind": "interior",
                                  "target_px": [10, 10]}],
            "object_map": [
                {"file": "OBJEKTKARTE-interior-modern-baseline.png", "markers": MARKER},
                {"file": "OBJEKTKARTE-interior-modern-upper-baseline.png",
                 "markers": MARKER},
            ],
        }

    def test_a_list_of_maps_does_not_crash_the_measurement(self):
        """Ohne Baseline-Render kommt {} zurueck -- aber eben kein Absturz."""
        self.assertEqual(self.mod.messe_platzhalter(self.job, "."), {})

    def test_a_single_map_from_an_older_job_still_reads(self):
        self.job["object_map"] = {"file": "OBJEKTKARTE-a.png", "markers": MARKER}
        self.assertEqual(self.mod.messe_platzhalter(self.job, "."), {})

    def test_no_map_at_all_is_fine(self):
        self.job["object_map"] = None
        self.assertEqual(self.mod.messe_platzhalter(self.job, "."), {})


class BelegStattBehauptung(Aufbau):
    """Zu jedem blauen Marker gehoert die Stelle, an der Codex das Objekt sieht.

    Rainer, 2026-08-29, ueber einen geschlossenen Kreis mit Codex: erst muss
    die Fehlerklasse weg, sonst wiederholt der Automat nur schneller dasselbe.

    Die Klasse ist immer dieselbe gewesen -- ein Objekt, das bleiben muss, ist
    verschwunden, und der `marker_check` meldete "sichtbar":

        2026-08-27  Badewanne, zwei Bilder
        2026-08-28  Schreibtisch, drei von vier Bildern
        2026-08-29  Waschmaschine und Trockner, zwei von vier Bildern

    Eine Behauptung laesst sich nicht pruefen. Eine Koordinate schon: `bei`
    ist der Pixel, an dem Codex das Objekt IM GELIEFERTEN BILD sieht. Wer sie
    hinschreibt, muss hinsehen -- und eine falsche Angabe faellt in einem
    Blick auf, statt dass jemand vier Bilder absucht.

    Die Angabe wird nur fuer blaue Marker verlangt. Rot heisst ersetzen; dort
    ist gerade kein Ausgangsobjekt mehr zu sehen.
    """

    def setUp(self):
        super().setUp()
        self.job["beleg_verlangt"] = True
        self.job["object_map"] = {
            "file": "OBJEKTKARTE-a.png",
            # Bewusst gross: sonst schlaegt die Bildgrenze zu, bevor der
            # Abstand geprueft werden kann.
            "image": [2000, 1500],
            "markers": [dict(m, px=[1000, 750]) for m in MARKER],
        }
        for bild in self.katalog["images"]:
            for eintrag in bild.get("marker_check") or []:
                if eintrag["status"] == "sichtbar":
                    eintrag["bei"] = [1000, 750]
        self.schreibe_katalog()

    def eintrag(self, n):
        for e in self.katalog["images"][1]["marker_check"]:
            if e["n"] == n:
                return e
        raise AssertionError(n)

    def test_a_complete_delivery_with_sightings_passes(self):
        self.assertEqual(self.pruefe(), [])

    def test_a_visible_marker_without_a_sighting_is_named(self):
        """Der Kern: 'sichtbar' allein ist ab jetzt keine Aussage mehr."""
        del self.eintrag(1)["bei"]
        self.schreibe_katalog()
        beanstandet = self.pruefe()
        self.assertTrue(any("bei" in b and "1" in b for b in beanstandet), beanstandet)

    def test_a_replaced_marker_needs_no_sighting(self):
        """Rot heisst ersetzen -- dort ist nichts vom Ausgangsobjekt zu sehen."""
        for eintrag in self.katalog["images"][1]["marker_check"]:
            if eintrag["status"] == "ersetzt":
                self.assertNotIn("bei", eintrag)
        self.assertEqual(self.pruefe(), [])

    def test_a_sighting_outside_the_image_is_named(self):
        self.eintrag(1)["bei"] = [5000, 750]
        self.schreibe_katalog()
        self.assertTrue(any("ausserhalb des Bildes" in b for b in self.pruefe()))

    def test_a_sighting_far_from_its_marker_is_named(self):
        """Ein Objekt bleibt in seinem Fussabdruck.

        Wer es 900 Pixel entfernt sieht, sieht entweder ein anderes Objekt
        oder hat die Zahl erfunden.
        """
        self.eintrag(1)["bei"] = [1000, 750 - 700]
        self.schreibe_katalog()
        self.assertTrue(any("weit von seinem Marker" in b for b in self.pruefe()))

    def test_a_sighting_a_little_off_is_accepted(self):
        """Der Marker sitzt im Schwerpunkt, das Objekt hat Ausdehnung."""
        self.eintrag(1)["bei"] = [1000 + 160, 750 + 90]
        self.schreibe_katalog()
        self.assertEqual(self.pruefe(), [])

    def test_an_older_job_is_not_asked_for_sightings(self):
        """Eine neue Forderung wirkt nicht nach hinten.

        Rainer, 2026-08-29: die erste Fassung dieser Pruefung warf 152
        Beanstandungen gegen eine Lieferung, die am Tag zuvor gegen die
        damalige Fassung von Abschnitt 11.1 gemacht worden war -- vollstaendig
        und regelkonform. Auftraege ohne `beleg_verlangt` stammen von vorher.
        """
        del self.job["beleg_verlangt"]
        for bild in self.katalog["images"]:
            for eintrag in bild.get("marker_check") or []:
                eintrag.pop("bei", None)
        self.schreibe_katalog()
        self.assertEqual(self.pruefe(), [])

    def test_a_new_job_without_sightings_is_named(self):
        """Gegenprobe: mit der Forderung im Auftrag zaehlt sie auch."""
        for bild in self.katalog["images"]:
            for eintrag in bild.get("marker_check") or []:
                eintrag.pop("bei", None)
        self.schreibe_katalog()
        self.assertTrue(any("`bei`" in b for b in self.pruefe()))

    def test_a_map_without_pixel_positions_asks_for_nothing(self):
        """Aeltere Auftraege tragen keine `px` -- dann ist nichts zu vergleichen."""
        self.job["object_map"] = {"file": "OBJEKTKARTE-a.png", "markers": MARKER}
        for bild in self.katalog["images"]:
            for eintrag in bild.get("marker_check") or []:
                eintrag.pop("bei", None)
        self.schreibe_katalog()
        self.assertEqual(self.pruefe(), [])


class RundenMitschreiben(Aufbau):
    """Je Pruefung eine Zeile. Die Zahl, an der spaeter entschieden wird.

    Rainer, 2026-08-29, ueber einen geschlossenen Kreis mit Codex: "wenn wir
    wirklich zufrieden sind mit unserem Auftrag-schreiben-Prompt und mehr oder
    weniger sicher sein koennen, dass nicht viele Fehler und Endlosschleifen
    auftreten."

    Das ist messbar statt Gefuehl: wie oft geht eine Lieferung im ERSTEN
    Durchlauf durch? In den zwei Tagen davor: keine einzige von vier. Bei der
    Quote waere ein geschlossener Kreis nur eine schnellere Art, dasselbe zu
    wiederholen.

    `RUNDEN.jsonl` sammelt das, eine Zeile je Pruefung, damit die Antwort
    spaeter dasteht statt geschaetzt zu werden.
    """

    def zeilen(self):
        pfad = os.path.join(self.tmp.name, "RUNDEN.jsonl")
        if not os.path.exists(pfad):
            return []
        with open(pfad, encoding="utf-8") as datei:
            return [json.loads(z) for z in datei if z.strip()]

    def test_a_clean_check_is_recorded(self):
        self.mod.notiere_runde(self.job, self.ordner, self.tmp.name, [])
        zeile = self.zeilen()[0]
        self.assertEqual(zeile["beanstandungen"], 0)
        self.assertEqual(zeile["plan_id"], "haus")
        self.assertEqual(zeile["ordner"], "codex-2026-08-27")

    def test_complaints_are_counted_and_kept(self):
        self.mod.notiere_runde(self.job, self.ordner, self.tmp.name,
                               ["01.png: Datei fehlt", "02.png: sha256 stimmt nicht"])
        zeile = self.zeilen()[0]
        self.assertEqual(zeile["beanstandungen"], 2)
        self.assertEqual(len(zeile["was"]), 2)

    def test_every_check_appends_a_line(self):
        """Auch die Wiederholung zaehlt -- sonst sieht eine dritte Runde aus
        wie eine erste."""
        for _ in range(3):
            self.mod.notiere_runde(self.job, self.ordner, self.tmp.name, [])
        self.assertEqual(len(self.zeilen()), 3)

    def test_a_defect_found_by_eye_can_be_added(self):
        """Der Prueferblick fand die Badewanne nicht -- das Auge fand sie.

        Ohne diese Unterscheidung sieht die Statistik besser aus, als sie ist.
        """
        self.mod.notiere_runde(self.job, self.ordner, self.tmp.name, [],
                               auge="Waschmaschine fehlt in 04 und 06")
        zeile = self.zeilen()[0]
        self.assertEqual(zeile["beanstandungen"], 0)
        self.assertEqual(zeile["auge"], "Waschmaschine fehlt in 04 und 06")

    def test_a_broken_record_never_blocks_the_check(self):
        """Eine Statistik darf keine Lieferung aufhalten."""
        pfad = os.path.join(self.tmp.name, "RUNDEN.jsonl")
        os.makedirs(pfad)          # ein Ordner, wo eine Datei hingehoert
        self.mod.notiere_runde(self.job, self.ordner, self.tmp.name, [])




class BelegNurFuerDenEigenenAuftrag(unittest.TestCase):
    """Eine Lieferung wird gegen IHREN Auftrag geprueft, nicht gegen den neuesten.

    Rainer, 2026-08-30, schickt dieselbe Lieferung noch einmal zur Pruefung --
    sie war am 2026-08-29 formal in Ordnung und bekam jetzt 152
    Beanstandungen, alle: "ist als sichtbar gemeldet, aber ohne `bei`".

    Der Grund ist meine eigene Aenderung. `beleg_verlangt` steht im AUFTRAG,
    und `go.py` erzeugt den Auftrag bei jedem Lauf neu:

        Lieferung   job_id ...-2026-08-29
        Auftrag     job_id ...-2026-08-30   beleg_verlangt: True

    Die Lieferung antwortet also auf den Auftrag von gestern und wird gegen
    den von heute gemessen. Die Absicht war ausdruecklich, dass eine neue
    Forderung nicht nach hinten wirkt -- der Gate am Auftrag reicht dafuer
    nicht, weil der Auftrag mitwandert.

    Verglichen werden muss die job_id.
    """

    def test_gleicher_auftrag_verlangt_den_beleg(self):
        self.assertTrue(load_module().beleg_gilt(
            {"job_id": "haus-2026-08-30", "beleg_verlangt": True},
            {"job_id": "haus-2026-08-30"}))

    def test_ein_aelterer_auftrag_wird_verschont(self):
        self.assertFalse(load_module().beleg_gilt(
            {"job_id": "haus-2026-08-30", "beleg_verlangt": True},
            {"job_id": "haus-2026-08-29"}))

    def test_ohne_forderung_nie(self):
        self.assertFalse(load_module().beleg_gilt(
            {"job_id": "haus-2026-08-30"},
            {"job_id": "haus-2026-08-30"}))

    def test_ohne_job_id_in_der_lieferung_zaehlt_die_forderung(self):
        """Verschont wird nur, wo BEIDE Kennungen dastehen und sich
        unterscheiden. Sonst liesse sich die Pruefung abschalten, indem man
        die Kennung weglaesst -- und die bestehenden Pruefungen in
        `BelegStattBehauptung` arbeiten genau mit solchen Katalogen."""
        self.assertTrue(load_module().beleg_gilt(
            {"job_id": "haus-2026-08-30", "beleg_verlangt": True}, {}))

    def test_ohne_job_id_im_auftrag_zaehlt_nur_die_forderung(self):
        """Ein von Hand gebauter Auftrag ohne Kennung soll nicht alles
        durchwinken, nur weil die Kennung fehlt."""
        self.assertTrue(load_module().beleg_gilt(
            {"beleg_verlangt": True}, {"job_id": "haus-2026-08-29"}))


class AbgeschriebenIstNichtGeprueft(unittest.TestCase):
    """Vier verschieden gestylte Bilder koennen nicht denselben Befund haben.

    Rainer, 2026-08-30, an german_catalog_review_bungalow_3_3_2_b_100_2: in
    drei von vier Grundrissen standen Sitz- und Essgruppe woanders als im
    Bauplan. Trotzdem meldete die catalog.json in ALLEN VIER Bildern 34 von 34
    Markern als sichtbar -- und die `bei`-Koordinaten waren untereinander
    zeichengleich UND pixelgenau die `px` aus dem Auftrag.

    Der bisherige Beleg (`bei` nahe am Marker) belohnt genau das: wer die Zahl
    aus dem Auftrag abschreibt, besteht ihn immer. Nachgemessen war das keine
    Ausnahme -- auch bungalow_001 hatte vier zeichengleiche Bloecke.

    Was dieser Test NICHT behauptet: dass die Bilder falsch sind. Er sagt nur,
    dass der Befund keiner ist. Vier getrennt gerenderte Bilder mit anderem
    Stil, anderem Licht und anderer Ausstattung geben nicht denselben
    Pixelbefund -- wer das meldet, hat einmal hingesehen und dreimal
    abgeschrieben, oder keinmal.
    """

    def marker_check(self, versatz=0):
        return [{"n": m["n"], "name": m["name"],
                 "status": "ersetzt" if m["farbe"] == "ersetzen" else "sichtbar",
                 "bei": [100 + versatz, 100 + versatz]}
                for m in MARKER]

    def lieferung(self, bloecke):
        mod = load_module()
        katalog = {"images": [{"filename": "%02d-floorplan.png" % (i + 3),
                               "marker_check": b} for i, b in enumerate(bloecke)]}
        return mod, katalog

    def test_vier_zeichengleiche_bloecke_werden_beanstandet(self):
        mod, katalog = self.lieferung([self.marker_check()] * 4)
        befund = mod.abgeschriebene_marker(katalog)
        self.assertTrue(befund, "vier identische Befunde blieben unbeanstandet")
        self.assertIn("4", befund[0])

    def test_zwei_bilder_reichen_noch_nicht(self):
        # Zwei Bilder koennen zufaellig gleich ausfallen. Erst ab drei ist es
        # kein Zufall mehr -- lieber spaet melden als falsch.
        mod, katalog = self.lieferung([self.marker_check()] * 2)
        self.assertEqual(mod.abgeschriebene_marker(katalog), [])

    def test_ein_abweichendes_bild_entschuldigt_die_anderen_drei_nicht(self):
        # Ich hatte hier zuerst das Gegenteil erwartet: ein Unterschied in
        # einem von vier Bildern sollte reichen. Das ist falsch. Drei
        # zeichengleiche Befunde sind drei Abschriften, egal was im vierten
        # Bild steht -- jedes Bild wird einzeln gerendert und einzeln geprueft.
        bloecke = [self.marker_check(), self.marker_check(),
                   self.marker_check(), self.marker_check(versatz=9)]
        mod, katalog = self.lieferung(bloecke)
        befund = mod.abgeschriebene_marker(katalog)
        self.assertTrue(befund)
        self.assertIn("3 Bilder", befund[0])

    def test_zwei_und_zwei_bleibt_unbeanstandet(self):
        # Zwei Paare koennen zufaellig gleich ausfallen; keine Gruppe erreicht
        # drei. Lieber spaet melden als falsch.
        bloecke = [self.marker_check(), self.marker_check(),
                   self.marker_check(versatz=9), self.marker_check(versatz=9)]
        mod, katalog = self.lieferung(bloecke)
        self.assertEqual(mod.abgeschriebene_marker(katalog), [])

    def test_ohne_marker_check_gibt_es_nichts_zu_vergleichen(self):
        mod, katalog = self.lieferung([])
        self.assertEqual(mod.abgeschriebene_marker(katalog), [])

    def test_bloecke_ohne_bei_werden_nicht_verglichen(self):
        # Aeltere Auftraege verlangen kein `bei`. Ohne Koordinaten sind vier
        # gleiche Statuslisten normal und kein Verdacht.
        ohne = [[{"n": m["n"], "name": m["name"], "status": "sichtbar"}
                 for m in MARKER] for _ in range(4)]
        mod, katalog = self.lieferung(ohne)
        self.assertEqual(mod.abgeschriebene_marker(katalog), [])

    def test_der_befund_steht_in_der_Pruefung(self):
        # Nicht nur die Hilfsfunktion -- er muss aus `pruefe()` herauskommen,
        # sonst ruft ihn niemand. (Vierter Verdrahtungsfehler dieser Art
        # heute: ein Helfer, den keiner aufruft, ist keine Pruefung.)
        quelle = (HERE / "lieferung-pruefen.py").read_text(encoding="utf-8")
        koerper = quelle[quelle.index("def pruefe("):quelle.index("def _auf_geforderte_namen")]
        self.assertIn("abgeschriebene_marker", koerper)



class GegenDasBesteBildMessen(unittest.TestCase):
    """Ein verschobenes Moebel von einem schiefen Lineal unterscheiden.

    Rainer, 2026-08-30, nachdem Codex aufgehoert hatte abzuschreiben: der
    Pruefer meldete 14 Beanstandungen an 3_3_2. Nachgerechnet ueber alle vier
    Bilder je Objekt zerfielen sie in zwei Gruppen:

        essgruppe_6-5       233   10  226  262   -> Bild 04 trifft, drei nicht
        doppelwaschtisch-23 308  346  347  511   -> KEINES trifft

    Trifft ein Bild, ist die Planstelle gut und die anderen haben wirklich
    umgeraeumt. Trifft KEINES, liegt es nicht an den Bildern: `px` ist in
    make-codex-job.py der projizierte URSPRUNG des fuehrenden Netzes, nicht
    die sichtbare Mitte. Am Baseline-Render nachgesehen -- an der Planstelle
    von `wand_wc-24` ist gar kein WC, dort ist eine Wandecke. Bei einem
    wandhaengenden oder zweiteiligen Objekt sitzt der Ursprung neben dem, was
    man sieht.

    Ein systematischer Versatz kuerzt sich heraus, sobald man gegen das BESTE
    der Bilder misst statt gegen den Plan allein. Was bleibt, ist echtes
    Umraeumen.
    """

    def bilder(self, *stellen):
        """Je Bild eine Stelle fuer dasselbe Objekt."""
        return {"images": [
            {"filename": "%02d-floorplan.png" % (i + 3),
             "marker_check": [{"n": 1, "name": "sofa-1", "status": "sichtbar",
                               "bei": list(ort)}]}
            for i, ort in enumerate(stellen)]}

    def job(self):
        return {"beleg_verlangt": True, "job_id": "haus-1",
                "object_map": {"image": [2000, 1500],
                               "markers": [{"n": 1, "name": "sofa-1",
                                            "farbe": "bleibt", "px": [1000, 750]}]}}

    def test_trifft_ein_bild_sind_die_anderen_verschoben(self):
        mod = load_module()
        schlecht, unklar, _ = mod.verschobene_objekte(
            self.job(), self.bilder((1010, 760), (1400, 1100)))
        self.assertEqual(unklar, [])
        self.assertEqual(len(schlecht), 1, schlecht)
        # Beanstandet wird 04. Dass 03 im Satz VORKOMMT, ist Absicht: er nennt
        # das Bild, in dem das Sofa richtig sitzt -- damit man nachsehen kann,
        # wie es aussehen soll. (Meine erste Erwartung hier war das Gegenteil
        # und war falsch.)
        self.assertTrue(schlecht[0].startswith("04-floorplan.png:"), schlecht[0])
        self.assertIn("sofa-1", schlecht[0])
        self.assertIn("in 03-floorplan.png sitzt es richtig", schlecht[0])

    def test_trifft_KEIN_bild_ist_das_lineal_schief(self):
        mod = load_module()
        schlecht, unklar, _ = mod.verschobene_objekte(
            self.job(), self.bilder((1400, 1100), (1420, 1150)))
        self.assertEqual(schlecht, [], "das ist unser Massstab, nicht ihre Lieferung")
        self.assertEqual(unklar, ["sofa-1"])

    def test_drei_daneben_werden_alle_drei_genannt(self):
        mod = load_module()
        schlecht, _, _ = mod.verschobene_objekte(
            self.job(), self.bilder((1000, 750), (1400, 1100), (600, 300), (1500, 200)))
        self.assertEqual(len(schlecht), 3, schlecht)

    def test_ein_einziges_bild_wird_nicht_quergeprueft(self):
        # Ohne zweites Bild gibt es kein "bestes". Dann bleibt die alte Regel
        # gegen den Plan die einzige, die es gibt -- siehe
        # BelegStattBehauptung.test_a_sighting_far_from_its_marker_is_named.
        mod = load_module()
        schlecht, unklar, _ = mod.verschobene_objekte(self.job(), self.bilder((1400, 1100)))
        self.assertEqual((schlecht, unklar), ([], []))

    def test_ohne_beleg_verlangt_wird_nichts_gemessen(self):
        mod = load_module()
        job = self.job()
        del job["beleg_verlangt"]
        schlecht, unklar, _ = mod.verschobene_objekte(
            job, self.bilder((1000, 750), (1400, 1100)))
        self.assertEqual((schlecht, unklar), ([], []))

    def test_gleichmaessig_daneben_ist_kein_umraeumen(self):
        """Der Fall, der die Regel gedreht hat.

        Rainer, 2026-08-30, dritte Runde an 3_3_2: das Wohnzimmer war
        repariert, es blieben neun Beanstandungen -- ALLE im Bad:

            badewanne-21           352 167 175 155   bestes 155
            doppelwaschtisch-23    319 343 363 293   bestes 293
            dusche_gross-20        303 320 322 197   bestes 197

        Im Wohnzimmer kommt das beste Bild auf 4 bis 57 Pixel heran, im Bad
        NIE unter 155. Kein Bild trifft je -- das ist der Versatz zwischen
        Objektursprung und sichtbarer Mitte, nicht verschobenes Mobiliar. Dass
        der Doppelwaschtisch ueberhaupt gemeldet wurde, lag allein daran, dass
        seine 293 knapp unter der festen 300er-Schwelle lagen. Willkuer, keine
        Messung.

        Also relativ messen: beanstandet wird, wer DEUTLICH schlechter ist als
        das beste Bild. Ein gleichmaessiger Versatz kuerzt sich heraus.
        """
        mod = load_module()
        # Vier Bilder, alle rund 350 Pixel daneben, aber untereinander einig.
        schlecht, _, _ = mod.verschobene_objekte(
            self.job(), self.bilder((1250, 1000), (1280, 1010),
                                    (1230, 1030), (1270, 980)))
        self.assertEqual(schlecht, [], schlecht)

    def test_ein_ausreisser_unter_gleichmaessig_daneben_wird_genannt(self):
        # Drei einig bei rund 350, eines bei rund 900. Das eine faellt auf.
        mod = load_module()
        schlecht, _, _ = mod.verschobene_objekte(
            self.job(), self.bilder((1250, 1000), (1280, 1010),
                                    (1230, 1030), (1800, 1400)))
        self.assertEqual(len(schlecht), 1, schlecht)
        self.assertTrue(schlecht[0].startswith("06-floorplan.png:"), schlecht[0])

    def test_die_querpruefung_haengt_in_pruefe(self):
        # Ein Helfer, den niemand aufruft, ist keine Pruefung.
        quelle = (HERE / "lieferung-pruefen.py").read_text(encoding="utf-8")
        koerper = quelle[quelle.index("def pruefe("):quelle.index("def _auf_geforderte_namen")]
        self.assertIn("verschobene_objekte", koerper)


    def test_kein_objekt_wird_zweimal_beanstandet(self):
        """Die aeltere Regel tritt zurueck, wo die neue urteilt.

        Beim ersten Bauen liefen beide: 24 Beanstandungen statt 10, jedes
        verschobene Moebel zweimal -- einmal gegen das beste Bild und einmal
        gegen den Plan allein, also mit dem Massstab, dessen Schiefe der Anlass
        fuer die Querpruefung war.
        """
        mod = load_module()
        _, _, beurteilt = mod.verschobene_objekte(
            self.job(), self.bilder((1010, 760), (1400, 1100)))
        self.assertIn("sofa-1", beurteilt)
        # Mit dem Namen in der Hand laesst die aeltere Regel den Abstand liegen.
        marker = {"name": "sofa-1", "px": [1000, 750]}
        eintrag = {"n": 1, "name": "sofa-1", "status": "sichtbar", "bei": [1400, 1100]}
        self.assertEqual(
            mod._beleg_beanstandungen("04.png", eintrag, marker, [2000, 1500],
                                      abstand_pruefen=False), [])
        self.assertTrue(
            mod._beleg_beanstandungen("04.png", eintrag, marker, [2000, 1500]))


# GANZ ANS ENDE. `unittest.main()` sammelt nur ein, was BIS HIERHIN definiert
# ist -- eine Klasse darunter laeuft nie mit und meldet trotzdem "OK".
# Sechstes Mal an einem Tag (2026-08-30); wer hier etwas anhaengt, haengt es
# ueber diese Zeilen.
class NachweisPruefungTest(unittest.TestCase):
    """Ohne Nachweis wird die Lieferung nicht angenommen.

    Rainer, 2026-08-31: "hes guessing again", "the asshole is not reading the
    blender files". Der Auftrag verlangt seit dem 2026-08-30, die .blend zu
    oeffnen; Codex hatte am selben Tag zugegeben, es noch nie getan zu haben.
    Ein Satz im Auftrag, den niemand nachprueft, aendert nichts.

    make-codex-job.py legt die Zahl der MESH-Objekte in codex-job.json unter
    `nachweis` ab und druckt sie NICHT in den Auftragstext. Wer sie in
    catalog.json richtig nennt, hat die Datei offen gehabt.
    """

    def test_die_richtige_zahl_geht_durch(self):
        modul = load_module()
        self.assertEqual(
            modul.nachweis_beanstandungen(
                {"nachweis": {"mesh_objekte": 214}},
                {"nachweis": "NACHWEIS: 214 MESH-Objekte"}),
            [])

    def test_eine_falsche_zahl_wird_beanstandet(self):
        modul = load_module()
        raus = modul.nachweis_beanstandungen(
            {"nachweis": {"mesh_objekte": 214}},
            {"nachweis": "NACHWEIS: 190 MESH-Objekte"})
        self.assertEqual(len(raus), 1)
        self.assertIn("190", raus[0])
        self.assertIn("214", raus[0])

    def test_ein_fehlender_nachweis_wird_beanstandet(self):
        modul = load_module()
        raus = modul.nachweis_beanstandungen(
            {"nachweis": {"mesh_objekte": 214}}, {"images": []})
        self.assertEqual(len(raus), 1)
        self.assertIn("Nachweis", raus[0])

    def test_alte_auftraege_ohne_nachweis_bleiben_gueltig(self):
        # Die zwoelf Auftraege vom 28.-30. August tragen kein `nachweis`.
        # Sie duerfen daran nicht scheitern.
        modul = load_module()
        self.assertEqual(modul.nachweis_beanstandungen({}, {"images": []}), [])
        self.assertEqual(
            modul.nachweis_beanstandungen({"nachweis": {}}, {"images": []}), [])

    def test_die_zahl_darf_irgendwo_im_katalog_stehen(self):
        # Codex hat den Rueckgabeschluessel schon einmal anders benannt
        # (`images` statt `entries`, 2026-08-27). Der Nachweis zaehlt, nicht
        # das Feld, in dem er steht.
        modul = load_module()
        self.assertEqual(
            modul.nachweis_beanstandungen(
                {"nachweis": {"mesh_objekte": 214}},
                {"notes": ["fertig", "NACHWEIS: 214 MESH-Objekte"]}),
            [])


class KastenInJedemBildTest(unittest.TestCase):
    """Ein Platzhalter kann in EINEM Bild ein Kasten bleiben und im naechsten nicht.

    `messe_platzhalter` misst seit jeher nur das erste Innenbild, mit der
    Begruendung im eigenen Docstring: "ein Platzhalter, der in einem Stil ein
    Kasten blieb, ist es in allen vieren."

    Am 2026-09-01 an german_catalog_review_bungalow_3_3_4_b_100_2 widerlegt.
    `stuff-9` (400 x 2450 x 800 mm an der Kuechenwand):

        03-floorplan-warm-modern       glatter Kasten
        04-floorplan-dark-modern       Kuechenzeile mit Fronten und Griffen
        05-floorplan-soft-scandinavian Kuechenzeile mit Fronten und Griffen
        06-floorplan-classic           glatter Kasten

    Die Warnung schlug an, weil 03 zufaellig das erste Bild ist. Waere 03 in
    Ordnung gewesen und nur 06 falsch, haette niemand etwas gesagt -- und ein
    Klotz waere in den Kundenkatalog gegangen, so wie am 2026-08-26 schon
    dreimal.

    `kasten_verdacht` bekommt deshalb je Marker die Messung aus JEDEM Bild und
    schlaegt an, sobald EINES davon noch flach ist.
    """

    def test_ein_einziges_flaches_bild_genuegt(self):
        modul = load_module()
        # (Farbe, flach im Baseline, flach je Lieferbild)
        raus = modul.kasten_verdacht({"stuff-9": ("ersetzen", 95.0, [95.0, 10.0, 12.0, 94.0])})
        self.assertEqual(raus, ["stuff-9"],
                         "in 03 und 06 blieb der Kasten stehen und niemand sagt es")

    def test_ueberall_ersetzt_ist_in_ordnung(self):
        modul = load_module()
        self.assertEqual(
            modul.kasten_verdacht({"stuff-9": ("ersetzen", 95.0, [10.0, 12.0, 9.0, 11.0])}),
            [])

    def test_eine_einzelne_zahl_gilt_weiter(self):
        # Alte Aufrufer und alte Messungen geben eine Zahl statt einer Liste.
        # Die Warnung darf daran nicht scheitern.
        modul = load_module()
        self.assertEqual(
            modul.kasten_verdacht({"stuff-9": ("ersetzen", 95.0, 95.0)}), ["stuff-9"])
        self.assertEqual(
            modul.kasten_verdacht({"stuff-9": ("ersetzen", 95.0, 10.0)}), [])

    def test_was_nie_ein_kasten_war_wird_nicht_gemeldet(self):
        # War die Stelle schon im Baseline nicht flach, ist sie verdeckt oder
        # angeschnitten -- daraus laesst sich nichts schliessen.
        modul = load_module()
        self.assertEqual(
            modul.kasten_verdacht({"stuff-9": ("ersetzen", 20.0, [95.0, 95.0])}), [])

    def test_nur_ersetzen_marker_zaehlen(self):
        modul = load_module()
        self.assertEqual(
            modul.kasten_verdacht({"badewanne-17": ("bleibt", 95.0, [95.0])}), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
