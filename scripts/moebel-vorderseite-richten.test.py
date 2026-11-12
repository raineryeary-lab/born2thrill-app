"""Tests fuer den Korrekturlauf, der Moebel von der Wand wegdreht.

Zwei Dinge muessen stimmen, und beide sind schon einmal schiefgegangen:

1. Die Drehung kommt aus der NORMALEN, nicht aus der Wandrichtung. Genau das
   war der Fehler in snapStampToWalls -- das Vorzeichen wurde bestimmt und
   dann weggeworfen.
2. Der Lauf richtet NUR Moebel, deren Ruecken definitionsgemaess an der Wand
   liegt. Eine Badewanne liegt mit der langen Seite an der Wand und ihre
   Vorderseite ist das Armaturenende; sie wegzudrehen waere ein neuer Fehler.
"""

import math
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import importlib.util

_pfad = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                     "moebel-vorderseite-richten.py")
_spec = importlib.util.spec_from_file_location("richten", _pfad)
richten = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(richten)


class DrehungAusNormale(unittest.TestCase):
    def test_vorderseite_faellt_auf_die_normale(self):
        for nx, ny in [(0, 1), (0, -1), (1, 0), (-1, 0)]:
            grad = richten.drehung_aus_normale(nx, ny)
            fx, fy = richten.vorderseite(grad)
            self.assertAlmostEqual(fx, nx, places=9, msg="%s,%s" % (nx, ny))
            self.assertAlmostEqual(fy, ny, places=9, msg="%s,%s" % (nx, ny))

    def test_dieselbe_wand_von_beiden_seiten_liegt_180_auseinander(self):
        oben = richten.drehung_aus_normale(0, 1)
        unten = richten.drehung_aus_normale(0, -1)
        self.assertEqual(abs(oben - unten), 180)


class NormaleZeigtInDenRaum(unittest.TestCase):
    """Eine waagerechte Wand, das Stueck einmal darueber und einmal darunter."""

    KANTE = (0.0, (1000.0, 0.0), [0, 0], [2000, 0])

    def test_stueck_oberhalb_bekommt_die_normale_nach_oben(self):
        nx, ny = richten.raumnormale((1000, 500), self.KANTE)
        self.assertAlmostEqual(nx, 0.0, places=9)
        self.assertAlmostEqual(ny, 1.0, places=9)

    def test_stueck_unterhalb_bekommt_die_normale_nach_unten(self):
        nx, ny = richten.raumnormale((1000, -500), self.KANTE)
        self.assertAlmostEqual(nx, 0.0, places=9)
        self.assertAlmostEqual(ny, -1.0, places=9)


class WelcheTypenGerichtetWerden(unittest.TestCase):
    def test_schraenke_und_geraete_gehoeren_dazu(self):
        for schluessel in ["kleiderschrank", "garderobe", "lowboard",
                           "kuehlschrank", "wand_wc", "waschmaschine"]:
            self.assertIn(schluessel, richten.AN_DIE_WAND, schluessel)

    def test_was_einer_anderen_regel_folgt_bleibt_unangetastet(self):
        # Badewanne: Armaturenende zeigt die Wand entlang.
        # Schreibtischstuhl: schaut zum Schreibtisch.
        # Schreibtisch: es wird davor gesessen, oft mit Blick zur Wand.
        for schluessel in ["badewanne", "eckbadewanne", "schreibtischstuhl",
                           "schreibtisch", "schreibtisch_kind", "dusche_gross"]:
            self.assertNotIn(schluessel, richten.AN_DIE_WAND, schluessel)


class GeschossZuordnung(unittest.TestCase):
    """Die Moebeldatei heisst floor-0, die Geometrie nennt es groundfloor."""

    GEOM = {"floors": [{"floor_level": "groundfloor", "rooms": [{"polygon": [[0, 0]]}]},
                       {"floor_level": "upperfloor", "rooms": [{"polygon": [[9, 9]]}]}]}

    def test_floor_0_findet_das_erdgeschoss(self):
        rooms = richten.raeume_fuer(self.GEOM, "floor-0")
        self.assertEqual(rooms[0]["polygon"], [[0, 0]])

    def test_floor_1_findet_das_obergeschoss(self):
        rooms = richten.raeume_fuer(self.GEOM, "floor-1")
        self.assertEqual(rooms[0]["polygon"], [[9, 9]])

    def test_ein_einzelnes_geschoss_passt_immer(self):
        eins = {"floors": [{"floor_level": "groundfloor", "rooms": [{"polygon": [[1, 1]]}]}]}
        self.assertEqual(richten.raeume_fuer(eins, "floor-0")[0]["polygon"], [[1, 1]])


class SicherungenWerdenNichtMitgemessen(unittest.TestCase):
    def test_der_dateifilter_kennt_die_endung(self):
        # Ein zweiter Lauf hat den Bestand VOR der Korrektur mitgemessen und
        # die alten Zahlen als offen gemeldet, weil die Sicherungen im selben
        # Ordner liegen und auch auf .json enden.
        with open(_pfad, encoding="utf-8") as datei:
            quelle = datei.read()
        self.assertIn(".vor-vorderseite-", quelle)


if __name__ == "__main__":
    unittest.main(verbosity=2)
