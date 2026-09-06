from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models_db import IncidentReport, User
from app.schemas import IncidentReportIn, IncidentReportOut

router = APIRouter(prefix="/incidents", tags=["incidents"])


def _to_out(incident: IncidentReport) -> IncidentReportOut:
    return IncidentReportOut(
        id=incident.id,
        vehicle_type=incident.vehicle_type,
        time_of_day=incident.time_of_day,
        weather=incident.weather,
        road_state=incident.road_state,
        heavy_traffic=incident.heavy_traffic,
        had_accident=incident.had_accident,
        severity=incident.severity,
        description=incident.description,
        reported_at=incident.reported_at,
    )


@router.get("", response_model=list[IncidentReportOut])
def list_incidents(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[IncidentReportOut]:
    """Liste des signalements reçus, réservée aux administrateurs."""
    if not current_user.is_admin:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Accès réservé aux administrateurs.",
        )
    incidents = (
        db.query(IncidentReport)
        .order_by(IncidentReport.reported_at.desc())
        .limit(100)
        .all()
    )
    return [_to_out(i) for i in incidents]


@router.post("", response_model=IncidentReportOut, status_code=201)
def create_incident(
    payload: IncidentReportIn,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> IncidentReportOut:
    """
    Enregistre un signalement d'incident réel (accident ou quasi-accident)
    avec les conditions au moment des faits. Ces données constituent le
    futur jeu de données local camerounais pour ré-entraîner le modèle ML.
    """
    incident = IncidentReport(
        user_id=current_user.id,
        vehicle_type=payload.vehicle_type.value,
        time_of_day=payload.time_of_day.value,
        weather=payload.weather.value,
        road_state=payload.road_state.value,
        heavy_traffic=payload.heavy_traffic,
        latitude=payload.latitude,
        longitude=payload.longitude,
        had_accident=payload.had_accident,
        severity=payload.severity.value if payload.severity else None,
        description=payload.description,
    )
    db.add(incident)
    db.commit()
    db.refresh(incident)

    return _to_out(incident)
