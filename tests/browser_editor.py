"""Real Chromium + HTTP + FFmpeg on a private, synthetic project. No external video."""
import json, os, socket, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from studio import defaults,STYLES

def main():
 with tempfile.TemporaryDirectory() as temp:
    d=Path(temp);pid='b'*32;p=d/'data'/pid;p.mkdir(parents=True);c={'title':'Contoh studio','summary':'Satu dua tiga','score':72,'start':0,'end':4,'edit':defaults(0,4)}
    for f,v in [('meta',{'title':'Video uji','duration':5}),('status',{'state':'ready','message':'Selesai'}),('clips',{'clips':[c],'words':[[.1,.7,'Satu'],[1.1,1.7,'dua'],[2.1,2.7,'tiga'],[3.1,3.7,'empat']],'faces':[[0,.5],[2,.6]]})]: (p/(f+'.json')).write_text(json.dumps(v))
    subprocess.run(['ffmpeg','-loglevel','error','-f','lavfi','-i','testsrc2=s=320x180:r=30:d=5','-f','lavfi','-i','sine=duration=5','-c:v','libx264','-threads','1','-c:a','aac',str(p/'source.mp4')],check=True)
    for f in ('cover.jpg','wave.png'):subprocess.run(['ffmpeg','-loglevel','error','-i',str(p/'source.mp4'),'-frames:v','1','-threads','1',str(p/f)],check=True)
    with socket.socket() as s:s.bind(('127.0.0.1',0));port=s.getsockname()[1]
    url=f'http://127.0.0.1:{port}';server=subprocess.Popen([sys.executable,'-m','uvicorn','app:app','--host','127.0.0.1','--port',str(port)],cwd=ROOT,env={**os.environ,'CLIP_DATA':str(d/'data')},stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    try:
        for _ in range(80):
            try:urllib.request.urlopen(url,timeout=1).close();break
            except OSError:time.sleep(.15)
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,executable_path=os.environ.get('CHROME') or None,args=['--disable-dev-shm-usage']);page=browser.new_page(viewport={'width':1280,'height':880});errors=[];page.on('pageerror',lambda e:errors.append(str(e)));page.goto(url);page.locator('#url').fill('https://example.com/not-media');page.get_by_role('button',name='Periksa video').click();expect(page.locator('#notice')).to_contain_text('Gunakan tautan');page.get_by_role('button',name='Video uji').click();page.get_by_role('button',name='Edit klip').click();expect(page.locator('#editor')).to_be_visible();
            for style in STYLES:page.get_by_label('Gaya subtitle').select_option(style)
            for ratio in ('1:1','16:9','9:16'):page.get_by_label('Rasio',exact=True).select_option(ratio)
            page.locator('#safe').check();expect(page.locator('#guides')).to_be_visible();page.get_by_label('Ikuti wajah').uncheck();page.get_by_label('Pusat horizontal').fill('62');page.get_by_label('Perbesaran').fill('1.2');page.locator('#words input').first.fill('Koreksi');page.get_by_label('Mulai (detik)',exact=True).fill('0.05');page.get_by_label('Selesai (detik)',exact=True).fill('3.85');page.locator('#cut').click();page.get_by_label('Buang dari (dtk)').fill('1');page.get_by_label('Sampai (dtk)').fill('2');page.get_by_label('Sampai (dtk)').press('Tab');page.locator('#save').click();expect(page.locator('#notice')).to_contain_text('tersimpan');page.locator('#closeEdit').click();page.get_by_role('button',name='Edit klip').click();expect(page.locator('#words input').first).to_have_value('Koreksi');expect(page.get_by_label('Gaya subtitle')).to_have_value(STYLES[-1]);
            for width in (1280,375):
                page.set_viewport_size({'width':width,'height':850});assert page.evaluate('document.documentElement.scrollWidth<=innerWidth'),f'Overflow: {width}';expect(page.get_by_label('Rasio',exact=True)).to_be_visible()
            for ext in ('srt','vtt','mp4'):
                with page.expect_download(timeout=90000) as pending:page.locator('#'+ext).click()
                file=pending.value.path();assert file and file.stat().st_size>0
                if ext=='mp4':
                    streams=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-of','json',str(file)]))['streams'];assert [streams[0]['width'],streams[0]['height']]==[1080,1920];assert abs(float(streams[0]['duration'])-2.8)<.12;assert streams[1]['codec_name']=='aac'
                else:assert 'Koreksi' in file.read_text() and 'dua' not in file.read_text()
            page.locator('#closeEdit').click();page.locator('#back').click();page.once('dialog',lambda dlg:dlg.accept());page.get_by_role('button',name='Hapus',exact=True).click();expect(page.locator('#history')).to_contain_text('Belum ada proyek');assert not errors,errors;browser.close();print('Desktop/mobile Chromium passed: input error, editor, 6 styles, 3 ratios, framing, cuts, subtitles, persistence, MP4/SRT/VTT downloads, delete.')
    finally:server.terminate();server.wait(timeout=10)
if __name__=='__main__':main()
