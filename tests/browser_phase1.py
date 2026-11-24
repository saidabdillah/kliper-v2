"""Browser uploads two real media assets, saves a timeline and downloads its render."""
import os,sys,tempfile,socket,subprocess,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as td:
 p=Path(td);ff=['ffmpeg','-loglevel','error','-f','lavfi','-i'];src=p/'studio.mp4';roll=p/'roll.mp4';song=p/'music.wav'
 for name,color in [(src,'black'),(roll,'red')]:subprocess.run(ff+[f'color=c={color}:s=160x90:r=30:d=2','-c:v','libx264','-threads','1',str(name)],check=True)
 subprocess.run(ff+['sine=duration=2',str(song)],check=True)
 with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
 url=f'http://127.0.0.1:{port}';server=subprocess.Popen([sys.executable,'-m','uvicorn','app:app','--host','127.0.0.1','--port',str(port)],cwd=root,env={**os.environ,'CLIP_DATA':str(p/'data')},stdout=subprocess.DEVNULL)
 try:
  for i in range(60):
   try:urllib.request.urlopen(url,timeout=1).close();break
   except OSError:time.sleep(.15)
  with sync_playwright() as pw:
   b=pw.chromium.launch(executable_path=os.getenv('CHROME') or None,args=['--disable-dev-shm-usage']);q=b.new_page(viewport={'width':1280,'height':840});errors=[];q.on('pageerror',lambda x:errors.append(str(x)));q.goto(url);q.locator('#sourceFile').set_input_files(src);q.locator('#uploadSource').click();q.get_by_text('Alternatif untuk video tanpa ucapan').click();q.get_by_role('button',name='Edit manual').click();expect(q.locator('#editor')).to_be_visible();
   for i,(kind,f) in enumerate([('video',roll),('audio',song)]):
    q.locator('#assetKind').select_option(kind);q.locator('#assetFile').set_input_files(f);q.locator('#addAsset').click();expect(q.locator('.track-row')).to_have_count(i+1);q.get_by_label('Mulai trek').nth(i).fill('0.5');q.get_by_label('Akhir trek').nth(i).fill('1.5')
   q.locator('#save').click();expect(q.locator('#notice')).to_contain_text('tersimpan');q.locator('#closeEdit').click();q.get_by_role('button',name='Edit klip').click();expect(q.locator('.track-row')).to_have_count(2);expect(q.get_by_label('Mulai trek').first).to_have_value('0.5');q.set_viewport_size({'width':375,'height':780});assert q.evaluate('document.documentElement.scrollWidth<=innerWidth');
   with q.expect_download(timeout=90000) as dl:q.locator('#mp4').click()
   assert dl.value.path().stat().st_size>1000;assert not errors,errors;b.close();print('Native phase-one browser export OK: uploaded video, B-roll, music, persistence and MP4.')
 finally:server.terminate();server.wait(timeout=10)
