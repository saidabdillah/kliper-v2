import json, math, os, re, shutil, threading, traceback, uuid
from pathlib import Path
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pipeline import ingest, analyze, normalize
from tracks import catalog,validate as validate_layers,normalize_asset
from starlette.concurrency import run_in_threadpool
from urllib.parse import unquote
import tempfile, subprocess
from studio import defaults
from studio import source, render, captions, spans, SIZES, STYLES
ROOT=Path(os.getenv('CLIP_DATA','data')).resolve(); ROOT.mkdir(parents=True,exist_ok=True); HERE=Path(__file__).resolve().parent; gate=threading.Lock()
app=FastAPI(docs_url=None,redoc_url=None,openapi_url=None)
app.add_middleware(TrustedHostMiddleware,allowed_hosts=['localhost','127.0.0.1'])
@app.middleware('http')
async def guard(req:Request,next_call):
    if req.method not in ('GET','HEAD'):
        if req.headers.get('x-studio')!='1':return Response(status_code=403)
        limit=2_000_000_000 if req.url.path=='/api/upload' or re.fullmatch(r'/api/[0-9a-f]{32}/assets',req.url.path) else 512000
        if req.headers.get('transfer-encoding') or not req.headers.get('content-length','0').isdigit() or int(req.headers.get('content-length',0))>limit:return Response(status_code=413)
    resp=await next_call(req); resp.headers.update({'X-Content-Type-Options':'nosniff','Referrer-Policy':'no-referrer','Content-Security-Policy':"default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data:; media-src 'self'; frame-ancestors 'none'; base-uri 'none'; object-src 'none'"}); return resp
@app.exception_handler(ValueError)
async def invalid(_,exc):return JSONResponse({'detail':str(exc)[:220]},400)

def write(p,name,obj):
    tmp=p/(name+'.tmp');tmp.write_text(json.dumps(obj,ensure_ascii=False,allow_nan=False),encoding='utf8');tmp.replace(p/name)
def read(p,name):return json.loads((p/name).read_text(encoding='utf8'))
def project(pid):
    if not re.fullmatch('[0-9a-f]{32}',pid) or not (ROOT/pid/'status.json').is_file():raise HTTPException(404,'Proyek tidak ditemukan.')
    return ROOT/pid
def state(p,s,msg):write(p,'status.json',dict(state=s,message=msg))
def lock():
    if not gate.acquire(False):raise HTTPException(409,'Server sedang memproses tugas lain.')
def work(p,fn,success):
    def task():
        try:fn(lambda msg:state(p,'busy',msg));state(p,success,'Selesai')
        except Exception as ex:
            traceback.print_exc();state(p,'error',str(ex)[:180] if isinstance(ex,ValueError) else 'Proses gagal. Periksa akses video, koneksi, kapasitas disk, dan log server.')
        finally:gate.release()
    state(p,'busy','Menunggu proses');threading.Thread(target=task,daemon=True).start()
for f in ROOT.glob('*/status.json'):
    if read(f.parent,f.name)['state']=='busy':state(f.parent,'error','Proses terhenti saat server dimulai ulang.')
@app.get('/')
def home():return FileResponse(HERE/'web/index.html')
@app.get('/api/projects')
def projects():return [dict(id=f.parent.name,title=read(f.parent,'meta.json')['title'] if (f.parent/'meta.json').exists() else 'Video baru',**read(f.parent,f.name)) for f in sorted(ROOT.glob('*/status.json'),key=lambda f:-f.stat().st_mtime)]
@app.post('/api/projects')
def create(body:dict):
    url=body.get('url');
    if not isinstance(url,str):raise ValueError('URL wajib diisi.')
    source(url);lock();p=ROOT/uuid.uuid4().hex
    try:
        if shutil.disk_usage(ROOT).free<2*1024**3:raise ValueError('Ruang kosong kurang dari 2 GiB.')
        p.mkdir();work(p,lambda prog:write(p,'meta.json',ingest(p,url,prog)),'preview')
    except Exception:gate.release();raise
    return {'id':p.name}
@app.get('/api/{pid}/status')
def status(pid:str):return read(project(pid),'status.json')
@app.get('/api/{pid}/data')
def data(pid:str):
    p=project(pid);return {'assets':catalog(p),**(read(p,'meta.json') if (p/'meta.json').exists() else {}),**(read(p,'clips.json') if (p/'clips.json').exists() else {})}
@app.post('/api/{pid}/analyze')
def analyze_route(pid:str,body:dict):
    p=project(pid);lang=body.get('lang');target=body.get('target');ratio=body.get('ratio');
    if lang not in ('auto','id','en') or target not in (30,45,60) or not isinstance(ratio,str) or ratio not in SIZES:raise ValueError('Pilihan proses tidak valid.')
    lock()
    try:
        if not (p/'meta.json').exists() or (p/'clips.json').exists():raise ValueError('Video tidak siap untuk analisis baru.')
        work(p,lambda prog:write(p,'clips.json',analyze(p,read(p,'meta.json'),lang,target,ratio,prog)),'ready')
    except Exception:gate.release();raise
    return {'ok':True}

def clipdata(p,i):
    if not (p/'clips.json').exists():raise HTTPException(409,'Klip belum siap.')
    d=read(p,'clips.json');
    if not 0<=i<len(d['clips']):raise HTTPException(404,'Klip tidak ditemukan.')
    return d,d['clips'][i]
def valid(e,d,du):
    def num(x,a,b):return type(x) in (float,int) and math.isfinite(x) and a<=x<=b
    if set(e)!=set(d['clips'][0]['edit']) or not all(num(e[k],a,b) for k,a,b in [('start',0,du),('end',0,du),('size',20,130),('y',5,95),('outline',0,12),('pan',0,100),('zoom',1,3)]) or not .1<=e['end']-e['start']<=600:raise ValueError('Durasi klip harus 0,1–600 detik. Periksa kontrol editor.')
    if not isinstance(e['ratio'],str) or e['ratio'] not in SIZES or e['style'] not in STYLES or e['fps'] not in (30,60) or type(e['auto'])!=bool or not all(isinstance(e[k],str) and re.fullmatch('#[0-9A-Fa-f]{6}',e[k]) for k in ('accent','primary')):raise ValueError('Gaya tidak valid.')
    if not isinstance(e['cuts'],list) or len(e['cuts'])>12 or any(not isinstance(c,list) or len(c)!=2 or not all(num(x,0,du) for x in c) or c[0]>=c[1] for c in e['cuts']) or sum(b-a for a,b in spans(e['start'],e['end'],e['cuts']))<.1:raise ValueError('Potongan tidak valid. Sisakan minimal 0,1 detik.')
    if not isinstance(e['edits'],dict) or any(not k.isdecimal() or len(k)>8 or int(k)>=len(d['words']) or not isinstance(v,str) or not v.strip() or len(v)>80 or not v.isprintable() for k,v in e['edits'].items()):raise ValueError('Koreksi kata tidak valid.')
def corrected(d,e):return [[a,b,e['edits'].get(str(n),t)] for n,(a,b,t) in enumerate(d['words'])]
@app.post('/api/{pid}/clips/{i}/save')
def save(pid:str,i:int,body:dict):
    p=project(pid);lock()
    try:
        d,c=clipdata(p,i);valid(body,d,read(p,'meta.json')['duration']);validate_layers(p,body.get('layers',[]),sum(b-a for a,b in spans(body['start'],body['end'],body['cuts'])));c['edit']=body;write(p,'clips.json',d)
    finally:gate.release()
    return {'ok':True}
@app.post('/api/{pid}/clips/{i}/render')
def export(pid:str,i:int):
    p=project(pid);lock()
    try:
        d,c=clipdata(p,i); e=c['edit'];name=f'clip-{i}.mp4'
        def job(prog):
            prog('Merender MP4 dengan subtitle');tmp=p/'render.tmp.mp4'
            try:render(p,e,corrected(d,e),tmp,d['faces']);tmp.replace(p/name)
            finally:tmp.unlink(missing_ok=True)
        work(p,job,'ready');return {'file':name}
    except Exception:gate.release();raise
@app.get('/api/{pid}/clips/{i}/text/{ext}')
def subtitle(pid:str,i:int,ext:str):
    if ext not in ('srt','vtt'):raise HTTPException(404)
    d,c=clipdata(project(pid),i);e=c['edit'];return Response(captions(corrected(d,e),spans(e['start'],e['end'],e['cuts']),ext),media_type='text/plain',headers={'Content-Disposition':f'attachment; filename="clip-{i+1}.{ext}"'})
@app.get('/api/{pid}/file/{name}')
def file(pid:str,name:str):
    p=project(pid)
    if not (re.fullmatch(r'(source\.mp4|cover\.jpg|wave\.png|clip-\d+\.mp4)',name) or name in {a['file'] for a in catalog(p)}) or not (p/name).is_file():raise HTTPException(404)
    return FileResponse(p/name,filename=name if name.startswith('clip-') else None)
@app.delete('/api/{pid}')
def delete(pid:str):
    p=project(pid);lock()
    try:shutil.rmtree(p)
    finally:gate.release()
    return {'ok':True}
async def receive(req,path,allowed):
    name=Path(unquote(req.headers.get('x-filename','')).replace('\\','/')).name[:180]
    if Path(name).suffix.lower() not in allowed:raise ValueError('Format file tidak didukung.')
    total=int(req.headers.get('content-length',0))
    if not 0<total<=2_000_000_000:raise HTTPException(413,'Maksimal 2 GB per berkas.')
    if shutil.disk_usage(path.parent).free < total+300_000_000:raise HTTPException(507,'Ruang disk tidak cukup.')
    size=0
    with path.open('wb') as f:
        async for chunk in req.stream():
            size+=len(chunk)
            if size>total:raise HTTPException(413,'Ukuran tidak sesuai.')
            f.write(chunk)
    if size!=total:raise ValueError('Pengiriman tidak lengkap.')
    return name

@app.post('/api/upload')
async def upload(req:Request):
    lock();p=ROOT/uuid.uuid4().hex;handed_off=False
    try:
        p.mkdir();raw=p/'input.media';name=await receive(req,raw,{'.mp4','.mov','.mkv','.webm'})
        def prepare(prog):
            try:write(p,'meta.json',normalize(p,raw,name,prog))
            finally:raw.unlink(missing_ok=True)
        work(p,prepare,'preview');handed_off=True;return {'id':p.name}
    finally:
        if not handed_off:
            shutil.rmtree(p,ignore_errors=True);gate.release()

@app.post('/api/{pid}/manual')
def manual(pid:str):
    p=project(pid);lock()
    try:
        if not (p/'meta.json').exists() or (p/'clips.json').exists():raise ValueError('Proyek bukan proyek baru.')
        meta=read(p,'meta.json');end=min(60,meta['duration']);c=dict(title=meta['title'],summary='Klip manual — geser batas di editor.',start=0,end=end,score=None,edit=defaults(0,end));write(p,'clips.json',dict(clips=[c],words=[],faces=[],method='Pilihan manual'));state(p,'ready','Selesai');return {'ok':True}
    finally:gate.release()

@app.post('/api/{pid}/assets')
async def add_asset(pid:str,kind:str,req:Request):
    p=project(pid);allowed={'video':{'.mp4','.mov','.mkv','.webm'},'image':{'.png','.jpg','.jpeg','.webp'},'audio':{'.mp3','.m4a','.aac','.wav','.flac','.ogg'}}
    if kind not in allowed:raise ValueError('Jenis aset tidak dikenal.')
    lock()
    try:
        records=catalog(p)
        if len(records)>=48:raise ValueError('Maksimal 48 aset per proyek.')
        with tempfile.TemporaryDirectory(dir=p) as tmp:
            raw=Path(tmp)/'incoming';name=await receive(req,raw,allowed[kind]);a=await run_in_threadpool(normalize_asset,p,raw,name,kind)
        write(p,'assets.json',records+[a]);return a
    except (subprocess.SubprocessError,KeyError):raise ValueError('Aset gagal dibaca. Periksa codec atau format file.') from None
    finally:gate.release()

app.mount('/assets',StaticFiles(directory=HERE/'web'),name='assets')
