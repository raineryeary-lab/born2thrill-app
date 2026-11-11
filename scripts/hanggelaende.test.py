import ast, math, pathlib, unittest
HERE=pathlib.Path(__file__).parent
ns={"math":math}
for filename in ["build-simplifier-render-plan.py","render-exterior.py"]:
 tree=ast.parse((HERE/filename).read_text(encoding="utf8"))
 funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in {"gelaende_aus_flaechen","gelaende_hoehe","gelaende_warnungen","gelaende_gitter"}]
 exec(compile(ast.Module(body=funcs,type_ignores=[]),filename,"exec"),ns)
class Terrain(unittest.TestCase):
 def terrain(self):
  areas=[{"level":"groundfloor","points_mm":[[0,-1000],[1000,-1000],[1000,-2000]],"base_z_m":2.75},{"level":"basement","points_mm":[[0,11000],[1000,11000],[1000,12000]],"base_z_m":0}]
  return ns["gelaende_aus_flaechen"](areas,None,["basement","groundfloor"])
 def test_two_levels(self):
  g=self.terrain(); self.assertEqual(g["art"],"hang"); self.assertEqual(g["richtung"],[0.,1.]); self.assertEqual(g["oben"],"groundfloor")
 def test_flat(self):
  f=ns["gelaende_aus_flaechen"]; self.assertEqual(f([],None,["groundfloor"]),{"art":"eben"}); self.assertEqual(f([{"level":"upperfloor"}],None,["groundfloor","upperfloor"]),{"art":"eben"})
 def test_plateaus_and_linear(self):
  f=ns["gelaende_hoehe"]; g=self.terrain()
  for y,z in [(-.3,2.75),(0,2.75),(5,1.375),(10,0),(10.3,0)]: self.assertAlmostEqual(f(5,y,g,(0,0,10,10)),z)
 def test_offset_driveway_keeps_entire_facade_plateau(self):
  g=self.terrain(); g["richtung"]=[.23,.973]
  for x in (0,5,10):
   self.assertAlmostEqual(ns["gelaende_hoehe"](x,-.3,g,(0,0,10,10)),2.75)
   self.assertAlmostEqual(ns["gelaende_hoehe"](x,10.3,g,(0,0,10,10)),0)
 def test_flat_height_unchanged(self):
  self.assertEqual(ns["gelaende_hoehe"](0,0,{"art":"eben"},(0,0,10,10)),-.16)
 def test_warnings(self):
  warnings=ns["gelaende_warnungen"](self.terrain(),(0,0,10,10),[{"id":"buried","x":5,"y":0,"z":1}], [{"id":"slope","base_z_m":2.75,"points_mm":[[5000,5000]]}])
  self.assertEqual(len(warnings),2)
 def test_no_false_warnings(self):
  self.assertEqual(ns["gelaende_warnungen"](self.terrain(),(0,0,10,10),[{"id":"clear","x":5,"y":10,"z":0}],[]),[])
 def test_mesh_omits_house(self):
  verts,faces=ns["gelaende_gitter"](self.terrain(),(0,0,10,10),[[(0,0),(10,0),(10,10),(0,10)]],1,.5)
  self.assertTrue(faces)
  for face in faces:
   x=sum(verts[i][0] for i in face)/len(face); y=sum(verts[i][1] for i in face)/len(face)
   self.assertFalse(0<x<10 and 0<y<10)
if __name__=="__main__": unittest.main()
