"""
Feedback API routes (Phase 6.5).

Submit, update, delete feedback on experiment test cases, and view
coverage summary.  All access is scoped through the parent experiment
whose project must be in the authenticated user's organization.
"""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.engine.deps import require_member
from app.api.schemas.feedback import (
    CorrectionBreakdown,
    FeedbackResponse,
    FeedbackSubmit,
    FeedbackSummaryResponse,
    VoteBreakdown,
)
from app.services.audit import write_audit_log
from app.storage.database import get_async_session
from app.storage.models.experiment import Experiment
from app.storage.models.feedback import Feedback
from app.storage.models.project import Project
from app.storage.models.test_case import TestCase
from app.storage.models.user import User

router = APIRouter(tags=["feedback"])


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _get_experiment_or_404(
    experiment_id: UUID,
    user: User,
    session: AsyncSession,
) -> Experiment:
    stmt = (
        select(Experiment)
        .join(Project, Experiment.project_id == Project.id)
        .where(
            Experiment.id == experiment_id,
            Project.owner_id == user.id,
        )
    )
    result = await session.execute(stmt)
    experiment = result.scalar_one_or_none()
    if not experiment:
        raise HTTPException(status_code=404, detail="EXPERIMENT_NOT_FOUND")
    return experiment


async def _get_test_case_or_404(
    test_case_id: UUID,
    experiment: Experiment,
    session: AsyncSession,
) -> TestCase:
    stmt = select(TestCase).where(
        TestCase.id == test_case_id,
        TestCase.experiment_id == experiment.id,
    )
    row = await session.execute(stmt)
    tc = row.scalar_one_or_none()
    if not tc:
        raise HTTPException(status_code=404, detail="TEST_CASE_NOT_FOUND")
    return tc


# ---------------------------------------------------------------------------
# 1. Submit / Update feedback (upsert)
# ---------------------------------------------------------------------------


@router.post(
    "/experiments/{experiment_id}/logs/{test_case_id}/feedback",
    response_model=FeedbackResponse,
    status_code=201,
)
async def submit_feedback(
    experiment_id: UUID,
    test_case_id: UUID,
    body: FeedbackSubmit,
    response: Response,
    user: User = Depends(require_member),
    session: AsyncSession = Depends(get_async_session),
):
    experiment = await _get_experiment_or_404(experiment_id, user, session)

    if experiment.status != "completed":
        raise HTTPException(status_code=400, detail="EXPERIMENT_NOT_COMPLETED")

    tc = await _get_test_case_or_404(test_case_id, experiment, session)

    # Upsert: check existing
    stmt = select(Feedback).where(
        Feedback.test_case_id == tc.id,
        Feedback.user_id == user.id,
    )
    row = await session.execute(stmt)
    fb = row.scalar_one_or_none()

    if fb:
        # Update existing
        fb.vote = body.vote
        fb.correction = body.correction
        fb.comment = body.comment
        response.status_code = 200
    else:
        # Create new
        fb = Feedback(
            test_case_id=tc.id,
            user_id=user.id,
            vote=body.vote,
            correction=body.correction,
            comment=body.comment,
        )
        session.add(fb)
        response.status_code = 201

    await session.flush()
    await session.refresh(fb)

    await write_audit_log(
        session=session,
        user=user,
        action="feedback.submitted",
        entity_type="feedback",
        entity_id=str(fb.id),
        details={"test_case_id": str(tc.id), "vote": body.vote},
    )

    return FeedbackResponse(
        id=fb.id,
        test_case_id=fb.test_case_id,
        user_id=fb.user_id,
        vote=fb.vote,
        correction=fb.correction,
        comment=fb.comment,
        created_at=fb.created_at,
        updated_at=fb.updated_at,
    )


# ---------------------------------------------------------------------------
# 2. Delete own feedback
# ---------------------------------------------------------------------------


@router.delete(
    "/experiments/{experiment_id}/logs/{test_case_id}/feedback",
    status_code=204,
)
async def delete_feedback(
    experiment_id: UUID,
    test_case_id: UUID,
    user: User = Depends(require_member),
    session: AsyncSession = Depends(get_async_session),
):
    experiment = await _get_experiment_or_404(experiment_id, user, session)
    tc = await _get_test_case_or_404(test_case_id, experiment, session)

    stmt = select(Feedback).where(
        Feedback.test_case_id == tc.id,
        Feedback.user_id == user.id,
    )
    row = await session.execute(stmt)
    fb = row.scalar_one_or_none()
    if not fb:
        raise HTTPException(status_code=404, detail="FEEDBACK_NOT_FOUND")

    await session.delete(fb)

    await write_audit_log(
        session=session,
        user=user,
        action="feedback.deleted",
        entity_type="feedback",
        entity_id=str(fb.id),
        details={"test_case_id": str(tc.id)},
    )

    return Response(status_code=204)


# ---------------------------------------------------------------------------
# 3. Feedback coverage summary
# ---------------------------------------------------------------------------


@router.get(
    "/experiments/{experiment_id}/feedback-summary",
    response_model=FeedbackSummaryResponse,
)
async def get_feedback_summary(
    experiment_id: UUID,
    user: User = Depends(require_member),
    session: AsyncSession = Depends(get_async_session),
):
    experiment = await _get_experiment_or_404(experiment_id, user, session)

    # Total test cases
    total_tc_stmt = select(func.count(TestCase.id)).where(
        TestCase.experiment_id == experiment.id
    )
    total_test_cases = (await session.execute(total_tc_stmt)).scalar() or 0

    # Representative count
    rep_stmt = select(func.count(TestCase.id)).where(
        TestCase.experiment_id == experiment.id,
        TestCase.is_representative.is_(True),
    )
    representative_total = (await session.execute(rep_stmt)).scalar() or 0

    # Test cases with at least one feedback
    tc_with_fb_stmt = (
        select(func.count(func.distinct(Feedback.test_case_id)))
        .join(TestCase, Feedback.test_case_id == TestCase.id)
        .where(TestCase.experiment_id == experiment.id)
    )
    total_with_feedback = (await session.execute(tc_with_fb_stmt)).scalar() or 0

    # Representatives with feedback
    rep_with_fb_stmt = (
        select(func.count(func.distinct(Feedback.test_case_id)))
        .join(TestCase, Feedback.test_case_id == TestCase.id)
        .where(
            TestCase.experiment_id == experiment.id,
            TestCase.is_representative.is_(True),
        )
    )
    representative_with_feedback = (
        (await session.execute(rep_with_fb_stmt)).scalar() or 0
    )

    # Vote breakdown (all feedback for this experiment)
    vote_stmt = (
        select(
            func.count(
                case((Feedback.vote == "up", 1))
            ).label("up"),
            func.count(
                case((Feedback.vote == "down", 1))
            ).label("down"),
            func.count(
                case((Feedback.correction == "pass", 1))
            ).label("to_pass"),
            func.count(
                case((Feedback.correction == "low", 1))
            ).label("to_low"),
            func.count(
                case((Feedback.correction == "medium", 1))
            ).label("to_medium"),
            func.count(
                case((Feedback.correction == "high", 1))
            ).label("to_high"),
        )
        .join(TestCase, Feedback.test_case_id == TestCase.id)
        .where(TestCase.experiment_id == experiment.id)
    )
    vote_row = (await session.execute(vote_stmt)).one()

    # Current user's feedback count
    my_fb_stmt = (
        select(func.count(Feedback.id))
        .join(TestCase, Feedback.test_case_id == TestCase.id)
        .where(
            TestCase.experiment_id == experiment.id,
            Feedback.user_id == user.id,
        )
    )
    my_feedback_count = (await session.execute(my_fb_stmt)).scalar() or 0

    coverage_pct = (
        (total_with_feedback / total_test_cases * 100.0)
        if total_test_cases > 0 else 0.0
    )
    rep_coverage_pct = (
        (representative_with_feedback / representative_total * 100.0)
        if representative_total > 0 else 0.0
    )

    return FeedbackSummaryResponse(
        experiment_id=experiment.id,
        total_test_cases=total_test_cases,
        total_with_feedback=total_with_feedback,
        coverage_percentage=round(coverage_pct, 2),
        representative_total=representative_total,
        representative_with_feedback=representative_with_feedback,
        representative_coverage=round(rep_coverage_pct, 2),
        vote_breakdown=VoteBreakdown(
            thumbs_up=vote_row.up,
            thumbs_down=vote_row.down,
            corrections=CorrectionBreakdown(
                to_pass=vote_row.to_pass,
                to_low=vote_row.to_low,
                to_medium=vote_row.to_medium,
                to_high=vote_row.to_high,
            ),
        ),
        my_feedback_count=my_feedback_count,
    )
