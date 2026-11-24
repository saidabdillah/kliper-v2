"""Live browser path. Pass a short speech video via TEST_VIDEO (or use public trailer)."""
import json,os,socket,sys,subprocess,tempfile,time,urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright,expect
root=Path(__file__).resolve().parents[1]
with tempfile.TemporaryDirectory() as tmp:
 d=Path(tmp);f=Path(os.environ['TEST_VIDEO']) if os.getenv('TEST_VIDEO') else d/'trailer.mp4'
 if not f.exists():urllib.request.urlretrieve('https://media.w3.org/2010/05/sintel/trailer.mp4',f)
 with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
 url=f'http://127.0.0.1:{port}';server=subprocess.Popen([sys.executable,'-m','uvicorn','app:app','--host','127.0.0.1','--port',str(port)],cwd=root,env={**os.environ,'CLIP_DATA':str(d/'data'),'WHISPER_MODEL':'tiny','OLLAMA_MODEL':''},stdout=subprocess.DEVNULL)
 try:
  for i in range(80):
   try:urllib.request.urlopen(url,timeout=1).close();break
   except OSError:time.sleep(.15)
  with sync_playwright() as pw:
   b=pw.chromium.launch(executable_path=os.getenv('CHROME') or None,args=['--disable-dev-shm-usage']);q=b.new_page();errors=[];q.on('pageerror',lambda e:errors.append(str(e)));q.goto(url);q.locator('#sourceFile').set_input_files(f);q.locator('#uploadSource').click();q.get_by_label('Bahasa audio').select_option('en');q.get_by_role('button',name='Buat klip dengan AI').click();expect(q.locator('#detail')).to_contain_text('AI lokal · E5',timeout=600000);count=q.locator('.card').count();assert 0<count<=10;assert q.locator('.card').get_by_text('Unduh MP4').count()==0;q.get_by_role('button',name='Edit klip').first.click();q.locator('#words input').first.fill('Koreksi');start=float(q.get_by_label('Mulai (detik)',exact=True).input_value());end=float(q.get_by_label('Selesai (detik)',exact=True).input_value());q.get_by_label('Selesai (detik)',exact=True).fill(str(min(end,start+3)));q.get_by_label('Rasio',exact=True).select_option('1:1');
   with q.expect_download(timeout=90000) as result:q.locator('#mp4').click()
   artifact=result.value.path();streams=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(artifact)]))['streams'];assert (streams[0]['width'],streams[0]['height'])==(1080,1080);assert abs(float(streams[0]['duration'])-min(end-start,3))<.12;assert streams[1]['codec_name']=='aac';
   with q.expect_download() as sub:q.locator('#srt').click()
   assert 'Koreksi' in sub.value.path().read_text();assert not errors,errors;print(f'AI selected {count} clips; edited export: {streams[0]["width"]}x{streams[0]["height"]}, {streams[0]["duration"]} s, AAC; corrected subtitle verified.');b.close()
 finally:server.terminate();server.wait(timeout=10)
