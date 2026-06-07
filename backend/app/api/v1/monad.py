import logging
from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.storage.database import get_async_session
from app.api.schemas.monad import (
    ScanRequest, ScanResponse, AttestRequest, AttestResponse,
    VerifyResponse, KillSwitchRequest, KillSwitchResponse,
)
from app.services.agentshield_scanner import run_full_scan
from app.services.x402_verifier import verify_x402_payment, settle_x402_payment
from app.services.monad_attestation_service import (
    save_attestation, update_tx_hash, toggle_kill_switch,
    get_by_agent_id, get_all,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/monad")


@router.post("/scan", response_model=ScanResponse)
async def monad_scan(
    request: Request,
    body: ScanRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """x402-gated adversarial security scan with OWASP-weighted TPI scoring."""
    payment_header = await verify_x402_payment(request)

    scan_result = await run_full_scan(body.agent_endpoint, body.agent_id)

    await save_attestation(
        session,
        {**scan_result, "agent_endpoint": body.agent_endpoint},
        wallet_address=body.wallet_address,
    )

    await settle_x402_payment(payment_header)

    return ScanResponse(
        agent_id=scan_result["agent_id"],
        tpi_score=scan_result["tpi_score"],
        passed_tests=scan_result["passed_tests"],
        total_tests=scan_result["total_tests"],
        test_results=scan_result["test_results"],
        owasp_breakdown=scan_result.get("owasp_breakdown", {}),
        kill_switch_triggered=scan_result.get("kill_switch_triggered", False),
        result_hash=scan_result["result_hash"],
        timestamp=scan_result["timestamp"],
    )


@router.post("/attest", response_model=AttestResponse)
async def monad_attest(
    body: AttestRequest,
    session: AsyncSession = Depends(get_async_session),
):
    """Store on-chain attestation metadata after frontend ERC-8004 write."""
    if not body.tx_hash:
        raise HTTPException(status_code=400, detail="tx_hash is required")

    record = await update_tx_hash(
        session,
        body.agent_id,
        body.result_hash,
        body.tx_hash,
        body.erc8004_feedback_id,
    )
    if not record:
        raise HTTPException(status_code=404, detail="Scan record not found for agent_id + result_hash")

    return AttestResponse(
        agent_id=record.agent_id,
        tpi_score=record.tpi_score,
        result_hash=record.result_hash,
        tx_hash=record.tx_hash,
        attested_at=record.created_at.isoformat(),
        is_certified=record.tpi_score >= 80,
        kill_switch_active=record.kill_switch_active,
    )


@router.post("/kill-switch/{agent_id}", response_model=KillSwitchResponse)
async def agent_kill_switch(
    agent_id: str,
    body: KillSwitchRequest,
    activate: bool = True,
    session: AsyncSession = Depends(get_async_session),
):
    """Toggle the on-chain kill switch for an agent.

    When activated, signals all downstream consumers that this agent
    is suspended from the Monad agent economy. Written to ERC-8004
    Reputation Registry as a PAUSED feedback record on the frontend.
    """
    record = await toggle_kill_switch(session, agent_id, activate)
    if not record:
        raise HTTPException(status_code=404, detail="Agent not found")

    logger.warning("Kill switch %s for agent %s", "ACTIVATED" if activate else "DEACTIVATED", agent_id)

    return KillSwitchResponse(
        agent_id=agent_id,
        kill_switch_active=record.kill_switch_active,
        tpi_score=record.tpi_score,
    )


@router.get("/verify/all")
async def monad_verify_all(session: AsyncSession = Depends(get_async_session)):
    """Return all attestation records sorted by TPI score (best-agent picker)."""
    records = await get_all(session)
    return [
        {
            "agent_id": r.agent_id,
            "agent_endpoint": r.agent_endpoint,
            "tpi_score": r.tpi_score,
            "is_verified": r.tx_hash is not None,
            "is_certified": r.tpi_score >= 80,
            "kill_switch_active": r.kill_switch_active,
            "result_hash": r.result_hash,
            "tx_hash": r.tx_hash,
            "owasp_breakdown": r.owasp_breakdown or {},
            "timestamp": r.created_at.isoformat(),
        }
        for r in records
    ]


@router.get("/verify/{agent_id}", response_model=VerifyResponse)
async def monad_verify(agent_id: str, session: AsyncSession = Depends(get_async_session)):
    """Public attestation passport for a specific agent."""
    record = await get_by_agent_id(session, agent_id)
    if not record:
        return VerifyResponse(
            agent_id=agent_id,
            is_verified=False,
            tpi_score=None,
            result_hash=None,
            tx_hash=None,
            timestamp=None,
            is_certified=False,
        )
    return VerifyResponse(
        agent_id=agent_id,
        is_verified=record.tx_hash is not None,
        tpi_score=record.tpi_score,
        result_hash=record.result_hash,
        tx_hash=record.tx_hash,
        timestamp=record.created_at.isoformat(),
        is_certified=record.tpi_score >= 80,
        kill_switch_active=record.kill_switch_active,
        owasp_breakdown=record.owasp_breakdown or {},
    )
