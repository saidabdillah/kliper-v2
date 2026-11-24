import ipaddress, json, math, re, subprocess, tempfile
from pathlib import Path
from urllib.parse import urlsplit, parse_qs

SIZES={'9:16':(1080,1920),'1:1':(1080,1080),'16:9':(1920,1080)}
STYLES=['Hormozi Bold','Karaoke Pill Box','Minimalist Clean','Neon Glow','Classic Cinema','Dual-Tone Keyword']
HOOK=set('kenapa mengapa cara rahasia jangan ternyata penting bagaimana kunci why how secret never mistake what stop'.split())
def source(url):
    u=urlsplit(url); h=u.hostname or ''; path=u.path
    if u.scheme!='https' or u.username is not None or u.password or u.port not in (None,443) or not re.fullmatch(r'[a-z0-9.-]+',h) or '.' not in h or len(url)>2048 or any(ord(c)<33 for c in url): raise ValueError('Gunakan tautan HTTPS publik.')
    if h in ('youtu.be','youtube.com','www.youtube.com','m.youtube.com'):
        i=(parse_qs(u.query).get('v') or [''])[0] if path=='/watch' else path.split('/')[-1]
        if re.fullmatch(r'[A-Za-z0-9_-]{11}',i): return 'platform','https://www.youtube.com/watch?v='+i
    if h in ('vimeo.com','www.vimeo.com') and re.fullmatch(r'/\d+/?',path): return 'platform','https://vimeo.com/'+path.strip('/')
    if h=='drive.google.com':
        m=re.fullmatch(r'/file/d/([\w-]+)(?:/view)?/?',path)
        if m:return 'platform','https://drive.google.com/file/d/'+m[1]+'/view'
    if path.lower().endswith(('.mov','.mp4')) and not h.endswith(('.local','.localhost','.internal')):
        try: ip=ipaddress.ip_address(h)
        except ValueError: pass
        else:
            if not ip.is_global:raise ValueError('Alamat internal ditolak.')
        return 'direct',url
    raise ValueError('Gunakan tautan video YouTube, Vimeo, Drive atau MP4/MOV langsung.')

def defaults(a,b): return dict(start=a,end=b,cuts=[],ratio='9:16',style=STYLES[0],primary='#FFFFFF',accent='#FFD60A',size=68,y=73,outline=3,pan=50,zoom=1,auto=True,fps=30,edits={},layers=[])
def spans(a,b,cuts):
    keep=[]; pos=a
    for x,y in sorted(cuts):
        x=max(a,x);y=min(b,y)
        if y<=x: continue
        if x>pos: keep.append((pos,x))
        pos=max(pos,y)
    if pos<b:keep.append((pos,b))
    return keep

def mapped(words,keep):
    t=0
    for a,b in keep:
        for x,y,text in words:
            if x>=b: break
            if y>a and x<b: yield (t+max(a,x)-a,t+min(b,y)-a,text)
        t+=b-a

def stamp(v,mode):
    unit=100 if mode=='ass' else 1000; s,ms=divmod(max(0,round(v*unit)),unit); h,s=divmod(s,3600);m,s=divmod(s,60)
    if mode=='ass':return f'{h}:{m:02}:{s:02}.{ms:02}'
    return f'{h:02}:{m:02}:{s:02}'+(',' if mode=='srt' else '.')+f'{ms:03}'

def captions(words,keep,mode):
    lines=['WEBVTT',''] if mode=='vtt' else []
    for n,(a,b,t) in enumerate(mapped(words,keep),1):
        if mode=='srt':lines.append(str(n))
        lines.extend([stamp(a,mode)+' --> '+stamp(b,mode),t,''])
    return '\n'.join(lines)+'\n'

def recommend(words,duration,target):
    candidates=[]; i=0; goal=target*.78
    while i<len(words):
        a=words[i][0]; j=i+1
        while j<len(words) and words[j][1]-a<=target and not (words[j-1][1]-a>=goal and words[j-1][2].endswith(('.','!','?'))):j+=1
        chunk=words[i:j]; b=min(duration,chunk[-1][1]+.15); text=' '.join(x[2] for x in chunk); tokens=re.findall(r'\w+',text.lower()); score=min(99,45+min(15,len(set(tokens)))+min(20,sum(t in HOOK for t in tokens)*5)+8*('?' in text)+6*('!' in text))
        candidates.append(dict(title=' '.join(text.split()[:9]),summary=' '.join(text.split()[:32]),score=score,start=a,end=b));i=j
    return sorted(candidates,key=lambda c:-c['score'])[:15]

def color(s): return '&H'+s[5:7]+s[3:5]+s[1:3]+'&'
def ass(words,keep,e,W,H):
    k=STYLES.index(e['style']); font='DejaVu Serif' if k==4 else 'DejaVu Sans'; size=int(e['size']); p=color(e['primary']); hi=color(e['accent']); border=3 if k in (1,2) else 1
    header=f'''[Script Info]
ScriptType: v4.00+
PlayResX: {W}
PlayResY: {H}
WrapStyle: 0
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: C,{font},{size},&H00FFFFFF,&H00FFFFFF,&H00111111,&H80111111,{-1 if k in (0,1,3,5) else 0},0,0,0,100,100,0,0,{border},{e['outline']},1,5,35,35,10,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
    lines=[]; items=list(mapped(words,keep)); n=4
    for i in range(0,len(items),n):
        group=items[i:i+n]; static=k in (2,4)
        for j,(a,b,_) in enumerate(group[:1] if static else group):
            tokens=[]
            for idx,(_,__,text) in enumerate(group):
                text=text.translate(str.maketrans({'{':'(', '}':')','\\':'／','\n':' '})); text=text.upper() if k==0 else text
                tag=r'\1c'+p
                if idx==j and not static:
                    tag+=r'\1c'+hi
                    if k==0:tag+=r'\fscx112\fscy112\t(0,160,\fscx100\fscy100)'
                    if k==1:tag+=r'\3c'+hi+r'\1c&HFFFFFF&'
                    if k==3:tag+=r'\blur4\3c'+hi
                if k==5 and text.strip('?!.,').lower() in HOOK:tag+=r'\b1\frz3\1c'+hi
                tokens.append('{'+tag+'}'+text+r'{\rC}')
            tag=rf'\pos({W//2},{int(H*e["y"]/100)})'+(r'\fad(80,50)' if k==2 else '')
            lines.append(f'Dialogue: 0,{stamp(a,"ass")},{stamp(group[-1][1] if static else b,"ass")},C,,0,0,0,,{{{tag}}}'+ ' '.join(tokens))
    return header+'\n'.join(lines)+'\n'

def render(p,e,words,out,faces):
    keep=spans(e['start'],e['end'],e['cuts']); W,H=SIZES[e['ratio']]; filters=[]; inputs=[]; links=''; fps=e['fps']; zoom=e['zoom']
    with tempfile.TemporaryDirectory(dir=p) as td:
        Path(td,'text.ass').write_text(ass(words,keep,e,W,H),encoding='utf8')
        for i,(a,b) in enumerate(keep):
            inputs+=['-ss',str(a),'-t',str(b-a),'-threads','1','-i',str((p/'source.mp4').resolve())]; pan=str(e['pan']/100)
            if e['auto'] and faces:
                from bisect import bisect_right
                idx=max(0,bisect_right([f[0] for f in faces],a)-1); pts=[f for f in faces[idx:] if f[0]<b]; pts=pts[::max(1,math.ceil(len(pts)/24))]
                if pts:
                    pan=str(pts[-1][1]);
                    for j in range(len(pts)-2,-1,-1):pan=f'if(lt(t,{max(0,pts[j+1][0]-a):.3f}),{pts[j][1]:.4f},{pan})'
            filters.append(f"[{i}:v]setpts=PTS-STARTPTS,crop=w='trunc(min(iw,ih*{W}/{H})/{zoom}/2)*2':h='trunc(min(ih,iw*{H}/{W})/{zoom}/2)*2':x='clip(iw*({pan})-ow/2,0,iw-ow)':y=(ih-oh)/2,scale={W}:{H},setsar=1,fps={fps}[v{i}]")
            filters.append(f'[{i}:a]asetpts=PTS-STARTPTS,apad,atrim=duration={b-a}[a{i}]');links+=f'[v{i}][a{i}]'
        from tracks import compose
        filters.append(links+f'concat=n={len(keep)}:v=1:a=1[v][a]'); audio=compose(p,e,keep,W,H,inputs,filters); subprocess.run(['ffmpeg','-nostdin','-y','-v','error',*inputs,'-filter_complex_threads','1','-filter_complex',';'.join(filters),'-map','[final]','-map',f'[{audio}]','-c:v','libx264','-threads','2','-preset','veryfast','-pix_fmt','yuv420p','-c:a','aac','-movflags','+faststart',str(out.resolve())],cwd=td,check=True,timeout=3600)
