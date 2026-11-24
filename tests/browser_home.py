"""Optional smoke test; set CHROME to a locally installed Chromium executable."""
import os, socket, subprocess, tempfile, time, urllib.request, sys
from pathlib import Path
with tempfile.TemporaryDirectory() as td:
 with socket.socket() as s:s.bind(('127.0.0.1',0)); port=s.getsockname()[1]
 url=f'http://127.0.0.1:{port}';env={**os.environ,'CLIP_DATA':td+'/data'};server=subprocess.Popen([sys.executable,'-m','uvicorn','app:app','--host','127.0.0.1','--port',str(port)],cwd=Path(__file__).resolve().parents[1],env=env,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
 try:
    for _ in range(50):
        try:urllib.request.urlopen(url,timeout=1).close();break
        except OSError:time.sleep(.1)
    html=subprocess.check_output([os.environ['CHROME'],'--headless','--disable-gpu','--disable-dev-shm-usage','--disable-background-networking','--no-first-run','--user-data-dir='+td+'/chrome','--virtual-time-budget=4000','--dump-dom',url],stderr=subprocess.DEVNULL,timeout=30).decode();assert 'Belum ada proyek. Mulai dengan satu tautan video.' in html;print('Homepage, JS and project list verified in Chromium.')
 finally:server.terminate();server.wait(timeout=10)
