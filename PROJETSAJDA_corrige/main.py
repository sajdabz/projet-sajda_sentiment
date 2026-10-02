import os

# transformers utilise PyTorch ici : on lui interdit de charger TensorFlow
# (évite le conflit tensorflow / tf_keras). À mettre AVANT l'import de transformers.
os.environ["USE_TF"] = "0"
os.environ["TRANSFORMERS_NO_TF"] = "1"

import base64

import cv2
import numpy as np
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy.orm import Session
from transformers import pipeline

from database import Base, engine, get_db
from models import Analyse, AnalyseFace

# Crée les tables (analyses + analyses_visage) si elles n'existent pas
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Analyse de sentiments : texte + photo")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # développement uniquement
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Le modèle texte est chargé une seule fois au démarrage
classifier = pipeline(
    "sentiment-analysis",
    model="nlptown/bert-base-multilingual-uncased-sentiment",
)


class TexteInput(BaseModel):
    texte: str


class ImageInput(BaseModel):
    image: str  # data URL base64 envoyée par le navigateur


def convertir_sentiment(label: str) -> str:
    """'1 star' ... '5 stars' -> négatif / neutre / positif"""
    if label in ("1 star", "2 stars"):
        return "négatif"
    if label == "3 stars":
        return "neutre"
    return "positif"


def convertir_emotion_sentiment(emotion: str) -> str:
    if emotion in ("happy", "surprise"):
        return "positif"
    if emotion in ("sad", "angry", "fear", "disgust"):
        return "négatif"
    return "neutre"


@app.post("/analyze")
def analyze_sentiment(input: TexteInput, db: Session = Depends(get_db)):
    texte = input.texte.strip()
    if not texte:
        raise HTTPException(status_code=400, detail="Le texte est vide.")

    resultat = classifier(texte, truncation=True, max_length=512)[0]
    sentiment = convertir_sentiment(resultat["label"])
    score = round(float(resultat["score"]), 2)

    analyse = Analyse(
        texte=texte,
        sentiment=sentiment,
        score=score,
        label_brut=resultat["label"],
    )
    db.add(analyse)
    db.commit()
    db.refresh(analyse)

    return {
        "id": analyse.id,
        "texte": analyse.texte,
        "sentiment": analyse.sentiment,
        "score": analyse.score,
        "label_brut": analyse.label_brut,
        "date_creation": analyse.date_creation,
    }


@app.post("/analyze-face")
def analyze_face(input: ImageInput, db: Session = Depends(get_db)):
    # 1) Décoder l'image base64
    try:
        data = input.image.split(",", 1)[1] if "," in input.image else input.image
        nparr = np.frombuffer(base64.b64decode(data), np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("image illisible")
    except Exception:
        raise HTTPException(status_code=400, detail="Image invalide.")

    # DeepFace est chargé ici (et pas au démarrage) : le mode texte marche
    # même si DeepFace / TensorFlow est mal installé.
    try:
        from deepface import DeepFace
    except Exception as e:
        raise HTTPException(
            status_code=503,
            detail="DeepFace n'est pas utilisable (installation TensorFlow) : " + str(e)[:150],
        )

    # 2) Analyser l'émotion. enforce_detection=True => erreur s'il n'y a pas de visage
    #    (avec False, DeepFace "invente" une émotion même sur un mur !)
    try:
        resultat = DeepFace.analyze(img, actions=["emotion"], enforce_detection=True)
    except ValueError:
        raise HTTPException(
            status_code=422,
            detail="Aucun visage détecté. Reprends la photo face à la caméra, bien éclairé.",
        )

    # selon la version de DeepFace : liste ou dict
    emotion_data = resultat[0] if isinstance(resultat, list) else resultat
    emotion_dominante = emotion_data["dominant_emotion"]
    score = round(float(emotion_data["emotion"][emotion_dominante]) / 100, 2)
    sentiment = convertir_emotion_sentiment(emotion_dominante)

    analyse = AnalyseFace(
        emotion_dominante=emotion_dominante,
        sentiment=sentiment,
        score=score,
    )
    db.add(analyse)
    db.commit()
    db.refresh(analyse)

    return {
        "id": analyse.id,
        "emotion_dominante": emotion_dominante,
        "sentiment": sentiment,
        "score": score,
        "date_creation": analyse.date_creation,
    }


@app.get("/historique")
def get_historique(db: Session = Depends(get_db)):
    return db.query(Analyse).order_by(Analyse.date_creation.desc()).all()


@app.get("/historique-visage")
def get_historique_visage(db: Session = Depends(get_db)):
    return db.query(AnalyseFace).order_by(AnalyseFace.date_creation.desc()).all()


@app.get("/")
def home():
    return {"message": "API d'analyse de sentiments (texte + photo) fonctionne !"}