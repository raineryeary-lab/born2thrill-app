import importlib.util, pathlib, unittest
s=importlib.util.spec_from_file_location("builder",pathlib.Path(__file__).with_name("build-simplifier-render-plan.py")); b=importlib.util.module_from_spec(s); s.loader.exec_module(b)
class StairLowest(unittest.TestCase):
 def core(self, elements, marks=None):
  return b.annotation_stair_core({"elements":elements,"floor_alignment":marks or {}}, b.Frame(10,1000,1000),"groundfloor")
 def stair(self, level, role=None):
  return {"id":level,"type":"stairs","floor_level":level,"role":role,"points":[{"x":.2,"y":.2},{"x":.2,"y":.6}],"width":.09}
 def test_normal(self):
  self.assertEqual(self.core([self.stair("groundfloor")])["id"],"groundfloor")
 def test_basement_real_beats_ground_opening(self):
  marks={k:[{"x":0,"y":0},{"x":1,"y":1}] for k in ["basement","groundfloor"]}
  self.assertEqual(self.core([self.stair("groundfloor","opening"),self.stair("basement")],marks)["id"],"basement")
 def test_only_opening_is_not_a_stair(self):
  self.assertIsNone(self.core([self.stair("groundfloor","opening")]))
 def test_registration(self):
  marks={"basement":[{"x":0,"y":0},{"x":1,"y":1}],"groundfloor":[{"x":.1,"y":.1},{"x":.6,"y":.6}]}
  got=self.core([self.stair("basement")],marks)
  expected=b.Frame(10,1000,1000).point({"x":.2,"y":.2})
  self.assertEqual(got["path_mm"][0],list(expected))
if __name__=="__main__": unittest.main()
