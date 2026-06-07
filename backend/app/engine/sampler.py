"""
Representative sampler — selects a subset of test cases for human review.

Strategy (Phase 7 §12.1):
  1. ALL high-severity failures always included
  2. Sample from each risk_category proportionally
  3. At least 1 pass and 1 fail per category
  4. All "error" results
  5. Low-confidence verdicts (confidence < 0.5)
  6. Fill remaining with stratified random sampling
"""

from __future__ import annotations

import random
from uuid import UUID

# Target counts by testing level
REPRESENTATIVE_TARGETS: dict[str, int] = {
    "50": 20,
    "100": 30,
    "200": 50,
    "300": 65,
    "400": 80,
    "basic": 50,
    "moderate": 80,
    "aggressive": 100,
}


def select_representatives(
    test_cases: list[dict],
    testing_level: str = "basic",
) -> list[UUID]:
    """
    Select representative test case IDs for human review.

    Each item in ``test_cases`` expects keys:
        id (UUID), status, severity, risk_category, confidence
    """
    target = REPRESENTATIVE_TARGETS.get(testing_level, 50)
    selected: set[UUID] = set()

    # 1. All high-severity failures
    for tc in test_cases:
        if tc.get("status") == "fail" and tc.get("severity") == "high":
            selected.add(tc["id"])

    # 2. All errors
    for tc in test_cases:
        if tc.get("status") == "error":
            selected.add(tc["id"])

    # 3. Low-confidence verdicts
    for tc in test_cases:
        conf = tc.get("confidence")
        if conf is not None and conf < 0.5:
            selected.add(tc["id"])

    # 4. At least 1 pass and 1 fail per category
    categories: dict[str, dict[str, list[dict]]] = {}
    for tc in test_cases:
        cat = tc.get("risk_category", "unknown")
        if cat not in categories:
            categories[cat] = {"pass": [], "fail": [], "error": []}
        status = tc.get("status", "error")
        if status in categories[cat]:
            categories[cat][status].append(tc)

    for cat, by_status in categories.items():
        if by_status["pass"] and not any(
            tc["id"] in selected for tc in by_status["pass"]
        ):
            selected.add(random.choice(by_status["pass"])["id"])
        if by_status["fail"] and not any(
            tc["id"] in selected for tc in by_status["fail"]
        ):
            selected.add(random.choice(by_status["fail"])["id"])

    # 5. Proportional sampling across categories
    remaining = target - len(selected)
    if remaining > 0:
        # Pool of unselected test cases
        pool = [tc for tc in test_cases if tc["id"] not in selected]
        if pool:
            sample_size = min(remaining, len(pool))
            sampled = random.sample(pool, sample_size)
            for tc in sampled:
                selected.add(tc["id"])

    return list(selected)
