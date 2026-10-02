import os
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Idéalement : définir la variable d'environnement DATABASE_URL.
# Sinon on utilise la valeur par défaut ci-dessous (PostgreSQL local).
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://postgres:sajda12345@localhost:5432/sentiment_db",
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
