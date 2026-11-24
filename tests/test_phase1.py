import json,subprocess,tempfile,time,unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
import app

class PhaseOne(unittest.TestCase):
 def test_upload_layer_mix_export(self):
    with tempfile.TemporaryDirectory() as tmp,patch.object(app,'ROOT',Path(tmp)):
        p=Path(tmp);c=TestClient(app.app,base_url='http://localhost:8765',headers={'X-Studio':'1'});ff=['ffmpeg','-v','error','-y'];src=p/'base.mp4';roll=p/'roll.mp4';music=p/'song.wav'
        for dst,col in [(src,'black'),(roll,'red')]:subprocess.run(ff+['-f','lavfi','-i',f'color=c={col}:s=160x90:r=30:d=3','-c:v','libx264','-threads','1',str(dst)],check=True)
        subprocess.run(ff+['-f','lavfi','-i','sine=frequency=550:duration=3',str(music)],check=True)
        def up(url,path):return c.post(url,content=path.read_bytes(),headers={'X-Filename':path.name,'Content-Type':'application/octet-stream'})
        res=up('/api/upload',src);self.assertEqual(res.status_code,200,res.text);base='/api/'+res.json()['id']
        def wait(expected):
            for _ in range(300):
                s=c.get(base+'/status').json()
                if s['state']!='busy':break
                time.sleep(.05)
            self.assertEqual(s['state'],expected,s)
        wait('preview');self.assertEqual(c.post(base+'/manual').status_code,200);e=c.get(base+'/data').json()['clips'][0]['edit'];assets=[]
        for file,kind in [(roll,'video'),(music,'audio')]:
            res=up(base+'/assets?kind='+kind,file);self.assertEqual(res.status_code,200,res.text);assets.append(res.json());
        e['layers']=[{'asset':a['id'],'start':1,'end':2.5,'volume':1} for a in assets];cp=base+'/clips/0';self.assertEqual(c.post(cp+'/save',json=e).status_code,200);self.assertEqual(c.post(cp+'/render').status_code,200);wait('ready');out=p/'export.mp4';out.write_bytes(c.get(base+'/file/clip-0.mp4').content)
        def sample(t):return subprocess.check_output(ff+['-ss',t,'-i',str(out),'-vf','scale=1:1,format=rgb24','-frames:v','1','-threads','1','-f','rawvideo','-'])
        self.assertLess(max(sample('0.4')),25);self.assertGreater(sample('1.5')[0],180)
        import array
        def peak(t):return max(map(abs,array.array('h',subprocess.check_output(ff+['-ss',t,'-i',str(out),'-t','0.2','-vn','-ac','1','-f','s16le','-']))))
        self.assertLess(peak('0.4'),10);self.assertGreater(peak('1.5'),100);self.assertEqual(c.delete(base).status_code,200)
