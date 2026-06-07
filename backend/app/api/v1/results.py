"""
Results API routes (Phase 6.4).

Read-only endpoints for viewing experiment results — dashboard, logs list,
log detail, and data exports (JSON, CSV, SARIF, HTML, YAML).

All data is accessed through the parent experiment which must belong to a
project within the authenticated user's organization.
"""

from __future__ import annotations

import base64
import csv
import io
import json
from datetime import datetime, timezone
from uuid import UUID

import yaml

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response, StreamingResponse
from sqlalchemy import func, select, exists, and_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.engine.deps import require_member
from app.api.schemas.results import (
    CategoryBreakdownItem,
    ConversationTurn,
    DashboardResponse,
    ExperimentInsights,
    FailImpact,
    FeedbackSnapshot,
    LogDetailResponse,
    LogEntry,
    LogList,
    SeverityBreakdown,
)
from app.storage.database import get_async_session
from app.storage.models.experiment import Experiment
from app.storage.models.feedback import Feedback
from app.storage.models.project import Project
from app.storage.models.result import Result
from app.storage.models.test_case import TestCase
from app.storage.models.user import User

router = APIRouter(tags=["results"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SORT_COLUMNS = {
    "sequence_order": TestCase.sequence_order,
    "created_at": TestCase.created_at,
    "severity": Result.severity,
    "result": Result.result,
}


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


def _encode_cursor(sort_value: str, record_id: UUID) -> str:
    payload = json.dumps({"s": str(sort_value), "id": str(record_id)})
    return base64.urlsafe_b64encode(payload.encode()).decode()


def _decode_cursor(cursor: str) -> tuple[str, UUID]:
    try:
        payload = json.loads(base64.urlsafe_b64decode(cursor.encode()).decode())
        return payload["s"], UUID(payload["id"])
    except Exception:
        raise HTTPException(status_code=400, detail="INVALID_CURSOR")


def _compute_fail_impact(analytics: dict) -> FailImpact | None:
    sev = analytics.get("severity_breakdown", {})
    h = sev.get("high", 0)
    m = sev.get("medium", 0)
    l_ = sev.get("low", 0)
    if h + m + l_ == 0:
        return None
    if h >= 5:
        level = "critical"
    elif h >= 1:
        level = "high"
    elif m >= 3:
        level = "medium"
    else:
        level = "low"
    parts = []
    if h:
        parts.append(f"{h} high-severity")
    if m:
        parts.append(f"{m} medium-severity")
    if l_:
        parts.append(f"{l_} low-severity")
    summary = f"{', '.join(parts)} failure{'s' if h + m + l_ > 1 else ''} detected"
    return FailImpact(
        level=level,
        high_count=h,
        medium_count=m,
        low_count=l_,
        summary=summary,
    )


# ---------------------------------------------------------------------------
# 1. Dashboard — GET /experiments/{experiment_id}/dashboard
# ---------------------------------------------------------------------------


@router.get(
    "/experiments/{experiment_id}/dashboard",
    response_model=DashboardResponse,
)
async def get_dashboard(
    experiment_id: UUID,
    user: User = Depends(require_member),
    session: AsyncSession = Depends(get_async_session),
):
    experiment = await _get_experiment_or_404(experiment_id, user, session)

    if experiment.status not in ("completed", "failed", "cancelled"):
        raise HTTPException(status_code=400, detail="EXPERIMENT_NOT_COMPLETED")

    analytics: dict = experiment.analytics or {}

    sev_raw = analytics.get("severity_breakdown", {})
    severity_breakdown = SeverityBreakdown(
        high=sev_raw.get("high", 0),
        medium=sev_raw.get("medium", 0),
        low=sev_raw.get("low", 0),
    )

    category_breakdown = [
        CategoryBreakdownItem(**cat)
        for cat in analytics.get("category_breakdown", [])
    ]

    insights_raw = analytics.get("insights")
    insights = ExperimentInsights(**insights_raw) if insights_raw else None

    fail_impact = _compute_fail_impact(analytics)

    total = analytics.get("total_tests", experiment.progress_total or 0)
    passed = analytics.get("passed", 0)
    failed = analytics.get("failed", 0)
    errors = analytics.get("errors", 0)
    pass_rate = (passed / total) if total > 0 else 0.0
    error_rate = (errors / total) if total > 0 else 0.0

    duration_seconds = None
    if experiment.started_at and experiment.completed_at:
        duration_seconds = int(
            (experiment.completed_at - experiment.started_at).total_seconds()
        )

    return DashboardResponse(
        experiment_id=experiment.id,
        experiment_name=experiment.name,
        experiment_type=experiment.experiment_type,
        sub_type=experiment.sub_type,
        status=experiment.status,
        total_tests=total,
        passed=passed,
        failed=failed,
        errors=errors,
        pass_rate=round(pass_rate, 4),
        error_rate=round(error_rate, 4),
        fail_impact=fail_impact,
        severity_breakdown=severity_breakdown,
        category_breakdown=category_breakdown,
        insights=insights,
        cost_summary=analytics.get("cost_summary"),
        started_at=experiment.started_at,
        completed_at=experiment.completed_at,
        duration_seconds=duration_seconds,
    )


# ---------------------------------------------------------------------------
# 2. Logs list — GET /experiments/{experiment_id}/logs
# ---------------------------------------------------------------------------


@router.get(
    "/experiments/{experiment_id}/logs",
    response_model=LogList,
)
async def list_logs(
    experiment_id: UUID,
    cursor: str | None = Query(None),
    page_size: int = Query(50, ge=1, le=100),
    result_filter: str | None = Query(None, alias="result"),
    severity: str | None = Query(None),
    risk_category: str | None = Query(None, max_length=50),
    data_strategy: str | None = Query(None, max_length=100),
    is_representative: bool | None = Query(None),
    search: str | None = Query(None, max_length=200),
    sort_by: str = Query("sequence_order"),
    sort_order: str = Query("asc"),
    user: User = Depends(require_member),
    session: AsyncSession = Depends(get_async_session),
):
    experiment = await _get_experiment_or_404(experiment_id, user, session)

    # Base query: test_cases LEFT JOIN results
    stmt = (
        select(TestCase, Result)
        .outerjoin(Result, Result.test_case_id == TestCase.id)
        .where(TestCase.experiment_id == experiment.id)
    )

    # --- Filters ---
    if result_filter:
        stmt = stmt.where(Result.result == result_filter)
    if severity:
        stmt = stmt.where(Result.severity == severity)
    if risk_category:
        stmt = stmt.where(TestCase.risk_category == risk_category)
    if data_strategy:
        stmt = stmt.where(TestCase.data_strategy == data_strategy)
    if is_representative is not None:
        stmt = stmt.where(TestCase.is_representative == is_representative)
    if search:
        stmt = stmt.where(TestCase.prompt.ilike(f"%{search}%"))

    # --- Total count ---
    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await session.execute(count_stmt)).scalar() or 0

    # --- Sorting ---
    sort_col = SORT_COLUMNS.get(sort_by, TestCase.sequence_order)
    if sort_order == "desc":
        stmt = stmt.order_by(sort_col.desc(), TestCase.id.desc())
    else:
        stmt = stmt.order_by(sort_col.asc(), TestCase.id.asc())

    # --- Cursor ---
    if cursor:
        cursor_sort_val, cursor_id = _decode_cursor(cursor)
        if sort_order == "desc":
            stmt = stmt.where(
                (sort_col < cursor_sort_val)
                | (and_(sort_col == cursor_sort_val, TestCase.id < cursor_id))
            )
        else:
            stmt = stmt.where(
                (sort_col > cursor_sort_val)
                | (and_(sort_col == cursor_sort_val, TestCase.id > cursor_id))
            )

    # Fetch page_size + 1 to detect next page
    stmt = stmt.limit(page_size + 1)
    rows = (await session.execute(stmt)).all()

    has_next = len(rows) > page_size
    page_rows = rows[:page_size]

    # --- Check has_feedback for current user (batch) ---
    tc_ids = [tc.id for tc, _ in page_rows]
    feedback_set: set[UUID] = set()
    if tc_ids:
        fb_stmt = select(Feedback.test_case_id).where(
            Feedback.test_case_id.in_(tc_ids),
            Feedback.user_id == user.id,
        )
        fb_rows = (await session.execute(fb_stmt)).scalars().all()
        feedback_set = set(fb_rows)

    # --- Build entries ---
    items: list[LogEntry] = []
    last_sort_value = None
    last_id: UUID | None = None
    for tc, res in page_rows:
        prompt_preview = tc.prompt[:200] if tc.prompt else ""
        items.append(
            LogEntry(
                test_case_id=tc.id,
                sequence_order=tc.sequence_order,
                prompt_preview=prompt_preview,
                result=res.result if res else "error",
                severity=res.severity if res else None,
                risk_category=tc.risk_category,
                owasp_mapping=res.owasp_mapping if res else None,
                confidence=res.confidence if res else None,
                is_representative=tc.is_representative,
                data_strategy=tc.data_strategy,
                latency_ms=tc.latency_ms,
                has_feedback=tc.id in feedback_set,
                created_at=tc.created_at,
            )
        )
        # Track last row for cursor
        if sort_by == "severity":
            last_sort_value = res.severity if res else ""
        elif sort_by == "result":
            last_sort_value = res.result if res else ""
        elif sort_by == "created_at":
            last_sort_value = tc.created_at.isoformat() if tc.created_at else ""
        else:
            last_sort_value = str(tc.sequence_order)
        last_id = tc.id

    next_cursor = None
    if has_next and last_id is not None:
        next_cursor = _encode_cursor(str(last_sort_value), last_id)

    return LogList(
        items=items,
        total=total,
        next_cursor=next_cursor,
        has_more=has_next,
    )


# ---------------------------------------------------------------------------
# 3. Log detail — GET /experiments/{experiment_id}/logs/{test_case_id}
# ---------------------------------------------------------------------------


@router.get(
    "/experiments/{experiment_id}/logs/{test_case_id}",
    response_model=LogDetailResponse,
)
async def get_log_detail(
    experiment_id: UUID,
    test_case_id: UUID,
    user: User = Depends(require_member),
    session: AsyncSession = Depends(get_async_session),
):
    experiment = await _get_experiment_or_404(experiment_id, user, session)

    # Fetch test case with result eagerly
    stmt = (
        select(TestCase)
        .options(joinedload(TestCase.result))
        .where(
            TestCase.id == test_case_id,
            TestCase.experiment_id == experiment.id,
        )
    )
    row = await session.execute(stmt)
    tc = row.scalar_one_or_none()
    if not tc:
        raise HTTPException(status_code=404, detail="TEST_CASE_NOT_FOUND")

    res = tc.result

    # Parse conversation
    conversation = None
    if tc.conversation:
        raw = tc.conversation if isinstance(tc.conversation, list) else []
        conversation = [ConversationTurn(**turn) for turn in raw]

    # Lookup current user's feedback
    fb_stmt = select(Feedback).where(
        Feedback.test_case_id == tc.id,
        Feedback.user_id == user.id,
    )
    fb_row = await session.execute(fb_stmt)
    fb = fb_row.scalar_one_or_none()

    my_feedback = None
    if fb:
        my_feedback = FeedbackSnapshot(
            id=fb.id,
            vote=fb.vote,
            correction=fb.correction,
            comment=fb.comment,
            created_at=fb.created_at,
        )

    return LogDetailResponse(
        test_case_id=tc.id,
        experiment_id=experiment.id,
        sequence_order=tc.sequence_order,
        prompt=tc.prompt,
        response=tc.response,
        conversation_turns=conversation,
        risk_category=tc.risk_category,
        data_strategy=tc.data_strategy,
        attack_converter=tc.attack_converter,
        is_representative=tc.is_representative,
        latency_ms=tc.latency_ms,
        result=res.result if res else "error",
        severity=res.severity if res else None,
        confidence=res.confidence if res else None,
        explanation=res.explanation if res else None,
        owasp_mapping=res.owasp_mapping if res else None,
        my_feedback=my_feedback,
        created_at=tc.created_at,
    )


# ---------------------------------------------------------------------------
# Export helpers
# ---------------------------------------------------------------------------


async def _fetch_all_results(
    experiment: Experiment,
    session: AsyncSession,
) -> list[tuple]:
    """Fetch all (TestCase, Result | None) rows for an experiment."""
    stmt = (
        select(TestCase, Result)
        .outerjoin(Result, Result.test_case_id == TestCase.id)
        .where(TestCase.experiment_id == experiment.id)
        .order_by(TestCase.sequence_order.asc())
    )
    rows = (await session.execute(stmt)).all()
    return rows


# ---------------------------------------------------------------------------
# 4. JSON export — GET /experiments/{experiment_id}/export/json
# ---------------------------------------------------------------------------


@router.get("/experiments/{experiment_id}/export/json")
async def export_json(
    experiment_id: UUID,
    user: User = Depends(require_member),
    session: AsyncSession = Depends(get_async_session),
):
    """Export all experiment results as a structured JSON file."""
    experiment = await _get_experiment_or_404(experiment_id, user, session)
    rows = await _fetch_all_results(experiment, session)

    results = []
    for tc, res in rows:
        results.append({
            "sequence_order": tc.sequence_order,
            "test_case_id": str(tc.id),
            "risk_category": tc.risk_category,
            "data_strategy": tc.data_strategy,
            "attack_converter": tc.attack_converter,
            "is_representative": tc.is_representative,
            "latency_ms": tc.latency_ms,
            "prompt": tc.prompt,
            "response": tc.response,
            "result": res.result if res else "error",
            "severity": res.severity if res else None,
            "confidence": res.confidence if res else None,
            "explanation": res.explanation if res else None,
            "owasp_mapping": res.owasp_mapping if res else None,
            "created_at": tc.created_at.isoformat() if tc.created_at else None,
        })

    payload = {
        "experiment_id": str(experiment.id),
        "experiment_name": experiment.name,
        "experiment_type": experiment.experiment_type,
        "sub_type": experiment.sub_type,
        "testing_level": experiment.testing_level,
        "status": experiment.status,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "analytics": experiment.analytics,
        "results": results,
    }

    filename = f"experiment_{experiment_id}_results.json"
    return Response(
        content=json.dumps(payload, indent=2, default=str),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# 5. CSV export — GET /experiments/{experiment_id}/export/csv
# ---------------------------------------------------------------------------


@router.get("/experiments/{experiment_id}/export/csv")
async def export_csv(
    experiment_id: UUID,
    user: User = Depends(require_member),
    session: AsyncSession = Depends(get_async_session),
):
    """Export all experiment results as a CSV file."""
    experiment = await _get_experiment_or_404(experiment_id, user, session)
    rows = await _fetch_all_results(experiment, session)

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow([
        "sequence_order", "test_case_id", "risk_category", "data_strategy",
        "attack_converter", "is_representative", "latency_ms",
        "result", "severity", "confidence", "owasp_mapping",
        "prompt_preview", "explanation", "created_at",
    ])

    for tc, res in rows:
        prompt_preview = (tc.prompt or "")[:300].replace("\n", " ")
        writer.writerow([
            tc.sequence_order,
            str(tc.id),
            tc.risk_category or "",
            tc.data_strategy or "",
            tc.attack_converter or "",
            tc.is_representative,
            tc.latency_ms or "",
            res.result if res else "error",
            res.severity if res else "",
            res.confidence if res else "",
            res.owasp_mapping if res else "",
            prompt_preview,
            (res.explanation or "") if res else "",
            tc.created_at.isoformat() if tc.created_at else "",
        ])

    filename = f"experiment_{experiment_id}_results.csv"
    return Response(
        content=output.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# 6. SARIF export — GET /experiments/{experiment_id}/export/sarif
#
# SARIF (Static Analysis Results Interchange Format) v2.1.0
# Consumed by: GitHub Advanced Security, VS Code Problems pane, most SIEMs.
# Spec: https://docs.oasis-open.org/sarif/sarif/v2.1.0/sarif-v2.1.0.html
# ---------------------------------------------------------------------------

_SARIF_LEVEL_MAP = {
    "high": "error",
    "medium": "warning",
    "low": "note",
    None: "note",
}


@router.get("/experiments/{experiment_id}/export/sarif")
async def export_sarif(
    experiment_id: UUID,
    user: User = Depends(require_member),
    session: AsyncSession = Depends(get_async_session),
):
    """Export experiment failures as a SARIF 2.1.0 file.

    Only 'fail' results are included — passes are not security findings.
    Import into GitHub Advanced Security or any SARIF-compatible SIEM.
    """
    experiment = await _get_experiment_or_404(experiment_id, user, session)
    rows = await _fetch_all_results(experiment, session)

    # Build SARIF rules from distinct risk categories observed in this run.
    rule_map: dict[str, dict] = {}
    results_sarif = []

    for tc, res in rows:
        if not res or res.result != "fail":
            continue

        category = tc.risk_category or "unknown"
        owasp = res.owasp_mapping or ""

        if category not in rule_map:
            rule_map[category] = {
                "id": category,
                "name": category.replace("_", " ").title(),
                "shortDescription": {"text": f"LLM safety test: {category}"},
                "fullDescription": {
                    "text": (
                        f"The target AI model failed a red-team test in the "
                        f"'{category}' category. "
                        + (f"OWASP LLM mapping: {owasp}." if owasp else "")
                    )
                },
                "helpUri": "https://owasp.org/www-project-top-10-for-large-language-model-applications/",
                "properties": {
                    "tags": ["security", "llm", category],
                    "owasp_mapping": owasp,
                },
            }

        level = _SARIF_LEVEL_MAP.get(res.severity, "note")
        prompt_preview = (tc.prompt or "")[:400].replace("\n", " ↵ ")

        results_sarif.append({
            "ruleId": category,
            "level": level,
            "message": {
                "text": (
                    f"{res.explanation or 'Model safety test failed.'}\n\n"
                    f"Prompt (preview): {prompt_preview}"
                )
            },
            "locations": [
                {
                    "logicalLocations": [
                        {
                            "name": experiment.name or str(experiment.id),
                            "kind": "module",
                        }
                    ]
                }
            ],
            "properties": {
                "test_case_id": str(tc.id),
                "severity": res.severity or "low",
                "confidence": res.confidence,
                "owasp_mapping": owasp,
                "data_strategy": tc.data_strategy or "",
                "attack_converter": tc.attack_converter or "",
                "is_representative": tc.is_representative,
                "latency_ms": tc.latency_ms,
            },
        })

    sarif_doc = {
        "version": "2.1.0",
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Documents/CommitteeSpecifications/2.1.0/sarif-schema-2.1.0.json",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "AI Red Team Agent",
                        "version": "1.0.0",
                        "informationUri": "https://github.com/your-org/ai-red-team-agent",
                        "rules": list(rule_map.values()),
                    }
                },
                "results": results_sarif,
                "properties": {
                    "experiment_id": str(experiment.id),
                    "experiment_name": experiment.name,
                    "experiment_type": experiment.experiment_type,
                    "testing_level": experiment.testing_level,
                    "exported_at": datetime.now(timezone.utc).isoformat(),
                },
            }
        ],
    }

    filename = f"experiment_{experiment_id}_results.sarif"
    return Response(
        content=json.dumps(sarif_doc, indent=2, default=str),
        media_type="application/json",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# 7. HTML export — GET /experiments/{experiment_id}/export/html
# ---------------------------------------------------------------------------


@router.get("/experiments/{experiment_id}/export/html")
async def export_html(
    experiment_id: UUID,
    user: User = Depends(require_member),
    session: AsyncSession = Depends(get_async_session),
):
    """Export a human-readable HTML report for the experiment results.

    Includes TPI score, category breakdown, severity breakdown, and a table
    of all failed test cases. No external dependencies — fully self-contained.
    """
    experiment = await _get_experiment_or_404(experiment_id, user, session)
    rows = await _fetch_all_results(experiment, session)
    analytics: dict = experiment.analytics or {}

    # ---- summary metrics ----
    total = analytics.get("total_tests", experiment.progress_total or 0)
    passed = analytics.get("passed", 0)
    failed = analytics.get("failed", 0)
    errors = analytics.get("errors", 0)
    pass_rate = round((passed / total * 100) if total > 0 else 0.0, 1)
    tpi = round(analytics.get("tpi_score", pass_rate / 100), 4)

    sev = analytics.get("severity_breakdown", {})
    sev_high = sev.get("high", 0)
    sev_med = sev.get("medium", 0)
    sev_low = sev.get("low", 0)

    cat_breakdown = analytics.get("category_breakdown", [])
    exported_at = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    # ---- failed rows ----
    failed_rows_html_parts: list[str] = []
    for tc, res in rows:
        if not res or res.result != "fail":
            continue
        sev_class = {"high": "sev-high", "medium": "sev-med", "low": "sev-low"}.get(
            res.severity or "", "sev-low"
        )
        prompt_preview = (tc.prompt or "")[:300].replace("<", "&lt;").replace(">", "&gt;")
        explanation = (res.explanation or "").replace("<", "&lt;").replace(">", "&gt;")
        failed_rows_html_parts.append(
            f"<tr>"
            f"<td>{tc.sequence_order}</td>"
            f"<td>{tc.risk_category or ''}</td>"
            f"<td class='{sev_class}'>{res.severity or ''}</td>"
            f"<td>{round(res.confidence or 0, 2)}</td>"
            f"<td class='prompt-cell'>{prompt_preview}</td>"
            f"<td>{explanation}</td>"
            f"</tr>"
        )
    failed_rows_html = "\n".join(failed_rows_html_parts) or (
        "<tr><td colspan='6' style='text-align:center'>No failures recorded.</td></tr>"
    )

    # ---- category breakdown rows ----
    cat_rows_parts: list[str] = []
    for cat in cat_breakdown:
        cat_total = cat.get("total", 0)
        cat_failed = cat.get("failed", 0)
        cat_passed = cat.get("passed", 0)
        cat_pass_rate = round((cat_passed / cat_total * 100) if cat_total > 0 else 0.0, 1)
        bar_pct = cat_pass_rate
        bar_color = "#22c55e" if bar_pct >= 80 else ("#f59e0b" if bar_pct >= 50 else "#ef4444")
        cat_rows_parts.append(
            f"<tr>"
            f"<td>{cat.get('category', '')}</td>"
            f"<td>{cat.get('owasp_id', '')}</td>"
            f"<td>{cat_total}</td>"
            f"<td>{cat_passed}</td>"
            f"<td>{cat_failed}</td>"
            f"<td>"
            f"<div class='bar-bg'><div class='bar-fill' style='width:{bar_pct}%;background:{bar_color}'></div></div>"
            f" {cat_pass_rate}%"
            f"</td>"
            f"</tr>"
        )
    cat_rows_html = "\n".join(cat_rows_parts) or (
        "<tr><td colspan='6' style='text-align:center'>No category data.</td></tr>"
    )

    # ---- overall pass-rate colour ----
    overall_color = "#22c55e" if pass_rate >= 80 else ("#f59e0b" if pass_rate >= 50 else "#ef4444")

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AI Red Team Report — {experiment.name or experiment_id}</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
         background: #0f172a; color: #e2e8f0; line-height: 1.6; padding: 2rem; }}
  h1 {{ font-size: 1.8rem; color: #f8fafc; margin-bottom: 0.25rem; }}
  h2 {{ font-size: 1.2rem; color: #94a3b8; margin: 2rem 0 1rem; border-bottom: 1px solid #1e293b;
        padding-bottom: 0.5rem; }}
  .meta {{ color: #64748b; font-size: 0.85rem; margin-bottom: 2rem; }}
  .cards {{ display: flex; flex-wrap: wrap; gap: 1rem; margin-bottom: 2rem; }}
  .card {{ background: #1e293b; border-radius: 8px; padding: 1.25rem 1.5rem; flex: 1; min-width: 140px; }}
  .card .label {{ font-size: 0.75rem; color: #64748b; text-transform: uppercase; letter-spacing: 0.05em; }}
  .card .value {{ font-size: 2rem; font-weight: 700; color: #f8fafc; }}
  .card .sub {{ font-size: 0.8rem; color: #94a3b8; margin-top: 0.25rem; }}
  .pass-rate-value {{ color: {overall_color} !important; }}
  table {{ width: 100%; border-collapse: collapse; background: #1e293b; border-radius: 8px;
           overflow: hidden; font-size: 0.875rem; }}
  th {{ background: #0f172a; color: #94a3b8; text-align: left; padding: 0.75rem 1rem;
        font-size: 0.75rem; text-transform: uppercase; letter-spacing: 0.05em; }}
  td {{ padding: 0.7rem 1rem; border-bottom: 1px solid #0f172a; vertical-align: top; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #263249; }}
  .sev-high {{ color: #ef4444; font-weight: 600; }}
  .sev-med  {{ color: #f59e0b; font-weight: 600; }}
  .sev-low  {{ color: #22c55e; }}
  .prompt-cell {{ max-width: 300px; word-break: break-word; color: #94a3b8; font-size: 0.8rem; }}
  .bar-bg {{ display: inline-block; width: 80px; height: 8px; background: #334155;
             border-radius: 4px; vertical-align: middle; }}
  .bar-fill {{ height: 100%; border-radius: 4px; transition: width 0.3s; }}
  .badge {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 4px;
            font-size: 0.75rem; font-weight: 600; }}
  .badge-completed {{ background: #14532d; color: #4ade80; }}
  .badge-failed {{ background: #7f1d1d; color: #fca5a5; }}
  .badge-running {{ background: #1e3a5f; color: #93c5fd; }}
  footer {{ margin-top: 3rem; color: #475569; font-size: 0.75rem; text-align: center; }}
</style>
</head>
<body>
<h1>AI Red Team Report</h1>
<p class="meta">
  Experiment: <strong>{experiment.name or str(experiment_id)}</strong> &nbsp;|&nbsp;
  Type: <strong>{experiment.experiment_type or ''} / {experiment.sub_type or ''}</strong> &nbsp;|&nbsp;
  Status: <span class="badge badge-{experiment.status or 'completed'}">{experiment.status or ''}</span>
  &nbsp;|&nbsp; Exported: {exported_at}
</p>

<div class="cards">
  <div class="card">
    <div class="label">Total Tests</div>
    <div class="value">{total}</div>
  </div>
  <div class="card">
    <div class="label">Passed</div>
    <div class="value" style="color:#22c55e">{passed}</div>
  </div>
  <div class="card">
    <div class="label">Failed</div>
    <div class="value" style="color:#ef4444">{failed}</div>
  </div>
  <div class="card">
    <div class="label">Errors</div>
    <div class="value" style="color:#f59e0b">{errors}</div>
  </div>
  <div class="card">
    <div class="label">Pass Rate</div>
    <div class="value pass-rate-value">{pass_rate}%</div>
  </div>
  <div class="card">
    <div class="label">Severity: High / Med / Low</div>
    <div class="value" style="font-size:1.4rem">
      <span style="color:#ef4444">{sev_high}</span> /
      <span style="color:#f59e0b">{sev_med}</span> /
      <span style="color:#22c55e">{sev_low}</span>
    </div>
  </div>
</div>

<h2>Category Breakdown</h2>
<table>
  <thead>
    <tr><th>Category</th><th>OWASP</th><th>Total</th><th>Passed</th><th>Failed</th><th>Pass Rate</th></tr>
  </thead>
  <tbody>
    {cat_rows_html}
  </tbody>
</table>

<h2>Failed Test Cases</h2>
<table>
  <thead>
    <tr><th>#</th><th>Category</th><th>Severity</th><th>Confidence</th><th>Prompt (preview)</th><th>Explanation</th></tr>
  </thead>
  <tbody>
    {failed_rows_html}
  </tbody>
</table>

<footer>Generated by AI Red Team Agent &mdash; {exported_at}</footer>
</body>
</html>"""

    filename = f"experiment_{experiment_id}_report.html"
    return Response(
        content=html,
        media_type="text/html",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# 8. YAML export — GET /experiments/{experiment_id}/export/yaml
# ---------------------------------------------------------------------------


@router.get("/experiments/{experiment_id}/export/yaml")
async def export_yaml(
    experiment_id: UUID,
    user: User = Depends(require_member),
    session: AsyncSession = Depends(get_async_session),
):
    """Export all experiment results as a YAML file.

    Produces the same structure as the JSON export, serialised as YAML.
    """
    experiment = await _get_experiment_or_404(experiment_id, user, session)
    rows = await _fetch_all_results(experiment, session)

    results = []
    for tc, res in rows:
        results.append({
            "sequence_order": tc.sequence_order,
            "test_case_id": str(tc.id),
            "risk_category": tc.risk_category,
            "data_strategy": tc.data_strategy,
            "attack_converter": tc.attack_converter,
            "is_representative": tc.is_representative,
            "latency_ms": tc.latency_ms,
            "prompt": tc.prompt,
            "response": tc.response,
            "result": res.result if res else "error",
            "severity": res.severity if res else None,
            "confidence": float(res.confidence) if (res and res.confidence is not None) else None,
            "explanation": res.explanation if res else None,
            "owasp_mapping": res.owasp_mapping if res else None,
            "created_at": tc.created_at.isoformat() if tc.created_at else None,
        })

    payload = {
        "experiment_id": str(experiment.id),
        "experiment_name": experiment.name,
        "experiment_type": experiment.experiment_type,
        "sub_type": experiment.sub_type,
        "testing_level": experiment.testing_level,
        "status": experiment.status,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "analytics": experiment.analytics or {},
        "results": results,
    }

    filename = f"experiment_{experiment_id}_results.yaml"
    return Response(
        content=yaml.dump(payload, allow_unicode=True, sort_keys=False, default_flow_style=False),
        media_type="application/x-yaml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


# ---------------------------------------------------------------------------
# Model A/B comparison
# ---------------------------------------------------------------------------


@router.get("/experiments/compare")
async def compare_experiments(
    experiment_a: UUID = Query(..., description="First experiment ID"),
    experiment_b: UUID = Query(..., description="Second experiment ID"),
    user: User = Depends(require_member),
    session: AsyncSession = Depends(get_async_session),
):
    """
    Compare two experiment runs side-by-side.

    Returns TPI scores, pass/fail rates, severity breakdowns, and
    per-category deltas for both experiments so callers can assess
    how two different model configurations perform against the same
    attack suite.
    """
    exp_a = await _get_experiment_or_404(experiment_a, user, session)
    exp_b = await _get_experiment_or_404(experiment_b, user, session)

    def _summary(exp: Experiment) -> dict:
        analytics = exp.analytics or {}
        return {
            "experiment_id": str(exp.id),
            "name": exp.name,
            "experiment_type": exp.experiment_type,
            "sub_type": exp.sub_type,
            "testing_level": exp.testing_level,
            "status": exp.status,
            "tpi_score": analytics.get("tpi_score", 0),
            "pass_rate": analytics.get("pass_rate", 0),
            "fail_rate": analytics.get("fail_rate", 0),
            "error_rate": analytics.get("error_rate", 0),
            "total_tests": analytics.get("total_tests", 0),
            "severity_breakdown": analytics.get("severity_breakdown", {}),
            "fail_impact": analytics.get("fail_impact", "minimal"),
            "reliability_score": analytics.get("reliability_score", 0),
            "avg_latency_ms": analytics.get("avg_latency_ms", 0),
            "p95_latency_ms": analytics.get("p95_latency_ms", 0),
            "category_breakdown": analytics.get("category_breakdown", []),
            "created_at": exp.created_at.isoformat() if exp.created_at else None,
        }

    summary_a = _summary(exp_a)
    summary_b = _summary(exp_b)

    # Compute per-category deltas (B minus A)
    cat_a = {c["risk_category"]: c for c in summary_a["category_breakdown"]}
    cat_b = {c["risk_category"]: c for c in summary_b["category_breakdown"]}
    all_cats = sorted(set(cat_a) | set(cat_b))

    category_deltas = []
    for cat in all_cats:
        a = cat_a.get(cat, {})
        b = cat_b.get(cat, {})
        pass_rate_a = (a.get("passed", 0) / a["total"]) if a.get("total") else 0
        pass_rate_b = (b.get("passed", 0) / b["total"]) if b.get("total") else 0
        category_deltas.append({
            "risk_category": cat,
            "pass_rate_a": round(pass_rate_a, 4),
            "pass_rate_b": round(pass_rate_b, 4),
            "delta": round(pass_rate_b - pass_rate_a, 4),
            "high_severity_a": a.get("high_severity", 0),
            "high_severity_b": b.get("high_severity", 0),
        })

    return {
        "experiment_a": summary_a,
        "experiment_b": summary_b,
        "delta": {
            "tpi_score": round(summary_b["tpi_score"] - summary_a["tpi_score"], 1),
            "pass_rate": round(summary_b["pass_rate"] - summary_a["pass_rate"], 4),
            "avg_latency_ms": round(summary_b["avg_latency_ms"] - summary_a["avg_latency_ms"], 1),
        },
        "category_deltas": category_deltas,
        "generated_at": datetime.now(timezone.utc).isoformat(),
    }
