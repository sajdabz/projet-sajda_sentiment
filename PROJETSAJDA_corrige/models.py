from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from database import Base


class Analyse(Base):
    """Analyse d'un TEXTE."""
    __tablename__ = "analyses"

    id = Column(Integer, primary_key=True, index=True)
    texte = Column(String, nullable=False)
    sentiment = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    label_brut = Column(String, nullable=False)
    date_creation = Column(DateTime, default=datetime.utcnow)


class AnalyseFace(Base):
    """Analyse d'une PHOTO (émotion du visage)."""
    __tablename__ = "analyses_visage"

    id = Column(Integer, primary_key=True, index=True)
    emotion_dominante = Column(String, nullable=False)
    sentiment = Column(String, nullable=False)
    score = Column(Float, nullable=False)
    date_creation = Column(DateTime, default=datetime.utcnow)
