import uuid
from datetime import datetime, timezone
from sqlalchemy import String, Integer, Boolean, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column
from app.storage.models.base import Base


class MonadAttestation(Base):
    __tablename__ = "monad_attestations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    agent_id: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    agent_endpoint: Mapped[str] = mapped_column(Text, nullable=False)
    wallet_address: Mapped[str | None] = mapped_column(String(42), nullable=True)
    tpi_score: Mapped[int] = mapped_column(Integer, nullable=False)
    result_hash: Mapped[str] = mapped_column(String(66), nullable=False)
    tx_hash: Mapped[str | None] = mapped_column(String(66), nullable=True)
    erc8004_feedback_id: Mapped[int | None] = mapped_column(Integer, nullable=True)
    passed_tests: Mapped[int] = mapped_column(Integer, nullable=False)
    total_tests: Mapped[int] = mapped_column(Integer, nullable=False, default=5)
    test_results: Mapped[dict] = mapped_column(JSON, nullable=False)
    owasp_breakdown: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    kill_switch_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
