import json, os, tempfile, unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
import app
from studio import defaults, STYLES, SIZES, ass, captions, spans, source

class EditorTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(); self.root=Path(self.tmp.name); self.use=patch.object(app,'ROOT',self.root); self.use.start(); self.addCleanup(self.tmp.cleanup); self.addCleanup(self.use.stop)
  self.c=TestClient(app.app,base_url='http://localhost:8765',headers={'X-Studio':'1'});self.pid='a'*32;self.p=self.root/self.pid;self.p.mkdir();self.base='/api/'+self.pid;self.e=defaults(1,5); self.words=[[1.1,1.5,'satu'],[2,2.5,'dua'],[4,4.5,'tiga']];app.write(self.p,'meta.json',{'title':'QA','duration':7});app.write(self.p,'clips.json',{'faces':[],'words':self.words,'clips':[{'edit':self.e}]});app.state(self.p,'ready','Selesai')
 def save(self):return self.c.post(self.base+'/clips/0/save',json=self.e)
 def test_save_reload_and_export(self):
  self.e.update(cuts=[[2,3]],edits={'2':'tiga!'});self.assertEqual(self.save().status_code,200);self.assertEqual(self.c.get(self.base+'/data').json()['clips'][0]['edit'],self.e)
  for ext in ('srt','vtt'):
   r=self.c.get(self.base+'/clips/0/text/'+ext);self.assertEqual(r.status_code,200);self.assertIn('tiga!',r.text);self.assertNotIn('dua',r.text);self.assertIn('00:00:02',r.text)
 def test_malformed_settings_leave_saved_data_intact(self):
  for k,v in [('ratio',[]),('end',0),('cuts',[[1,5]]),('edits',{'100':'bad'}),('fps',24),('primary','invalid')]:
   with self.subTest(k=k):
    self.e={**defaults(1,5),k:v};self.assertEqual(self.save().status_code,400);self.assertEqual(app.read(self.p,'clips.json')['clips'][0]['edit'],defaults(1,5))
 def test_lock_then_delete(self):
  with app.gate:self.assertEqual(self.c.delete(self.base).status_code,409)
  self.assertTrue(self.p.exists());self.assertEqual(self.c.delete(self.base).status_code,200);self.assertEqual(self.c.get(self.base+'/status').status_code,404)
 def test_all_templates_and_dimensions(self):
  for s in STYLES:
   for ratio,(W,H) in SIZES.items():
    with self.subTest(s=s,ratio=ratio):
     text=ass(self.words,[(1,5)],dict(self.e,style=s,ratio=ratio),W,H);self.assertIn('Dialogue:',text);self.assertIn(f'PlayResY: {H}',text)
 def test_normal_public_links(self):
  for u in ['https://youtu.be/12345678901','https://www.youtube.com/watch?v=12345678901','https://vimeo.com/12345','https://drive.google.com/file/d/abc123/view','https://example.com/video.mov']:
   self.assertIn(source(u)[0],('direct','platform'))
 def test_media_range(self):
  (self.p/'source.mp4').write_bytes(b'1234567890');r=self.c.get(self.base+'/file/source.mp4',headers={'Range':'bytes=2-4'});self.assertEqual((r.status_code,r.content),(206,b'345'))
