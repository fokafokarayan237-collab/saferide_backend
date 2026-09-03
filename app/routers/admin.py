import json
from collections import Counter
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models_db import Evaluation, User
from app.schemas import AdminStatsOut, DailyCountOut, FactorFrequencyOut

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsOut)
def get_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> AdminStatsOut:
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs.",
        )

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
