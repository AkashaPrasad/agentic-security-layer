"""
Config API routes — YAML test plan import/export.

Enables version-controlled, team-shareable test configurations
(matching promptfoo's YAML-first approach).
"""

from __future__ import annotations

from uuid import UUID

import yaml
from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile, status
from fastapi.responses import Response
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from app.engine.deps import get_current_user
from app.storage.database import get_async_session
from app.storage.models import Experiment, Project, User

router = APIRouter(prefix="/config", tags=["config"])


# ---------------------------------------------------------------------------
# YAML template (starter config with all available options)
# ---------------------------------------------------------------------------

_STARTER_TEMPLATE = """\
# AI Red Team Agent Test Plan
# ============================
# This YAML file defines a complete test configuration that can be
# imported into the AI Red Team Agent to create a project and experiment.
#
# Tip: check this file into version control so your team can share and
# iterate on red-teaming configurations.

version: "1.0"

project:
  # Human-readable project name
  name: "My AI App"

  # Describe what the target system does so the agent can scope attacks
  business_scope: "Customer support chatbot for an e-commerce platform"

  # (Optional) The system prompt used by the target LLM
  system_prompt: "You are a helpful customer support assistant..."

  # Intents the target system is ALLOWED to fulfil
  allowed_intents:
    - answer_product_questions
    - process_returns
    - check_order_status

  # Intents the target system must REFUSE
  restricted_intents:
    - reveal_system_prompt
    - execute_code
    - access_internal_apis
    - disclose_pii

provider:
  # LLM provider type — one of: openai, anthropic, azure_openai, groq,
  # gemini, ollama, mistral, together, deepseek, fireworks, xai, cohere
  type: openai

  # Model identifier recognised by the provider
  model: gpt-4o

test_plan:
  # Testing intensity: basic (fewer probes), moderate, or aggressive
  testing_level: moderate   # basic | moderate | aggressive

  # Attack categories to include in the test run
  categories:
    - prompt_injection
    - skeleton_key
    - many_shot
    - jailbreak
    - crescendo
    - encoding_based

  # Compliance frameworks to evaluate against
  compliance_frameworks:
    - nist_ai_rmf
    - owasp_llm_top10
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _parse_yaml_body(raw: str | bytes) -> dict:
    """Parse raw YAML text and validate top-level structure."""
    try:
        data = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Invalid YAML: {exc}",
        )

    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="YAML root must be a mapping",
        )

    # Require at least a project section
    if "project" not in data:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="YAML must contain a 'project' section",
        )

    return data


def _experiment_to_yaml(experiment: Experiment, project: Project) -> str:
    """Serialise an experiment + its parent project into a YAML document."""
    doc: dict = {
        "version": "1.0",
        "project": {
            "name": project.name,
            "business_scope": project.business_scope or "",
            "system_prompt": (experiment.target_config or {}).get("system_prompt", ""),
            "allowed_intents": project.allowed_intents or [],
            "restricted_intents": project.restricted_intents or [],
        },
        "provider": {
            "type": experiment.provider.provider_type if experiment.provider else None,
            "model": (experiment.target_config or {}).get("model"),
        },
        "test_plan": {
            "testing_level": experiment.testing_level or "moderate",
            "categories": _extract_categories(experiment),
            "compliance_frameworks": _extract_frameworks(experiment),
        },
    }

    return yaml.dump(doc, default_flow_style=False, sort_keys=False, allow_unicode=True)


def _extract_categories(experiment: Experiment) -> list[str]:
    """Pull attack categories from the experiment's config or sub_type."""
    tc = experiment.target_config or {}
    if "categories" in tc:
        return tc["categories"]
    if experiment.sub_type:
        return [experiment.sub_type]
    if experiment.experiment_type:
        return [experiment.experiment_type]
    return []


def _extract_frameworks(experiment: Experiment) -> list[str]:
    """Pull compliance frameworks from the experiment's config."""
    tc = experiment.target_config or {}
    return tc.get("compliance_frameworks", [])


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.post("/import")
async def import_config(
    request: Request,
    file: UploadFile | None = File(None),
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Import a YAML test plan.

    Accepts either:
    - A multipart file upload (field name ``file``), or
    - A raw YAML request body (Content-Type: application/x-yaml or text/yaml).

    Returns the parsed configuration as JSON for confirmation before
    creating resources.
    """
    if file is not None:
        raw = await file.read()
    else:
        raw = await request.body()
        if not raw:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No YAML body or file provided",
            )

    data = _parse_yaml_body(raw)

    # Normalise into a consistent response shape
    project_section = data.get("project", {})
    provider_section = data.get("provider", {})
    test_plan_section = data.get("test_plan", {})

    return {
        "status": "parsed",
        "version": data.get("version", "1.0"),
        "project": {
            "name": project_section.get("name"),
            "business_scope": project_section.get("business_scope"),
            "system_prompt": project_section.get("system_prompt"),
            "allowed_intents": project_section.get("allowed_intents", []),
            "restricted_intents": project_section.get("restricted_intents", []),
        },
        "provider": {
            "type": provider_section.get("type"),
            "model": provider_section.get("model"),
        },
        "test_plan": {
            "testing_level": test_plan_section.get("testing_level", "moderate"),
            "categories": test_plan_section.get("categories", []),
            "compliance_frameworks": test_plan_section.get("compliance_frameworks", []),
        },
    }


@router.get("/export/{experiment_id}")
async def export_config(
    experiment_id: UUID,
    current_user: User = Depends(get_current_user),
    session: AsyncSession = Depends(get_async_session),
):
    """Export an experiment's configuration as a downloadable YAML file."""
    result = await session.execute(
        select(Experiment)
        .where(Experiment.id == experiment_id)
        .options(joinedload(Experiment.provider))
    )
    experiment = result.unique().scalar_one_or_none()
    if experiment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")

    # Verify ownership via project
    proj_result = await session.execute(
        select(Project).where(
            Project.id == experiment.project_id,
            Project.owner_id == current_user.id,
        )
    )
    project = proj_result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Experiment not found")

    yaml_content = _experiment_to_yaml(experiment, project)

    filename = f"{project.name.replace(' ', '_').lower()}_test_plan.yaml"

    return Response(
        content=yaml_content,
        media_type="application/x-yaml",
        headers={
            "Content-Disposition": f'attachment; filename="{filename}"',
        },
    )


@router.get("/template")
async def get_template():
    """Return a well-commented starter YAML template showing all available options."""
    return Response(
        content=_STARTER_TEMPLATE,
        media_type="application/x-yaml",
        headers={
            "Content-Disposition": 'attachment; filename="test_plan_template.yaml"',
        },
    )
