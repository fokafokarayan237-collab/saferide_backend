import json
from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models_db import Evaluation, User
from app.schemas import (
    AdminStatsOut,
    DailyCountOut,
    FactorFrequencyOut,
    SetAdminIn,
    UserOut,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(current_user: User) -> None:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs.",
        )


@router.get("/stats", response_model=AdminStatsOut)
def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AdminStatsOut:
    _require_admin(current_user)

    since = datetime.now(timezone.utc) - timedelta(days=7)
    evaluations = (
        db.query(Evaluation).filter(Evaluation.evaluated_at >= since).all()
    )

    total = len(evaluations)
    high_risk_count = sum(1 for e in evaluations if e.level == "eleve")
    high_risk_pct = round((high_risk_count / total) * 100, 1) if total else 0.0

    # Évaluations par jour, sur les 7 derniers jours (jours sans données -> 0)
    counts_by_day: dict[str, int] = {}
    today = datetime.now(timezone.utc).date()
    for i in range(6, -1, -1):
        day = today - timedelta(days=i)
        counts_by_day[day.isoformat()] = 0
    for e in evaluations:
        day_key = e.evaluated_at.date().isoformat()
        if day_key in counts_by_day:
            counts_by_day[day_key] += 1
    daily_counts = [
        DailyCountOut(date=day, count=count) for day, count in counts_by_day.items()
    ]

    # Facteur le plus déterminant (premier de la liste, déjà triée par
    # poids décroissant côté risk_model.py) de chaque évaluation
    factor_counter: Counter[str] = Counter()
    for e in evaluations:
        factors = json.loads(e.factors_json)
        if factors:
            factor_counter[factors[0]["label"]] += 1

    top_factors = [
        FactorFrequencyOut(label=label, frequency=round(count / total, 2))
        for label, count in factor_counter.most_common(5)
    ] if total else []

    return AdminStatsOut(
        total_evaluations_7d=total,
        high_risk_percentage=high_risk_pct,
        daily_counts=daily_counts,
        top_factors=top_factors,
    )


@router.get("/users", response_model=list[UserOut])
def list_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[UserOut]:
    """Liste de tous les comptes, réservée aux administrateurs."""
    _require_admin(current_user)
    users = db.query(User).order_by(User.created_at.desc()).all()
    return [
        UserOut(
            id=u.id,
            phone=u.phone,
            email=u.email,
            is_admin=u.is_admin,
            created_at=u.created_at,
        )
        for u in users
    ]


@router.patch("/users/{user_id}", response_model=UserOut)
def set_user_admin(
    user_id: int,
    data: SetAdminIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> UserOut:
    """Promeut ou rétrograde un utilisateur en/de administrateur."""
    _require_admin(current_user)

    if user_id == current_user.id and not data.is_admin:
        raise HTTPException(
            status_code=400,
            detail="Tu ne peux pas retirer ton propre statut administrateur.",
        )

    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable.")

    user.is_admin = data.is_admin
    db.commit()
    db.refresh(user)

    return UserOut(
        id=user.id,
        phone=user.phone,
        email=user.email,
        is_admin=user.is_admin,
        created_at=user.created_at,
    )
