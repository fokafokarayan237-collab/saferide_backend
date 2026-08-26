"""
Service d'évaluation du risque routier.

Deux modes, sélectionnés automatiquement :
1. Modèle ML (Random Forest, scikit-learn) si un fichier de modèle
   entraîné est trouvé à MODEL_PATH — c'est le mode prévu à terme.
2. Repli sur un scoring à base de règles pondérées si aucun modèle
   n'est présent (ex : avant l'entraînement, ou pendant les tests).

⚠️ Le modèle actuellement livré (s'il est présent) a été entraîné sur
des données SYNTHÉTIQUES générées par generate_synthetic_data.py, pour
valider le pipeline de bout en bout. Il doit être ré-entraîné sur les
vrais datasets (Kaggle + données locales camerounaises, cf. Phase 1/3
du projet) avant toute mise en production. Voir saferide_ml/README.md.

L'explication des facteurs (les 3 conditions les plus déterminantes)
reste calculée par les règles pondérées dans les deux modes : extraire
une explication par prédiction individuelle depuis une forêt aléatoire
demanderait un outil dédié (ex: SHAP), hors périmètre du MVP.
"""

import os
from datetime import datetime, timezone
from pathlib import Path

import joblib
import pandas as pd

from app.schemas import (
    RiskFactorOut,
    RiskLevel,
    RiskResultOut,
    RoadState,
    TimeOfDay,
    TripConditionsIn,
    WeatherCondition,
)

MODEL_PATH = os.getenv(
    "RISK_MODEL_PATH",
    str(Path(__file__).resolve().parents[2] / "ml_model" / "risk_model.joblib"),
)

try:
    _ml_pipeline = joblib.load(MODEL_PATH)
except FileNotFoundError:
    _ml_pipeline = None

# Poids par condition (calibrés à dire d'expert ; utilisés pour le
# scoring de repli ET pour l'explication des facteurs dans tous les cas)
_WEATHER_WEIGHT = {
    WeatherCondition.clair: 0.05,
    WeatherCondition.pluieLegere: 0.35,
    WeatherCondition.forteRain: 0.75,
    WeatherCondition.brouillard: 0.65,
}
_ROAD_WEIGHT = {
    RoadState.bon: 0.05,
    RoadState.moyen: 0.35,
    RoadState.mauvais: 0.70,
}
_TIME_WEIGHT = {
    TimeOfDay.jour: 0.10,
    TimeOfDay.nuit: 0.55,
}
_VEHICLE_MULTIPLIER = {
    "moto": 1.15,   # plus vulnérable
    "voiture": 1.0,
    "bus": 0.9,
}
_TRAFFIC_WEIGHT = 0.25

_WEATHER_LABEL = {
    WeatherCondition.clair: "Temps clair",
    WeatherCondition.pluieLegere: "Pluie légère",
    WeatherCondition.forteRain: "Forte pluie",
    WeatherCondition.brouillard: "Brouillard",
}
_ROAD_LABEL = {
    RoadState.bon: "Route en bon état",
    RoadState.moyen: "Route en état moyen",
    RoadState.mauvais: "Route en mauvais état",
}
_TIME_LABEL = {
    TimeOfDay.jour: "Conduite de jour",
    TimeOfDay.nuit: "Faible éclairage (nuit)",
}


def _level_from_score(score: float) -> RiskLevel:
    if score < 0.34:
        return RiskLevel.faible
    if score < 0.67:
        return RiskLevel.modere
    return RiskLevel.eleve


def _rule_based_score(conditions: TripConditionsIn) -> float:
    weather_w = _WEATHER_WEIGHT[conditions.weather]
    road_w = _ROAD_WEIGHT[conditions.road_state]
    time_w = _TIME_WEIGHT[conditions.time_of_day]
    traffic_w = _TRAFFIC_WEIGHT if conditions.heavy_traffic else 0.0

    raw_score = (
        weather_w * 0.35
        + road_w * 0.30
        + time_w * 0.25
        + traffic_w * 0.10
    )
    multiplier = _VEHICLE_MULTIPLIER[conditions.vehicle_type.value]
    return min(raw_score * multiplier, 1.0)


def _ml_score_and_level(conditions: TripConditionsIn) -> tuple[float, RiskLevel]:
    row = pd.DataFrame([{
        "vehicle_type": conditions.vehicle_type.value,
        "time_of_day": conditions.time_of_day.value,
        "weather": conditions.weather.value,
        "road_state": conditions.road_state.value,
        "heavy_traffic": conditions.heavy_traffic,
    }])
    predicted_level = _ml_pipeline.predict(row)[0]
    proba = _ml_pipeline.predict_proba(row)[0]
    classes = list(_ml_pipeline.classes_)

    # Score continu = proba pondérée par la sévérité (faible=0, modere=0.5, eleve=1)
    severity = {"faible": 0.0, "modere": 0.5, "eleve": 1.0}
    score = sum(p * severity[c] for c, p in zip(classes, proba))

    return round(float(score), 2), RiskLevel(predicted_level)


def _explanation_factors(conditions: TripConditionsIn) -> list[RiskFactorOut]:
    candidates = [
        (_WEATHER_LABEL[conditions.weather], _WEATHER_WEIGHT[conditions.weather]),
        (_ROAD_LABEL[conditions.road_state], _ROAD_WEIGHT[conditions.road_state]),
        (_TIME_LABEL[conditions.time_of_day], _TIME_WEIGHT[conditions.time_of_day]),
    ]
    if conditions.heavy_traffic:
        candidates.append(("Trafic dense", _TRAFFIC_WEIGHT))

    candidates.sort(key=lambda c: c[1], reverse=True)
    return [
        RiskFactorOut(label=label, weight=round(weight, 2))
        for label, weight in candidates[:3]
        if weight > 0
    ]


def compute_risk(conditions: TripConditionsIn) -> RiskResultOut:
    if _ml_pipeline is not None:
        score, level = _ml_score_and_level(conditions)
    else:
        score = round(_rule_based_score(conditions), 2)
        level = _level_from_score(score)

    return RiskResultOut(
        score=score,
        level=level,
        factors=_explanation_factors(conditions),
        evaluated_at=datetime.now(timezone.utc),
    )
