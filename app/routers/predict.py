import json

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models_db import Evaluation, User
from app.schemas import RiskFactorOut, RiskResultOut, TripConditionsIn
from app.services.risk_model import compute_risk

router = APIRouter(prefix="/predict", tags=["risque"])


@router.post("", response_model=RiskResultOut)
def predict_risk(
    conditions: TripConditionsIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> RiskResultOut:
    """
    Calcule le risque pour les conditions données et enregistre
    l'évaluation dans l'historique de l'utilisateur connecté.
    """
    result = compute_risk(conditions)

    evaluation = Evaluation(
        user_id=current_user.id,
        vehicle_type=conditions.vehicle_type.value,
        time_of_day=conditions.time_of_day.value,
        weather=conditions.weather.value,
        road_state=conditions.road_state.value,
        heavy_traffic=conditions.heavy_traffic,
        score=result.score,
        level=result.level.value,
        factors_json=json.dumps([f.model_dump() for f in result.factors]),
        evaluated_at=result.evaluated_at,
    )
    db.add(evaluation)
    db.commit()
    db.refresh(evaluation)  # récupère l'id généré par la base

    return RiskResultOut(
        id=evaluation.id,
        score=result.score,
        level=result.level,
        factors=[RiskFactorOut(**f.model_dump()) for f in result.factors],
        evaluated_at=result.evaluated_at,
    )
