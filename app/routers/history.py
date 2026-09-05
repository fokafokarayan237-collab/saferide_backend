import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models_db import Evaluation, User
from app.schemas import RiskFactorOut, RiskResultOut

router = APIRouter(prefix="/history", tags=["historique"])


def _to_result_out(e: Evaluation) -> RiskResultOut:
    return RiskResultOut(
        id=e.id,
        score=e.score,
        level=e.level,
        factors=[RiskFactorOut(**f) for f in json.loads(e.factors_json)],
        evaluated_at=e.evaluated_at,
    )


@router.get("", response_model=list[RiskResultOut])
def get_history(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[RiskResultOut]:
    evaluations = (
        db.query(Evaluation)
        .filter(Evaluation.user_id == current_user.id)
        .order_by(Evaluation.evaluated_at.desc())
        .all()
    )
    return [_to_result_out(e) for e in evaluations]


@router.delete("/{evaluation_id}", status_code=204)
def delete_history_entry(
    evaluation_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    evaluation = (
        db.query(Evaluation)
        .filter(
            Evaluation.id == evaluation_id,
            Evaluation.user_id == current_user.id,
        )
        .first()
    )
    if evaluation is None:
        raise HTTPException(status_code=404, detail="Évaluation introuvable.")
    db.delete(evaluation)
    db.commit()
