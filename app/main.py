import base64
import secrets
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, HttpUrl, Field
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload
from .config import APP_PASSWORD, COLLECTOR
from .db import Base, engine, get_db
from .models import Video, Snapshot
from .collectors.official import OfficialCollector
from .collectors.public import PublicExtractor
from .hooks import analyze_hook

Base.metadata.create_all(bind=engine)
app = FastAPI(title="TikInsight Personal", version="1.0.0")

@app.middleware("http")
async def protect(request: Request, call_next):
    if request.url.path == "/api/health" or not APP_PASSWORD:
        return await call_next(request)
    try:
        scheme, encoded = request.headers.get("authorization", "").split(" ", 1)
        user, password = base64.b64decode(encoded).decode().split(":", 1)
        valid = scheme.lower() == "basic" and secrets.compare_digest(password, APP_PASSWORD)
    except Exception:
        valid = False
    if not valid:
        return Response("Authentification requise", status_code=401, headers={"WWW-Authenticate": 'Basic realm="TikInsight Personal"'})
    return await call_next(request)

def get_collector(name=None):
    choice = (name or COLLECTOR).lower()
    if choice == "official": return OfficialCollector()
    if choice == "public": return PublicExtractor()
    raise HTTPException(400, "Connecteur inconnu.")

class AddVideo(BaseModel):
    url: HttpUrl
    transcript: str | None = Field(default=None, max_length=20000)

class HookBody(BaseModel):
    description: str | None = Field(default=None, max_length=5000)
    transcript: str | None = Field(default=None, max_length=20000)

def snap_json(s):
    return {"id": s.id, "captured_at": s.captured_at.isoformat(), "views": s.views, "likes": s.likes,
            "comments": s.comments, "shares": s.shares, "source": s.source, "note": s.note}

def video_json(v):
    return {"id": v.id, "url": v.url, "platform_id": v.platform_id, "creator": v.creator, "title": v.title,
            "transcript": v.transcript, "collector": v.collector,
            "snapshots": [snap_json(s) for s in v.snapshots],
            "hook": analyze_hook(v.title, v.transcript)}

def collect(url, name=None):
    try: return get_collector(name).fetch(url)
    except (RuntimeError, ValueError) as exc: raise HTTPException(502, str(exc))

@app.get("/api/health")
def health():
    info = {"status": "ok", "collector_default": COLLECTOR}
    try:
        import yt_dlp
        info["yt_dlp"] = yt_dlp.version.__version__
    except Exception:
        info["yt_dlp"] = None
    try:
        import curl_cffi
        info["curl_cffi"] = curl_cffi.__version__
    except Exception:
        info["curl_cffi"] = None
    return info

@app.get("/", response_class=HTMLResponse)
def home(): return HTML

@app.get("/api/videos")
def list_videos(db: Session = Depends(get_db)):
    videos = db.scalars(select(Video).options(selectinload(Video.snapshots)).order_by(Video.id.desc())).all()
    return [video_json(v) for v in videos]

@app.post("/api/videos")
def add_video(body: AddVideo, request: Request, db: Session = Depends(get_db)):
    url = str(body.url)
    if "tiktok.com/" not in url.lower(): raise HTTPException(400, "Seules les URL TikTok sont acceptées.")
    existing = db.scalar(select(Video).where(Video.url == url).options(selectinload(Video.snapshots)))
    if existing:
        if body.transcript: existing.transcript = body.transcript; db.commit()
        return video_json(existing)
    m = collect(url, request.query_params.get("collector"))
    v = Video(url=m.url or url, platform_id=m.platform_id, creator=m.creator, title=m.title,
              transcript=body.transcript, collector=m.source)
    v.snapshots.append(Snapshot(views=m.views, likes=m.likes, comments=m.comments, shares=m.shares, source=m.source, note=m.note))
    db.add(v); db.commit(); db.refresh(v)
    return video_json(v)

@app.post("/api/videos/{video_id}/refresh")
def refresh(video_id: int, request: Request, db: Session = Depends(get_db)):
    v = db.scalar(select(Video).where(Video.id == video_id).options(selectinload(Video.snapshots)))
    if not v: raise HTTPException(404, "Vidéo inconnue.")
    m = collect(v.url, request.query_params.get("collector") or v.collector)
    v.snapshots.append(Snapshot(views=m.views, likes=m.likes, comments=m.comments, shares=m.shares, source=m.source, note=m.note))
    v.title = m.title or v.title; v.creator = m.creator or v.creator; v.collector = m.source
    db.commit(); db.refresh(v)
    return video_json(v)

@app.get("/api/videos/{video_id}/history")
def history(video_id: int, db: Session = Depends(get_db)):
    v = db.scalar(select(Video).where(Video.id == video_id).options(selectinload(Video.snapshots)))
    if not v: raise HTTPException(404, "Vidéo inconnue.")
    result = []
    for i, s in enumerate(v.snapshots):
        old = v.snapshots[i-1] if i else None
        row = snap_json(s)
        for field in ("views", "likes", "comments", "shares"):
            row["delta_" + field] = (getattr(s, field) - getattr(old, field)
                if old and getattr(s, field) is not None and getattr(old, field) is not None else None)
        result.append(row)
    return result

@app.post("/api/hooks/analyze")
def hook(body: HookBody):
    return analyze_hook(body.description, body.transcript)

HTML = r'''<!doctype html>
<html lang="fr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>TikInsight Personal</title><style>
*{box-sizing:border-box}body{margin:0;background:#0b1220;color:#edf3ff;font:16px system-ui}header{padding:20px;background:#101827}main{max-width:850px;margin:auto;padding:14px}.card{background:#121d30;border:1px solid #26364f;border-radius:15px;padding:15px;margin:12px 0}p,.muted{color:#a6b5cb}label{display:block;margin:12px 0 5px;color:#a6b5cb}input,textarea,select,button{width:100%;padding:12px;border-radius:9px;border:1px solid #26364f;background:#0c1525;color:#edf3ff;font:inherit}button{background:#65e0bb;color:#06241c;font-weight:700;margin-top:9px}.stats{display:grid;grid-template-columns:repeat(4,1fr);gap:6px}.stat{background:#0b1424;padding:10px;border-radius:9px}.stat b{display:block}.item{padding:13px 0;border-top:1px solid #26364f}.row{display:grid;grid-template-columns:1fr 1fr;gap:8px}.tag{display:inline-block;border:1px solid #26364f;border-radius:99px;padding:4px 8px;margin:3px;font-size:.8rem}.err{color:#ff9d9d}@media(max-width:500px){.stats{grid-template-columns:repeat(2,1fr)}.row{grid-template-columns:1fr}}
</style></head><body><header><h1>📊 TikInsight Personal</h1><div class="muted">Statistiques accessibles · historique · hooks</div></header><main>
<section class="card"><h2>Ajouter une vidéo</h2><p>Les compteurs absents restent « — ». L'accès aux vidéos concurrentes n'est pas garanti.</p>
<label>URL TikTok</label><input id="url" placeholder="https://www.tiktok.com/@.../video/..." type="url">
<label>Transcription (facultative)</label><textarea id="transcript" rows="3" placeholder="Phrase prononcée au début..."></textarea>
<label>Connecteur</label><select id="collector"><option value="official">API officielle</option><option value="public">Connecteur public alternatif</option></select>
<button onclick="add()">Collecter et enregistrer</button><div id="msg" class="muted"></div></section>
<section class="card"><div class="row"><h2>Vidéos suivies</h2><button onclick="load()">Actualiser</button></div><div id="videos">Chargement…</div></section>
<section class="card"><h2>Analyser un hook</h2><label>Phrase d'ouverture / transcription</label><textarea id="hook" rows="3" placeholder="Collez le hook..."></textarea><button onclick="analyze()">Analyser</button><div id="result"></div></section>
</main><script>
const $=x=>document.getElementById(x),fmt=x=>x===null||x===undefined?'—':Number(x).toLocaleString('fr-FR');
function esc(x){return String(x??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
async function api(p,o={}){let r=await fetch(p,{...o,headers:{'Content-Type':'application/json'}});let d=await r.json().catch(()=>({detail:r.statusText}));if(!r.ok)throw Error(d.detail||'Erreur HTTP '+r.status);return d}
async function add(){try{$('msg').textContent='Collecte…';let v=await api('/api/videos?collector='+$('collector').value,{method:'POST',body:JSON.stringify({url:$('url').value,transcript:$('transcript').value||null})});$('msg').textContent='Vidéo enregistrée, ID local '+v.id;load()}catch(e){$('msg').innerHTML='<span class="err">'+esc(e.message)+'</span>'}}
async function load(){try{let a=await api('/api/videos');$('videos').innerHTML=a.length?a.map(v=>{let s=v.snapshots.at(-1)||{};return `<div class="item"><b>${esc(v.title||'Titre indisponible')}</b><p class="muted">@${esc(v.creator||'créateur inconnu')} · ID ${v.id} · ${esc(v.collector)}</p><div class="stats">${[['Vues',s.views],['J’aime',s.likes],['Commentaires',s.comments],['Partages',s.shares]].map(([k,n])=>`<div class="stat"><span class="muted">${k}</span><b>${fmt(n)}</b></div>`).join('')}</div><p class="muted">${esc(s.note||'')}</p><div class="row"><button onclick="refresh(${v.id})">Nouveau snapshot</button><button onclick="history(${v.id})">Historique</button></div><div id="h${v.id}"></div><p>Signaux du hook : ${v.hook.signals.map(x=>`<span class="tag">${esc(x)}</span>`).join('')||'aucun détecté'}</p><p class="muted">${esc(v.hook.assessment)}</p></div>`}).join(''):'Aucune vidéo suivie.'}catch(e){$('videos').innerHTML='<span class="err">'+esc(e.message)+'</span>'}}
async function refresh(id){try{await api('/api/videos/'+id+'/refresh',{method:'POST'});load()}catch(e){alert(e.message)}}
async function history(id){try{let a=await api('/api/videos/'+id+'/history');$('h'+id).innerHTML=a.map(s=>`<p class="muted">${esc(s.captured_at)} — vues ${fmt(s.views)} (Δ ${fmt(s.delta_views)}), likes ${fmt(s.likes)} (Δ ${fmt(s.delta_likes)}), commentaires ${fmt(s.comments)} (Δ ${fmt(s.delta_comments)}), partages ${fmt(s.shares)} (Δ ${fmt(s.delta_shares)})</p>`).join('')}catch(e){alert(e.message)}}
async function analyze(){try{let r=await api('/api/hooks/analyze',{method:'POST',body:JSON.stringify({description:$('hook').value})});$('result').innerHTML=`<p>${esc(r.assessment)}</p><p>Nombre de mots : ${r.word_count}</p>${r.signals.map(x=>`<span class="tag">${esc(x)}</span>`).join('')}<ul>${r.suggestions.map(x=>`<li>${esc(x)}</li>`).join('')}</ul>`}catch(e){$('result').textContent=e.message}}
load();
</script></body></html>'''
