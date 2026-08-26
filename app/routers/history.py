import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models_db import Evaluation, User
from app.schemas import RiskFactorOut, RiskResultOut

router = APIRouter(prefix="/history", tags=["historique"])


def _to_result_out(e: Evaluation) -> RiskResultOut:
    return RiskResultOut(
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
