import http.client, ipaddress, json, os, re, socket, ssl, subprocess
from pathlib import Path
from urllib.parse import urlsplit,urljoin,unquote
from studio import source, recommend, defaults
LIMIT=1024**3

def fetch(url,path):
    for _ in range(5):
        u=urlsplit(url); host=u.hostname
        if not host or u.scheme!='https' or u.port not in (None,443) or u.username is not None or u.password or not re.fullmatch(r'[a-zA-Z0-9.-]+',host): raise ValueError('Alamat unduhan tidak diizinkan.')
        ips=[x[4][0] for x in socket.getaddrinfo(host,443,type=socket.SOCK_STREAM)]
        if not ips or any(not ipaddress.ip_address(ip).is_global or ipaddress.ip_address(ip).is_multicast for ip in ips):raise ValueError('Alamat jaringan privat ditolak.')
        conn=http.client.HTTPSConnection(host,timeout=30);conn._create_connection=lambda address,*a,**kw: socket.create_connection((ips[0],443),timeout=30)
        try:
            conn.request('GET',(u.path or '/')+('?' + u.query if u.query else ''),headers={'User-Agent':'ClipStudio/1.0'}); resp=conn.getresponse()
            if resp.status in (301,302,303,307,308):url=urljoin(url,resp.getheader('Location',''));continue
            if resp.status!=200:raise ValueError('Server sumber menolak unduhan (HTTP %s).'%resp.status)
            if int(resp.getheader('Content-Length') or 0)>LIMIT:raise ValueError('Batas file 1 GiB.')
            import time
            until=time.monotonic()+900; total=0
            with path.open('wb') as f:
                while block:=resp.read(512*1024):
                    total+=len(block)
                    if total>LIMIT or time.monotonic()>until:raise ValueError('Batas ukuran atau waktu unduh terlampaui.')
                    f.write(block)
            return
        finally:conn.close()
    raise ValueError('Terlalu banyak pengalihan URL.')

def cmd(args,limit=900):return subprocess.check_output(args,timeout=limit,stderr=subprocess.DEVNULL)
SAFE=['-protocol_whitelist','file','-format_whitelist','mov,matroska,webm']
def ingest(p,url,progress):
    kind,u=source(url); raw=p/'input.media'; title=unquote(urlsplit(u).path.split('/')[-1]);progress('Mengunduh video')
    try:
        if kind=='direct':fetch(u,raw)
        else:
            base=['yt-dlp','--ignore-config','--no-playlist','--no-cache-dir','--socket-timeout','20','--retries','1','--max-filesize','1G','--match-filter','!is_live & duration <=? 7200','-f','b[height<=1080]/bv[height<=1080]+ba/b','--no-warnings']; result=cmd(base+['--print','after_move:title','--no-simulate','-o',str(p/'input.%(ext)s'),'--',u],1200).decode().strip(); files=list(p.glob('input.*'))
            if len(files)!=1:raise ValueError('Gagal mengambil satu video publik. Periksa durasi dan akses tautan.')
            files[0].replace(raw);title=result.splitlines()[-1] if result else 'Video publik'
        if raw.stat().st_size>LIMIT:raise ValueError('Batas file 1 GiB.')
        return normalize(p,raw,title,progress)
    finally:
        for file in p.glob('input.*'):file.unlink(missing_ok=True)

def normalize(p,raw,title,progress):
    meta=json.loads(cmd(['ffprobe','-v','error',*SAFE,'-show_format','-show_streams','-of','json',str(raw)],45)); dur=float(meta['format']['duration']); tracks=meta['streams']; video=next((t for t in tracks if t['codec_type']=='video'),{})
    if not .1<dur<=7200 or not 0<video.get('width',0)*video.get('height',0)<=16777216: raise ValueError('Butuh video dengan audio, durasi maksimal 2 jam dan resolusi maksimal 16 megapiksel.')
    silent=not any(t['codec_type']=='audio' for t in tracks)
    extra=['-f','lavfi','-i','anullsrc=r=48000:cl=stereo'] if silent else []
    progress('Menyiapkan video editor');cmd(['ffmpeg','-y','-nostdin','-v','error',*SAFE,'-threads','2','-i',str(raw),*extra,'-t',str(dur),'-map','0:v:0','-map','1:a:0' if silent else '0:a:0','-vf',"scale='min(1920,iw)':'min(1920,ih)':force_original_aspect_ratio=decrease:force_divisible_by=2",'-c:v','libx264','-threads','2','-preset','ultrafast','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart','-fs',str(3*LIMIT),str(p/'source.mp4')],3600)
    actual=float(cmd(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',str(p/'source.mp4')]))
    if actual+1<dur:raise ValueError('Video melebihi batas berkas kerja.')
    cmd(['ffmpeg','-v','error','-i',str(p/'source.mp4'),'-frames:v','1','-vf','scale=480:-2','-threads','1',str(p/'cover.jpg')]);cmd(['ffmpeg','-v','error','-i',str(p/'source.mp4'),'-filter_complex','[0:a]aresample=1000,showwavespic=s=960x70:colors=0xc8f78f','-frames:v','1','-threads','1',str(p/'wave.png')]);return {'title':title[:200],'duration':actual}

def faces(p,duration):
    import cv2
    cv2.setNumThreads(1); cap=cv2.VideoCapture(str(p/'source.mp4')); model=cv2.CascadeClassifier(cv2.data.haarcascades+'haarcascade_frontalface_default.xml'); pts=[]; prev=.5
    try:
        for s in range(0,int(duration)+1,max(2,int(duration/240))):
            cap.set(cv2.CAP_PROP_POS_MSEC,1000*s); ok,frame=cap.read()
            if not ok:continue
            small=cv2.resize(frame,(320,max(20,int(320*frame.shape[0]/frame.shape[1])))); boxes=model.detectMultiScale(cv2.cvtColor(small,cv2.COLOR_BGR2GRAY),1.15,5)
            if len(boxes):
                x,y,w,h=max(boxes,key=lambda f:int(f[2])*int(f[3]));prev=round(.35*prev+.65*(x+w/2)/320,4)
            pts.append([s,prev])
    finally:cap.release()
    return pts

def analyze(p,meta,lang,target,ratio,progress):
    from faster_whisper import WhisperModel
    progress('Memuat model transkripsi'); model=WhisperModel(os.environ.get('WHISPER_MODEL','base'),device='cpu',compute_type='int8',cpu_threads=2); segments,_=model.transcribe(str(p/'source.mp4'),language=None if lang=='auto' else lang,word_timestamps=True,vad_filter=True,beam_size=2);words=[]; percent=-1
    for seg in segments:
        words.extend([round(w.start,3),round(w.end,3),w.word.strip()] for w in seg.words or [] if w.word.strip() and w.end>w.start)
        done=int(seg.end*100/meta['duration'])//5*5
        if done!=percent:progress('Mentranskripsi · %s%%'%min(100,done)); percent=done
    if not words:raise ValueError('Tidak ada ucapan yang terdeteksi.')
    del model,segments
    progress('Mencari momen dan posisi wajah'); clips=recommend(words,meta['duration'],target);pts=faces(p,meta['duration']);
    from ranking import semantic
    progress('Menilai kandidat klip');clips,method=semantic(clips,words)
    for c in clips:c['edit']={**defaults(c['start'],c['end']),'ratio':ratio}
    return dict(words=words,clips=clips,faces=pts,method=method)
