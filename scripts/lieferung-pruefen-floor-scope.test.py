from pathlib import Path
import unittest,importlib.util
P=Path(__file__).with_name('lieferung-pruefen.py')
s=importlib.util.spec_from_file_location('verifier',P);m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class FloorScope(unittest.TestCase):
 def fixture(self):
  maps=[];images=[]
  for floor,x in [('ground',100),('upper',900)]:
   maps.append({'file':'OBJEKTKARTE-'+floor+'.png','markers':[{'n':1,'name':'teppich-0','px':[x,100],'farbe':'bleibt'}]})
   for style in ['warm','dark']:
    images.append({'filename':floor+'-'+style+'.png','source_blend':floor+'.blend','marker_check':[{'n':1,'name':'teppich-0','status':'sichtbar','bei':[x,100]}]})
  return {'beleg_verlangt':True,'object_map':maps},{'images':images}
 def test_identical_names_on_different_floors_are_independent(self):
  job,c=self.fixture();self.assertEqual(m.verschobene_objekte(job,c)[0],[])
 def test_real_same_floor_displacement_still_fails(self):
  job,c=self.fixture();c['images'][1]['marker_check'][0]['bei']=[600,600]
  failures=m.verschobene_objekte(job,c)[0]
  self.assertEqual(len(failures),1,failures);self.assertTrue(failures[0].startswith('ground-dark.png:'))
if __name__=='__main__':unittest.main()
