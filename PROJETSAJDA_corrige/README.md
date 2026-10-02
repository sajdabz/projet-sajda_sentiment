# Analyse de sentiments : texte + photo

## Lancer le projet
```bash
pip install -r requirements.txt
# (optionnel) export DATABASE_URL="postgresql://user:motdepasse@localhost:5432/sentiment_db"
uvicorn main:app --reload
```
Puis ouvrir `index.html` dans le navigateur (ou via Live Server).
La base PostgreSQL `sentiment_db` doit exister ; les tables sont créées automatiquement.

## Routes
- `POST /analyze` : texte -> sentiment
- `POST /analyze-face` : photo (base64) -> émotion -> sentiment
- `GET /historique`, `GET /historique-visage`
