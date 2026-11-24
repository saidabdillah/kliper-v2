"use strict";
const accepted={video:'.mp4,.mov,.mkv,.webm',image:'.jpg,.jpeg,.png,.webp',audio:'.mp3,.m4a,.aac,.wav,.flac,.ogg'};
async function sendFile(path,file){
 if(!file)throw Error('Pilih file terlebih dahulu.');if(file.size>2000000000)throw Error('Batas file 2 GB.');
 const res=await fetch(path,{method:'POST',headers:{'X-Studio':'1','X-Filename':encodeURIComponent(file.name),'Content-Type':'application/octet-stream'},body:file});
 if(!res.ok){const j=await res.json().catch(()=>({}));throw Error(j.detail||`Unggah gagal (${res.status}).`)}return res.json();
}
$('uploadSource').onclick=act(async()=>{let b=$('uploadSource');b.disabled=true;try{msg('Mengunggah video…');const p=await sendFile('/api/upload',$('sourceFile').files[0]);await open(p.id)}finally{b.disabled=false}});
$('assetKind').onchange=()=>{$('assetFile').value='';$('assetFile').accept=accepted[$('assetKind').value]};
function outputTime(t){let from=e.start,total=0;t=Math.max(from,Math.min(e.end,t));for(let [a,b] of [...e.cuts].sort((x,y)=>x[0]-y[0])){a=Math.max(from,a);b=Math.min(t,b);if(b<=a)continue;total+=a-from;from=b}return total+Math.max(0,t-from)}
function placeAsset(a){const total=outputTime(e.end);if(e.layers.length>=12)throw Error('Maksimal 12 item pada timeline.');let t=Math.min(outputTime(v.currentTime),Math.max(0,total-.2));if(total<.1)throw Error('Periksa batas klip.');e.layers.push({asset:a.id,start:+t.toFixed(3),end:+Math.min(total,t+(a.duration||3)).toFixed(3),volume:a.kind==='audio'?.5:1});dirty=true;buildTracks();paint()}
$('addAsset').onclick=act(async()=>{const b=$('addAsset');b.disabled=true;let pid=id,editRef=e;try{msg('Menyiapkan aset…');const a=await sendFile(base()+'/assets?kind='+$('assetKind').value,$('assetFile').files[0]);if(view!=='editor'||id!==pid||e!==editRef)return;data.assets.push(a);placeAsset(a);$('assetFile').value='';msg('Aset ditambahkan. Simpan untuk mempertahankan susunan.')}finally{b.disabled=false}});
let previewTracks=[];
function buildTracks(){
 e.layers??=[];data.assets??=[];const p=$('trackList'),library=$('library'),o=$('overlays');previewTracks.forEach(n=>n.pause?.());previewTracks=[];clear(o);clear(p);clear(library);
 data.assets.forEach(a=>library.append(btn('+ '+a.name,()=>placeAsset(a))));let total=outputTime(e.end);p.append(el('p','Video utama · '+total.toFixed(2)+' detik','base-track'));
 e.layers.forEach((l,i)=>{let a=data.assets.find(x=>x.id===l.asset);if(!a)return;let n=el(a.kind==='image'?'img':a.kind==='video'?'video':'audio');n.src=media(a.file);n.hidden=true;if(a.kind!=='image'){n.preload='auto';n.muted=a.kind==='video';n.playsInline=true}o.append(n);previewTracks[i]=n;
 let row=el('div',undefined,'track-row');row.append(el('strong',(a.kind==='audio'?'Musik':a.kind==='image'?'Gambar':'B-roll')+' · '+a.name));let meter=el('div',undefined,'lane'),bar=el('i');meter.append(bar);row.append(meter);let fields=el('div',undefined,'track-fields');
 function position(){bar.style.left=(Math.min(1,l.start/(total||1))*100)+'%';bar.style.width=(Math.max(0,Math.min(1-l.start/(total||1),(l.end-l.start)/(total||1)))*100)+'%'}position();
 for(let [k,title] of [['start','Mulai trek'],['end','Akhir trek'],...(a.kind==='audio'?[['volume','Volume musik']]:[])]){let inp=el('input');inp.type='number';inp.min=0;inp.max=k==='volume'?1:total;inp.step='.01';inp.value=l[k];field(fields,title,inp);inp.oninput=()=>{l[k]=Number(inp.value);dirty=true;position();paint()}}
 fields.append(btn('Hapus trek',()=>{e.layers.splice(i,1);dirty=true;buildTracks();paint()}));row.append(fields);p.append(row)
 });if(!e.layers.length)p.append(el('p','Tambahkan B-roll, gambar, atau musik untuk membuat trek baru.','hint'));
}
function syncTracks(t){let pos=outputTime(t);(e.layers||[]).forEach((l,i)=>{let n=previewTracks[i];if(!n)return;let on=pos>=l.start&&pos<l.end&&t>=e.start&&t<e.end;n.hidden=!on;if(n.tagName==='IMG')return;if(!on){n.pause();return}n.volume=Math.max(0,Math.min(1,l.volume));let at=Math.max(0,pos-l.start);if(n.readyState&&Math.abs(n.currentTime-at)>(v.paused?.04:.18))n.currentTime=at;if(v.paused)n.pause();else if(n.paused)n.play().catch(()=>{})})}
v.addEventListener('pause',()=>previewTracks.forEach(n=>n.pause?.()));
