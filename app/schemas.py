from datetime import datetime
from enum import Enum
from pydantic import BaseModel, EmailStr, Field


# --- Enums : doivent rester synchronisés avec lib/models/trip_conditions.dart ---

class VehicleType(str, Enum):
    moto = "moto"
    voiture = "voiture"
    bus = "bus"


class TimeOfDay(str, Enum):
    jour = "jour"
    nuit = "nuit"


class WeatherCondition(str, Enum):
    clair = "clair"
    pluieLegere = "pluieLegere"
    forteRain = "forteRain"
    brouillard = "brouillard"


class RoadState(str, Enum):
    bon = "bon"
    moyen = "moyen"
    mauvais = "mauvais"


class RiskLevel(str, Enum):
    faible = "faible"
    modere = "modere"
    eleve = "eleve"


# --- Requête envoyée par l'app mobile (POST /predict) ---

class TripConditionsIn(BaseModel):
    vehicle_type: VehicleType
    time_of_day: TimeOfDay
    weather: WeatherCondition
    road_state: RoadState
    heavy_traffic: bool = False
    latitude: float | None = None
    longitude: float | None = None


# --- Réponse renvoyée à l'app mobile ---

class RiskFactorOut(BaseModel):
    label: str
    weight: float = Field(ge=0.0, le=1.0)


class RiskResultOut(BaseModel):
    score: float = Field(ge=0.0, le=1.0)
    level: RiskLevel
    factors: list[RiskFactorOut]
    evaluated_at: datetime


# --- Auth ---

class LoginIn(BaseModel):
    phone: str
    password: str


class RegisterIn(BaseModel):
    phone: str
    password: str
    email: EmailStr | None = None


class LoginOut(BaseModel):
    access_token: str
    token_type: str = "bearer"


# --- Admin (statistiques agrégées) ---

class DailyCountOut(BaseModel):
    date: str  # format AAAA-MM-JJ
    count: int


class FactorFrequencyOut(BaseModel):
    label: str
    frequency: float = Field(ge=0.0, le=1.0)  # part des évaluations où ce facteur est le plus déterminant


class AdminStatsOut(BaseModel):
    total_evaluations_7d: int
    high_risk_percentage: float = Field(ge=0.0, le=100.0)
    daily_counts: list[DailyCountOut]  # 7 derniers jours, dans l'ordre chronologique
    top_factors: list[FactorFrequencyOut]
