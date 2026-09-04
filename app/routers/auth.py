import random
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.models_db import OtpCode, User
from app.schemas import LoginIn, LoginOut, OtpRequiredOut, OtpVerifyIn, RegisterIn
from app.security import create_access_token, hash_password, verify_password

router = APIRouter(prefix="/auth", tags=["auth"])

OTP_VALIDITY_MINUTES = 5


def _generate_otp() -> str:
    return f"{random.randint(0, 999999):06d}"


def _create_otp(db: Session, phone: str, purpose: str) -> str:
    code = _generate_otp()
    otp = OtpCode(
        phone=phone,
        code=code,
        purpose=purpose,
        expires_at=datetime.utcnow() + timedelta(minutes=OTP_VALIDITY_MINUTES),
    )
    db.add(otp)
    db.commit()
    return code


@router.post("/register", response_model=OtpRequiredOut)
def register(credentials: RegisterIn, db: Session = Depends(get_db)) -> OtpRequiredOut:
    existing_phone = db.query(User).filter(User.phone == credentials.phone).first()
    if existing_phone:
        raise HTTPException(status_code=409, detail="Ce numéro est déjà utilisé.")

    if credentials.email:
        existing_email = db.query(User).filter(User.email == credentials.email).first()
        if existing_email:
            raise HTTPException(status_code=409, detail="Cet email est déjà utilisé.")

    user = User(
        phone=credentials.phone,
        email=credentials.email,
        hashed_password=hash_password(credentials.password),
    )
    db.add(user)
    db.commit()

    code = _create_otp(db, user.phone, purpose="register")
    return OtpRequiredOut(
        message="Compte créé. Entre le code de vérification pour terminer l'inscription.",
        phone=user.phone,
        test_code=code,
    )


@router.post("/login", response_model=OtpRequiredOut)
def login(credentials: LoginIn, db: Session = Depends(get_db)) -> OtpRequiredOut:
    user = db.query(User).filter(User.phone == credentials.phone).first()
    if user is None or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Numéro ou mot de passe incorrect.")

    code = _create_otp(db, user.phone, purpose="login")
    return OtpRequiredOut(
        message="Entre le code de vérification pour te connecter.",
        phone=user.phone,
        test_code=code,
    )


@router.post("/verify-otp", response_model=LoginOut)
def verify_otp(data: OtpVerifyIn, db: Session = Depends(get_db)) -> LoginOut:
    otp = (
        db.query(OtpCode)
        .filter(OtpCode.phone == data.phone, OtpCode.code == data.code, OtpCode.used == False)  # noqa: E712
        .order_by(OtpCode.id.desc())
        .first()
    )
    if otp is None:
        raise HTTPException(status_code=401, detail="Code invalide.")
    if otp.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Code expiré, redemande un code.")

    otp.used = True
    db.commit()

    user = db.query(User).filter(User.phone == data.phone).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    token = create_access_token(subject=user.phone)
    return LoginOut(access_token=token, is_admin=user.is_admin)
