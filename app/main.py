from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.database import Base, engine
from app.routers import admin, auth, history, predict

# Crée les tables MySQL si elles n'existent pas encore.
# Pour un vrai projet en évolution, remplacer par des migrations Alembic.
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="SafeRide Cameroun API",
    description="API d'évaluation du risque routier - Projet de génie logiciel",
    version="0.1.0",
)

# En développement seulement : à restreindre au domaine réel avant mise en prod
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(history.router)
app.include_router(admin.router)


@app.get("/health", tags=["système"])
def health_check():
    return {"status": "ok"}
