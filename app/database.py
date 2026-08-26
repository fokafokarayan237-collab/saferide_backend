"""
Configuration de la base de données.

L'URL de connexion vient de la variable d'environnement DATABASE_URL,
avec un repli sur une base MySQL locale par défaut (dev uniquement).

Format attendu :
  mysql+pymysql://<user>:<password>@<host>:<port>/<database>
"""

import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mysql+pymysql://root:root@localhost:3306/saferide",
)

engine = create_engine(DATABASE_URL, pool_pre_ping=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """Dépendance FastAPI : fournit une session DB et la ferme après usage."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
