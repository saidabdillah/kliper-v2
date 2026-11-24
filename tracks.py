"""Project-scoped assets and time ranges on the edited/output clock."""
import json,math,re,subprocess,uuid
from pathlib import Path
from pipeline import cmd

def catalog(p):return json.loads((p/'assets.json').read_text()) if (p/'assets.json').is_file() else []
def validate(p,layers,total):
    if not isinstance(layers,list) or len(layers)>12:raise ValueError('Maksimal 12 item timeline.')
    assets={a['id']:a for a in catalog(p)}
    for x in layers:
        if not isinstance(x,dict) or set(x)!={'asset','start','end','volume'} or not isinstance(x['asset'],str) or x['asset'] not in assets:raise ValueError('Aset tidak ada di proyek ini.')
        if not all(type(x[k]) in (float,int) and math.isfinite(x[k]) for k in ('start','end','volume')) or not 0<=x['start']<x['end']<=total+.001 or not 0<=x['volume']<=1:raise ValueError('Rentang atau volume layer tidak valid.')
        a=assets[x['asset']];
        if a['kind']!='image' and x['end']-x['start']>a['duration']+.051:raise ValueError('Rentang melebihi panjang aset.')

def normalize_asset(p,raw,name,kind):
    formats={'video':'mov,matroska,webm','image':'png_pipe,jpeg_pipe,webp_pipe','audio':'mp3,wav,mov,flac,ogg,matroska,webm,aac'};opt=['-protocol_whitelist','file','-format_whitelist',formats[kind]]
    info=json.loads(cmd(['ffprobe','-v','error',*opt,'-show_streams','-show_format','-of','json',str(raw)],30));track=next((s for s in info['streams'] if s['codec_type']==('audio' if kind=='audio' else 'video')),None)
    if not track or track.get('width',1)*track.get('height',1)>16777216:raise ValueError('Jenis atau resolusi aset tidak didukung.')
    duration=0 if kind=='image' else float(info['format'].get('duration',0));
    if kind!='image' and not 0<duration<=7200:raise ValueError('Durasi aset tidak valid.')
    aid=uuid.uuid4().hex;ext={'image':'png','video':'mp4','audio':'m4a'}[kind];fn=f'{aid}.{ext}';out=p/fn
    scale="scale='min(1920,iw)':'min(1920,ih)':force_original_aspect_ratio=decrease:force_divisible_by=2"
    args={'image':['-frames:v','1','-vf',scale,'-threads','1'],'video':['-map','0:v:0','-an','-t','600','-vf',scale,'-c:v','libx264','-threads','2','-preset','veryfast','-pix_fmt','yuv420p','-movflags','+faststart'],'audio':['-map','0:a:0','-vn','-t','600','-c:a','aac','-ar','48000','-ac','2']}[kind]
    try:cmd(['ffmpeg','-nostdin','-v','error',*opt,'-threads','1','-i',str(raw),*args,str(out)],1200)
    except Exception:out.unlink(missing_ok=True);raise
    return dict(id=aid,kind=kind,name=name,file=fn,duration=min(duration,600))

def compose(p,e,keep,W,H,inputs,filters):
    v,a='v','a';assets={x['id']:x for x in catalog(p)}
    for i,l in enumerate(e.get('layers',[])):
        asset=assets[l['asset']];kind=asset['kind'];idx=len(keep)+i;start=l['start'];end=l['end'];length=end-start
        inputs.extend((['-loop','1','-framerate',str(e['fps'])] if kind=='image' else [])+['-threads','1','-t',str(length),'-i',str((p/asset['file']).resolve())]);tag=f'layer{i}'
        if kind=='audio':
            filters.extend([f'[{idx}:a]asetpts=PTS-STARTPTS,volume={l["volume"]},adelay={round(1000*start)}:all=1[{tag}]',f'[{a}][{tag}]amix=inputs=2:duration=first:normalize=0[aud{i}]']);a=f'aud{i}'
        else:
            filters.extend([f'[{idx}:v]scale={W}:{H}:force_original_aspect_ratio=increase,crop={W}:{H},setsar=1,fps={e["fps"]},setpts=PTS-STARTPTS+{start}/TB[{tag}]',f"[{v}][{tag}]overlay=eof_action=pass:repeatlast=0:enable='gte(t,{start})*lt(t,{end})'[vis{i}]"]);v=f'vis{i}'
    filters.append(f'[{v}]ass=text.ass[final]');return a
