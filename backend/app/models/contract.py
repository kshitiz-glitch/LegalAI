from datetime import datetime
from sqlalchemy import String, DateTime, Float, ForeignKey, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from typing import Optional
from app.core.database import Base


class Contract(Base):
    __tablename__ = "contracts"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    contract_type: Mapped[Optional[str]] = mapped_column(String(100))
    # pending | analyzing | complete | error
    status: Mapped[str] = mapped_column(String(50), default="pending", nullable=False)
    overall_risk_score: Mapped[Optional[float]] = mapped_column(Float)
    summary: Mapped[Optional[str]] = mapped_column(Text)
    parties: Mapped[Optional[dict]] = mapped_column(JSONB)
    key_dates: Mapped[Optional[dict]] = mapped_column(JSONB)
    clauses: Mapped[Optional[list]] = mapped_column(JSONB)
    redlines: Mapped[Optional[list]] = mapped_column(JSONB)
    negotiation_strategy: Mapped[Optional[dict]] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )
