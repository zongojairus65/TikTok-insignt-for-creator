import re
import httpx
from .base import Metrics
from ..config import TIKTOK_ACCESS_TOKEN

ID_RE = re.compile(r"/video/(\d+)")

class OfficialCollector:
    name = "official"
    def fetch(self, url: str) -> Metrics:
        match = ID_RE.search(url)
        if not match:
            raise ValueError("URL invalide : identifiant /video/ introuvable.")
        if not TIKTOK_ACCESS_TOKEN:
            raise RuntimeError("TIKTOK_ACCESS_TOKEN absent. Obtenez un jeton OAuth autorisé.")
        video_id = match.group(1)
        endpoint = "https://open.tiktokapis.com/v2/video/query/"
        params = {"fields": "id,share_url,video_description,title,like_count,comment_count,share_count,view_count"}
        headers = {"Authorization": f"Bearer {TIKTOK_ACCESS_TOKEN}", "Content-Type": "application/json"}
        response = httpx.post(endpoint, params=params, headers=headers, json={"filters": {"video_ids": [video_id]}}, timeout=20)
        if response.status_code >= 400:
            raise RuntimeError(f"TikTok API HTTP {response.status_code}: {response.text[:250]}")
        payload = response.json()
        data = payload.get("data") or {}
        items = data.get("videos") or data.get("video_list") or []
        item = next((x for x in items if str(x.get("id", "")) == video_id), None)
        if not item:
            raise RuntimeError("Vidéo non retournée. L'API officielle ne garantit pas l'accès aux vidéos concurrentes; vérifiez le compte et le scope video.list.")
        return Metrics(
            url=item.get("share_url") or url, platform_id=str(item.get("id") or video_id),
            title=item.get("title") or item.get("video_description"),
            views=item.get("view_count"), likes=item.get("like_count"),
            comments=item.get("comment_count"), shares=item.get("share_count"),
            source=self.name, note="API officielle; disponibilité dépend du compte et des autorisations."
        )
