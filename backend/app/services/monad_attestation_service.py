from sqlalchemy import select, desc
from sqlalchemy.ext.asyncio import AsyncSession
from app.storage.models.monad_attestation import MonadAttestation


async def save_attestation(
    session: AsyncSession,
    scan_result: dict,
    wallet_address: str | None = None,
) -> MonadAttestation:
    record = MonadAttestation(
        agent_id=scan_result["agent_id"],
        agent_endpoint=scan_result["agent_endpoint"],
        wallet_address=wallet_address,
        tpi_score=scan_result["tpi_score"],
        result_hash=scan_result["result_hash"],
        tx_hash=scan_result.get("tx_hash"),
        passed_tests=scan_result["passed_tests"],
        total_tests=scan_result["total_tests"],
        test_results=scan_result["test_results"],
        owasp_breakdown=scan_result.get("owasp_breakdown", {}),
        kill_switch_active=scan_result.get("kill_switch_triggered", False),
    )
    session.add(record)
    await session.flush()
    return record


async def update_tx_hash(
    session: AsyncSession,
    agent_id: str,
    result_hash: str,
    tx_hash: str,
    erc8004_feedback_id: int | None = None,
) -> MonadAttestation | None:
    stmt = (
        select(MonadAttestation)
        .where(MonadAttestation.agent_id == agent_id)
        .where(MonadAttestation.result_hash == result_hash)
        .order_by(desc(MonadAttestation.created_at))
        .limit(1)
    )
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()
    if record:
        record.tx_hash = tx_hash
        if erc8004_feedback_id is not None:
            record.erc8004_feedback_id = erc8004_feedback_id
        await session.flush()
    return record


async def toggle_kill_switch(
    session: AsyncSession,
    agent_id: str,
    activate: bool,
) -> MonadAttestation | None:
    """Enable or disable the kill switch for an agent's latest attestation."""
    stmt = (
        select(MonadAttestation)
        .where(MonadAttestation.agent_id == agent_id)
        .order_by(desc(MonadAttestation.created_at))
        .limit(1)
    )
    result = await session.execute(stmt)
    record = result.scalar_one_or_none()
    if record:
        record.kill_switch_active = activate
        await session.flush()
    return record


async def get_by_agent_id(session: AsyncSession, agent_id: str) -> MonadAttestation | None:
    stmt = (
        select(MonadAttestation)
        .where(MonadAttestation.agent_id == agent_id)
        .order_by(desc(MonadAttestation.created_at))
        .limit(1)
    )
    result = await session.execute(stmt)
    return result.scalar_one_or_none()


async def get_all(session: AsyncSession, limit: int = 100) -> list[MonadAttestation]:
    stmt = (
        select(MonadAttestation)
        .order_by(desc(MonadAttestation.tpi_score), desc(MonadAttestation.created_at))
        .limit(limit)
    )
    result = await session.execute(stmt)
    return list(result.scalars().all())
