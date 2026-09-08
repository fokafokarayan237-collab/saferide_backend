from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models_db import User
from app.schemas import MeOut, UpdateProfileIn

router = APIRouter(prefix="/users", tags=["utilisateurs"])


def _to_out(user: User) -> MeOut:
    return MeOut(
        id=user.id,
        phone=user.phone,
        email=user.email,
        nom=user.nom,
        prenom=user.prenom,
        photo_base64=user.photo_base64,
        is_admin=user.is_admin,
        created_at=user.created_at,
    )


@router.get("/me", response_model=MeOut)
def get_me(current_user: User = Depends(get_current_user)) -> MeOut:
    return _to_out(current_user)


@router.patch("/me", response_model=MeOut)
def update_me(
    data: UpdateProfileIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> MeOut:
    if data.nom is not None:
        current_user.nom = data.nom
    if data.prenom is not None:
        current_user.prenom = data.prenom
    if data.photo_base64 is not None:
        current_user.photo_base64 = data.photo_base64
    db.commit()
    db.refresh(current_user)
    return _to_out(current_user)


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    """Supprime définitivement le compte (et en cascade son historique et
    ses signalements, via les relations SQLAlchemy)."""
    db.delete(current_user)
    db.commit()
