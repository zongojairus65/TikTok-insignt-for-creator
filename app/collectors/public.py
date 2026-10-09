from .base import Metrics

class PublicExtractor:
    name = "public"
    def fetch(self, url: str) -> Metrics:
        try:
            import yt_dlp
        except ImportError as exc:
            raise RuntimeError("Connecteur public non installé : pip install -r requirements-public.txt") from exc
        try:
            with yt_dlp.YoutubeDL({"quiet": True, "no_warnings": True, "skip_download": True, "noplaylist": True}) as ydl:
                info = ydl.extract_info(url, download=False)
        except Exception as exc:
            raise RuntimeError(f"Extraction publique impossible : {type(exc).__name__}: {str(exc)[:180]}") from exc
        return Metrics(
            url=info.get("webpage_url") or url,
            platform_id=str(info.get("id")) if info.get("id") else None,
            creator=info.get("uploader") or info.get("channel"),
            title=info.get("title"),
            views=info.get("view_count"), likes=info.get("like_count"),
            comments=info.get("comment_count"),
            shares=info.get("share_count") or info.get("repost_count"),
            source=self.name, note="Extracteur public best-effort; compteurs absents laissés vides."
        )
