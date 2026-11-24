"""Optional end-to-end check. Downloads a public trailer and model to the test machine."""
import sys,os,time,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
with tempfile.TemporaryDirectory() as path:
 os.environ['CLIP_DATA']=path
 from fastapi.testclient import TestClient
 from app import app
 c=TestClient(app,base_url='http://localhost:8765',headers={'X-Studio':'1'})
 def req(method,path,**kw):
    r=c.request(method,path,**kw);r.raise_for_status();return r
 def wait(base,expected):
    before=time.monotonic();last=None
    while time.monotonic()-before<1500:
        s=req('GET',base+'/status').json()
        if s['message']!=last: print(s,flush=True);last=s['message']
        if s['state']!='busy':assert s['state']==expected,s;return
        time.sleep(1)
    raise TimeoutError('Job not finished')
 pid=req('POST','/api/projects',json={'url':os.environ.get('TEST_URL','https://media.w3.org/2010/05/sintel/trailer.mp4')}).json()['id'];base='/api/'+pid;wait(base,'preview');req('POST',base+'/analyze',json={'ratio':'9:16','lang':'en','target':30});wait(base,'ready');d=req('GET',base+'/data').json();assert d['words'] and d['clips'];print('Real transcript:',d['words'][:4],flush=True);e=d['clips'][0]['edit'];e['end']=min(e['end'],e['start']+3); e['style']='Karaoke Pill Box';e['edits']={str(next(i for i,w in enumerate(d['words']) if w[0]>=e['start'])):'Uji'};cp=base+'/clips/0';req('POST',cp+'/save',json=e);assert 'Uji' in req('GET',cp+'/text/srt').text;assert req('GET',cp+'/text/vtt').text.startswith('WEBVTT');file=req('POST',cp+'/render').json()['file'];wait(base,'ready');r=req('GET',base+'/file/'+file);assert b'ftyp' in r.content[:30];print('MP4',len(r.content),'bytes;',len(d['clips']),'clips;',len(d['words']),'words.');req('DELETE',base);assert c.get(base+'/status').status_code==404
