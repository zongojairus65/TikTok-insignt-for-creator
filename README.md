# TikInsight Personal

Dashboard personnel mobile : statistiques disponibles, historique des snapshots, analyse heuristique des hooks.

## Limites essentielles
- L'API officielle TikTok `video/query` exige un jeton OAuth avec les permissions nécessaires et ne garantit pas l'accès aux vidéos d'autres comptes. Elle vérifie que la vidéo appartient au compte autorisé.
- Le connecteur `yt-dlp` est optionnel et best-effort : TikTok peut bloquer la requête, changer son site ou ne pas exposer certaines métriques.
- Une valeur `null` / « — » signifie non disponible, jamais zéro.
- L'analyse des hooks est linguistique et heuristique. Elle ne mesure pas la rétention et ne prédit pas la viralité.

Docs officielles :
- https://developers.tiktok.com/docs/en/tiktok-api-v2-video-query
- https://developers.tiktok.com/docs/en/display-api-overview
- https://developers.tiktok.com/docs/en/tiktok-api-v2-video-object

## Android / Termux
```bash
pkg update && pkg upgrade
pkg install python git
# Décompressez le ZIP dans un dossier accessible, puis entrez dans ce dossier
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```
Modifiez `.env` avec un éditeur texte. Mettez un long secret dans `APP_PASSWORD`, par exemple une valeur générée par :
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```
Pour lancer localement :
```bash
set -a; source .env; set +a
uvicorn app.main:app --host 127.0.0.1 --port 8000
```
Ouvrez `http://127.0.0.1:8000` dans le navigateur du téléphone. Le navigateur demande l'authentification HTTP Basic si `APP_PASSWORD` est renseigné.

Pour le connecteur public :
```bash
pip install -r requirements-public.txt
```
Puis réglez `COLLECTOR=public` dans `.env`.

## GitHub + Render
1. Créez un dépôt GitHub vide et téléversez les fichiers du ZIP (ou utilisez `git init`, `git add .`, `git commit`, puis `git push` depuis Termux).
2. Sur Render : New → Web Service → connectez le dépôt.
3. Build command : `pip install -r requirements.txt`
4. Start command : `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
5. Configurez `APP_PASSWORD` et `DATABASE_URL` dans Environment. Pour une vraie persistance sur Render, configurez PostgreSQL et mettez son URL dans `DATABASE_URL`; SQLite local convient aux tests Termux.
6. Ajoutez `TIKTOK_ACCESS_TOKEN` uniquement si vous avez obtenu un jeton officiel autorisé. Ne commitez jamais les secrets.
7. `render.yaml` fournit une configuration de départ, mais la base PostgreSQL doit être créée/configurée séparément.

## Utilisation
Ajoutez une URL TikTok, choisissez le connecteur, puis utilisez « Snapshot » pour enregistrer les compteurs actuels disponibles. Les différences sont calculées entre deux snapshots uniquement si les deux valeurs existent. Ajoutez une transcription pour analyser plus utilement la phrase d'ouverture.

## API
- `GET /api/health`
- `GET /api/videos`
- `POST /api/videos` JSON `{"url":"https://www.tiktok.com/@nom/video/123","transcript":"..."}`
- `POST /api/videos/{id}/refresh?collector=public`
- `GET /api/videos/{id}/history`
- `POST /api/hooks/analyze` JSON `{"description":"...","transcript":"..."}`

## Tests
```bash
pip install -r requirements-dev.txt
pytest -q
```

L'application ne contourne pas les restrictions, CAPTCHA ou connexions TikTok. Respectez les conditions d'utilisation, les droits des créateurs et les règles applicables.
