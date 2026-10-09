from .base import Metrics

HINT = (
    " Causes probables : TikTok bloque la requête (IP, anti-bot) ou yt-dlp est obsolète. "
    "Essayez : pip install -U yt-dlp curl_cffi, puis relancez. "
    "Sinon, utilisez le connecteur officiel."
)


def _base_opts():
    return {"quiet": True, "no_warnings": True, "skip_download": True,
            "noplaylist": True, "socket_timeout": 20}


def _impersonation_opts():
    """Ajoute l'imitation de navigateur seulement si curl_cffi est installé."""
    opts = _base_opts()
    try:
        import curl_cffi  # noqa: F401
        from yt_dlp.networking.impersonate import ImpersonateTarget
        opts["impersonate"] = ImpersonateTarget("chrome")
    except Exception:
        pass
    return opts


class PublicExtractor:
    name = "public"

    def fetch(self, url: str) -> Metrics:
        try:
            import yt_dlp
        except ImportError as exc:
            raise RuntimeError("Connecteur public non installé : pip install -r requirements-public.txt") from exc

        info, last_exc = None, None
        for opts in (_impersonation_opts(), _base_opts()):
            try:
                with yt_dlp.YoutubeDL(opts) as ydl:
                    info = ydl.extract_info(url, download=False)
                break
            except Exception as exc:
                last_exc = exc
                if "impersonate" not in opts:
                    break
        if info is None:
            raise RuntimeError(
                f"Extraction publique impossible : {type(last_exc).__name__}: {str(last_exc)[:180]}.{HINT}"
            ) from last_exc

        return Metrics(
            url=info.get("webpage_url") or url,
            platform_id=str(info.get("id")) if info.get("id") else None,
            creator=info.get("uploader") or info.get("channel"),
            title=info.get("title"),
            views=info.get("view_count"), likes=info.get("like_count"),
            comments=info.get("comment_count"),
            shares=info.get("share_count") or info.get("repost_count"),
            source=self.name, note="Extracteur public best-effort; compteurs absents laissés vides.",
        )
