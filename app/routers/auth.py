from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models_db import User
from app.schemas import LoginIn, LoginOut
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=LoginOut)
def register(credentials: LoginIn, db: Session = Depends(get_db)) -> LoginOut:
    existing = db.query(User).filter(User.phone == credentials.phone).first()
    if existing:
        raise HTTPException(status_code=409, detail="Ce numéro est déjà utilisé.")

    user = User(
        phone=credentials.phone,
        hashed_password=hash_password(credentials.password),
    )
    db.add(user)
    db.commit()

    token = create_access_token(subject=user.phone)
    return LoginOut(access_token=token)


@router.post("/login", response_model=LoginOut)
def login(credentials: LoginIn, db: Session = Depends(get_db)) -> LoginOut:
    user = db.query(User).filter(User.phone == credentials.phone).first()
    if user is None or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Numéro ou mot de passe incorrect.")

    token = create_access_token(subject=user.phone)
    return LoginOut(access_token=token)
