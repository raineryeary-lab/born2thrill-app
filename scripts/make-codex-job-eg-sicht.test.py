"""EG-Sicht copies retain real furniture but not structural furniture markers."""
import importlib.util
import os
import unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
os.environ.setdefault("FLOORPLAN_WORKBENCH_DATA_DIR",str(HERE))
spec=importlib.util.spec_from_file_location("make_codex_job",HERE/"make-codex-job.py")
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
class EgSichtTests(unittest.TestCase):
 def test_structural_copies_have_no_role(self):
  for name in ["floor1784967058512","floor-1","ground","stair-step-7.001","stair-podest-2.001"]:
   with self.subTest(name=name):
    self.assertEqual(mod._stamm("EG-Sicht-"+name),mod._stamm(name))
    self.assertIsNone(mod.rolle_fuer(mod._stamm("EG-Sicht-"+name)))
 def test_furniture_and_door_retained(self):
  self.assertEqual(mod._stamm("EG-Sicht-sofa-1"),"sofa")
  self.assertIsNotNone(mod.rolle_fuer(mod._stamm("EG-Sicht-sofa-1")))
  self.assertEqual(mod._stamm("EG-Sicht-wall-1-door"),"tuer")
  self.assertEqual(mod._bauteil("EG-Sicht-wall-1-door"),"EG-Sicht-wall-1-door")
 def test_original_identity_retained_when_grouping_parts(self):
  self.assertEqual(mod._bauteil("EG-Sicht-sofa-1-leg-0"),"EG-Sicht-sofa-1")
  self.assertEqual(mod._bauteil("EG-Sicht-desk-1-top"),"EG-Sicht-desk-1")
 def test_inventory_excludes_structure_not_furniture(self):
  names=["EG-Sicht-floor1784967058512","EG-Sicht-ground","EG-Sicht-stair-step-7.001","EG-Sicht-sofa-1","EG-Sicht-sofa-1-leg-0","EG-Sicht-sofa-2","sofa-1","EG-Sicht-wall-1-door"]
  before=list(names)
  self.assertEqual(mod._inventar(names),{"sofa":3})
  self.assertEqual(names,before)
 def test_normal_names_unchanged(self):
  for name,stem,part in [("sofa-1-leg-0","sofa","sofa-1"),("wall-1-door","tuer","wall-1-door"),("stair-step-7.001","stair","stair-step-7.001"),("stuff-19","stuff","stuff-19")]:
   self.assertEqual(mod._stamm(name),stem)
   self.assertEqual(mod._bauteil(name),part)
if __name__=="__main__":unittest.main()
