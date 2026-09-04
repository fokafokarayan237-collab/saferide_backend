from datetime import datetime, timezone

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    evaluations: Mapped[list["Evaluation"]] = relationship(
        back_populates="user", cascade="all, delete-orphan"
    )


class OtpCode(Base):
    """Code de vérification à 6 chiffres (inscription ou connexion).

    MODE TEST : le code n'est pas envoyé par SMS, il est renvoyé directement
    dans la réponse de l'API pour que l'app puisse l'afficher à l'écran.
    """

    __tablename__ = "otp_codes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    phone: Mapped[str] = mapped_column(String(20), index=True)
    code: Mapped[str] = mapped_column(String(6))
    purpose: Mapped[str] = mapped_column(String(20))  # "register" ou "login"
    used: Mapped[bool] = mapped_column(Boolean, default=False)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )


class Evaluation(Base):
    """Une évaluation de risque enregistrée pour un utilisateur donné."""

    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True)

    # Conditions saisies
    vehicle_type: Mapped[str] = mapped_column(String(20))
    time_of_day: Mapped[str] = mapped_column(String(10))
    weather: Mapped[str] = mapped_column(String(20))
    road_state: Mapped[str] = mapped_column(String(10))
    heavy_traffic: Mapped[bool] = mapped_column(Boolean, default=False)
    latitude: Mapped[float | None] = mapped_column(Float, nullable=True)
    longitude: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Résultat
    score: Mapped[float] = mapped_column(Float)
    level: Mapped[str] = mapped_column(String(10))
    factors_json: Mapped[str] = mapped_column(String(500))  # JSON encodé : [{"label":..,"weight":..}]
    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )

    user: Mapped["User"] = relationship(back_populates="evaluations")
