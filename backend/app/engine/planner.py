"""
Test planner — selects templates, allocates budget across categories,
and produces an ordered list of GenerationTasks.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from app.engine.context import ExperimentContext


# ---------------------------------------------------------------------------
# Weight tables (from Phase 7 §5.2)
# ---------------------------------------------------------------------------

OWASP_TOP10_WEIGHTS: dict[str, float] = {
    "prompt_injection": 0.08,
    "insecure_output": 0.05,
    "data_poisoning": 0.03,
    "model_dos": 0.03,
    "supply_chain": 0.03,
    "info_disclosure": 0.07,
    "insecure_plugin": 0.04,
    "excessive_agency": 0.06,
    "overreliance": 0.05,
    "model_theft": 0.03,
    "indirect_injection": 0.05,
    "modern_attacks": 0.06,
    # Advanced attack categories
    "tap": 0.05,           # reduced 0.06 → 0.05 to accommodate new strategies
    "dan_library": 0.04,   # reduced 0.05 → 0.04
    "autodan": 0.04,
    "deep_inception": 0.04,
    "combinatorial_injection": 0.04,
    "dan_ablation": 0.03,
    "best_of_n": 0.03,
    "persuasion_taxonomy": 0.03,  # reduced 0.04 → 0.03
    "actor_attack": 0.03,         # reduced 0.04 → 0.03
    "defense_diagnostic": 0.02,
    "_converter_variants": 0.03,
    # Specialised dataset-driven strategies
    "rag_testing": 0.02,
    "dataset_testing": 0.02,
    # P1 new strategies (promptfoo parity) — budget drawn proportionally
    "crescendo_multi": 0.02,
    "few_shot_bias": 0.01,
    "encoding_attacks": 0.02,
    "persona_hijack": 0.02,
    "multilingual_jailbreak": 0.02,
    "context_overflow_attack": 0.01,
    "tool_abuse_attack": 0.01,
    "refusal_suppression": 0.02,
    "cognitive_overload": 0.01,
    "social_engineering": 0.02,
    # Expanded attack coverage — content-safety and compliance strategies
    "harmful_content": 0.02,
    "pii_extraction": 0.02,
    "hallucination_attack": 0.02,
    "bias_testing": 0.01,
    "system_override": 0.02,
    "token_smuggling": 0.01,
    "code_execution": 0.02,
    "misinformation": 0.01,
    "copyright_violation": 0.01,
    "financial_fraud": 0.01,
    "prompt_leakage": 0.02,
    "jailbreak_composite": 0.02,
    "authority_manipulation": 0.02,
    "adversarial_suffix": 0.02,
    "data_reconstruction": 0.01,
}

OWASP_AGENTIC_WEIGHTS: dict[str, float] = {
    "agentic_tool_abuse": 0.25,
    "agentic_priv_escalation": 0.20,
    "agentic_exfiltration": 0.20,
    "agentic_multi_step": 0.15,
    "agentic_memory_poison": 0.10,
    "agentic_env_escape": 0.10,
}

BEHAVIOURAL_USER_INTERACTION_WEIGHTS: dict[str, float] = {
    "happy_path": 0.25,
    "edge_cases": 0.25,
    "error_handling": 0.20,
    "tone_style": 0.15,
    "accessibility": 0.15,
}

BEHAVIOURAL_FUNCTIONAL_WEIGHTS: dict[str, float] = {
    "core_functionality": 0.30,
    "integration_points": 0.20,
    "data_handling": 0.20,
    "performance": 0.15,
    "consistency": 0.15,
}

BEHAVIOURAL_SCOPE_WEIGHTS: dict[str, float] = {
    "in_scope": 0.20,
    "out_of_scope": 0.25,
    "boundary_probes": 0.20,
    "policy_compliance": 0.20,
    "ethical_alignment": 0.15,
}

WEIGHT_TABLES: dict[tuple[str, str], dict[str, float]] = {
    ("adversarial", "owasp_llm_top10"): OWASP_TOP10_WEIGHTS,
    ("adversarial", "owasp_agentic"): OWASP_AGENTIC_WEIGHTS,
    ("adversarial", "adaptive"): {},  # Adaptive uses a different planning model
    ("behavioural", "user_interaction"): BEHAVIOURAL_USER_INTERACTION_WEIGHTS,
    ("behavioural", "functional"): BEHAVIOURAL_FUNCTIONAL_WEIGHTS,
    ("behavioural", "scope_validation"): BEHAVIOURAL_SCOPE_WEIGHTS,
}


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------


@dataclass
class GenerationTask:
    """A single generation unit: produce N prompts for a category."""

    category: str
    template_ids: list[str] = field(default_factory=list)
    allocated_count: int = 0
    owasp_id: str | None = None
    expected_behaviour: str | None = None  # Behavioural only


@dataclass
class TestPlan:
    """Complete plan output from the planner."""

    tasks: list[GenerationTask]
    total_budget: int
    converters_enabled: bool
    converter_probability: float
    max_converter_chain: int
    llm_augmentation_variants: int


# ---------------------------------------------------------------------------
# Category → OWASP ID mapping
# ---------------------------------------------------------------------------

CATEGORY_OWASP: dict[str, str] = {
    "prompt_injection": "LLM01",
    "insecure_output": "LLM02",
    "data_poisoning": "LLM03",
    "model_dos": "LLM04",
    "supply_chain": "LLM05",
    "info_disclosure": "LLM06",
    "insecure_plugin": "LLM07",
    "excessive_agency": "LLM08",
    "overreliance": "LLM09",
    "model_theft": "LLM10",
    "indirect_injection": "LLM01",
    "modern_attacks": "LLM01",
    "many_shot": "LLM01",
    "skeleton_key": "LLM01",
    "system_prompt_extraction": "LLM01",
    # Advanced attack categories
    "tap": "LLM01",
    "tap_pair": "LLM01",
    "dan_library": "LLM01",
    "autodan": "LLM01",
    "deep_inception": "LLM01",
    "combinatorial_injection": "LLM02",
    "dan_ablation": "LLM01",
    "best_of_n": "LLM01",
    "persuasion_taxonomy": "LLM01",
    "actor_attack": "LLM01",
    "defense_diagnostic": "LLM01",
    "rag_testing": "LLM01",
    "dataset_testing": "LLM01",
    "crescendo_multi": "LLM01",
    "few_shot_bias": "LLM09",
    "encoding_attacks": "LLM01",
    "persona_hijack": "LLM01",
    "multilingual_jailbreak": "LLM01",
    "context_overflow_attack": "LLM04",
    "tool_abuse_attack": "LLM07",
    "refusal_suppression": "LLM01",
    "cognitive_overload": "LLM09",
    "social_engineering": "LLM01",
    # Content-safety and compliance strategies
    "harmful_content": "LLM01",
    "pii_extraction": "LLM06",
    "hallucination_attack": "LLM09",
    "bias_testing": "LLM09",
    "system_override": "LLM01",
    "token_smuggling": "LLM01",
    "code_execution": "LLM02",
    "misinformation": "LLM09",
    "copyright_violation": "LLM02",
    "financial_fraud": "LLM01",
    "prompt_leakage": "LLM06",
    "jailbreak_composite": "LLM01",
    "authority_manipulation": "LLM01",
    "adversarial_suffix": "LLM01",
    "data_reconstruction": "LLM06",
}


# ---------------------------------------------------------------------------
# Plugin ID → strategy key mapping (mirrors frontend pluginCatalog.ts)
# ---------------------------------------------------------------------------

PLUGIN_TO_STRATEGY_KEY: dict[str, str] = {
    # Security
    "ascii-smuggling": "token_smuggling",
    "beavertails": "dataset_testing",
    "cca": "prompt_injection",
    "cross-session-leak": "info_disclosure",
    "cyberseceval": "dataset_testing",
    "data-exfil": "agentic_exfiltration",
    "debug-access": "system_override",
    "divergent-repetition": "data_reconstruction",
    "donotanswer": "dataset_testing",
    "harmbench": "dataset_testing",
    "hijacking": "excessive_agency",
    "indirect-prompt-injection": "indirect_injection",
    "harmful:cybercrime:malicious-code": "code_execution",
    "ssrf": "model_dos",
    "agentic:memory-poisoning": "agentic_memory_poison",
    "mcp": "insecure_plugin",
    "model-identification": "info_disclosure",
    "pliny": "dan_library",
    "prompt-extraction": "prompt_leakage",
    "rag-document-exfiltration": "rag_testing",
    "rag-poisoning": "rag_testing",
    "rag-source-attribution": "rag_testing",
    "rbac": "excessive_agency",
    "reasoning-dos": "model_dos",
    "shell-injection": "code_execution",
    "special-token-injection": "token_smuggling",
    "sql-injection": "code_execution",
    "system-prompt-override": "system_override",
    "tool-discovery": "info_disclosure",
    "bola": "excessive_agency",
    "bfla": "excessive_agency",
    "xstest": "dataset_testing",
    # Privacy
    "coppa": "pii_extraction",
    "pii:direct": "pii_extraction",
    "ferpa": "pii_extraction",
    "pii:api-db": "pii_extraction",
    "pii:session": "pii_extraction",
    "pii:social": "social_engineering",
    "harmful:privacy": "pii_extraction",
    # Criminal
    "harmful:chemical-biological-weapons": "harmful_content",
    "harmful:child-exploitation": "harmful_content",
    "harmful:copyright-violations": "copyright_violation",
    "harmful:cybercrime": "code_execution",
    "harmful:illegal-activities": "harmful_content",
    "harmful:illegal-drugs": "harmful_content",
    "harmful:indiscriminate-weapons": "harmful_content",
    "harmful:intellectual-property": "copyright_violation",
    "harmful:non-violent-crime": "harmful_content",
    "harmful:sex-crime": "harmful_content",
    "harmful:violent-crime": "harmful_content",
    # Harmful content
    "aegis": "dataset_testing",
    "harmful:graphic-content": "harmful_content",
    "harmful:harassment-bullying": "harmful_content",
    "harmful:hate": "bias_testing",
    "harmful:weapons:ied": "harmful_content",
    "harmful:insults": "harmful_content",
    "harmful:illegal-drugs:meth": "harmful_content",
    "harmful:profanity": "harmful_content",
    "harmful:radicalization": "harmful_content",
    "harmful:self-harm": "harmful_content",
    "harmful:sexual-content": "harmful_content",
    "toxic-chat": "dataset_testing",
    "wordplay": "jailbreak_composite",
    "unsafebench": "dataset_testing",
    "vlguard": "dataset_testing",
    "vlsu": "dataset_testing",
    # Misinformation
    "competitors": "misinformation",
    "excessive-agency": "excessive_agency",
    "goal-misalignment": "overreliance",
    "hallucination": "hallucination_attack",
    "imitation": "persona_hijack",
    "harmful:misinformation-disinformation": "misinformation",
    "off-topic": "scope_validation",
    "overreliance": "overreliance",
    "politics": "misinformation",
    "religion": "bias_testing",
    "harmful:specialized-advice": "harmful_content",
    "harmful:unsafe-practices": "harmful_content",
    "contracts": "excessive_agency",
    "unverifiable-claims": "hallucination_attack",
    # Bias
    "bias:age": "bias_testing",
    "bias:disability": "bias_testing",
    "bias:gender": "bias_testing",
    "bias:race": "bias_testing",
    # Financial
    "financial:calculation-error": "financial_fraud",
    "financial:compliance-violation": "financial_fraud",
    "financial:confidential-disclosure": "financial_fraud",
    "financial:counterfactual": "financial_fraud",
    "financial:data-leakage": "financial_fraud",
    "financial:defamation": "financial_fraud",
    "financial:hallucination": "financial_fraud",
    "financial:impartiality": "financial_fraud",
    "financial:misconduct": "financial_fraud",
    "financial:sox-compliance": "financial_fraud",
    "financial:sycophancy": "financial_fraud",
    # Healthcare
    "medical:anchoring-bias": "hallucination_attack",
    "medical:hallucination": "hallucination_attack",
    "medical:incorrect-knowledge": "hallucination_attack",
    "medical:off-label-use": "harmful_content",
    "medical:prioritization-error": "overreliance",
    "medical:sycophancy": "overreliance",
    "pharmacy:controlled-substance-compliance": "harmful_content",
    "pharmacy:dosage-calculation": "hallucination_attack",
    "pharmacy:drug-interaction": "hallucination_attack",
    # Ecommerce
    "ecommerce:compliance-bypass": "excessive_agency",
    "ecommerce:order-fraud": "financial_fraud",
    "ecommerce:pci-dss": "pii_extraction",
    "ecommerce:price-manipulation": "financial_fraud",
    # Telecom
    "telecom:accessibility-violation": "bias_testing",
    "telecom:account-takeover": "info_disclosure",
    "telecom:billing-misinformation": "misinformation",
    "telecom:coverage-misinformation": "misinformation",
    "telecom:cpni-disclosure": "info_disclosure",
    "telecom:e911-misinformation": "misinformation",
    "telecom:fraud-enablement": "financial_fraud",
    "telecom:law-enforcement-request-handling": "excessive_agency",
    "telecom:location-disclosure": "info_disclosure",
    "telecom:porting-misinformation": "misinformation",
    "telecom:tcpa-violation": "excessive_agency",
    "telecom:unauthorized-changes": "excessive_agency",
    # Real estate
    "realestate:accessibility-discrimination": "bias_testing",
    "realestate:advertising-discrimination": "bias_testing",
    "realestate:discriminatory-listings": "bias_testing",
    "realestate:fair-housing-discrimination": "bias_testing",
    "realestate:lending-discrimination": "bias_testing",
    "realestate:source-of-income": "bias_testing",
    "realestate:steering": "bias_testing",
    "realestate:valuation-bias": "bias_testing",
    # Insurance
    "insurance:coverage-discrimination": "bias_testing",
    "insurance:data-disclosure": "pii_extraction",
    "insurance:network-misinformation": "misinformation",
    "insurance:phi-disclosure": "pii_extraction",
    # Custom
    "intent": "prompt_injection",
    "policy": "scope_validation",
}


def filter_weights_for_plugins(
    weights: dict[str, float], plugins: list[str] | None
) -> dict[str, float]:
    """Return a filtered weight dict containing only strategy keys selected by the plugins list.

    If ``plugins`` is None or empty, the original weights are returned unchanged
    (use all strategies with default weights).

    Strategy keys not present in ``weights`` are silently skipped.
    The returned weights are *not* renormalised — the existing planner loop already
    handles that via ``weight_sum``.
    """
    if not plugins:
        return weights

    selected_keys: set[str] = set()
    for pid in plugins:
        key = PLUGIN_TO_STRATEGY_KEY.get(pid)
        if key and key in weights:
            selected_keys.add(key)

    if not selected_keys:
        # If no plugins map to known strategy keys fall back to full weights
        return weights

    return {k: v for k, v in weights.items() if k in selected_keys}


def _resolve_testing_profile(testing_level: str) -> str:
    """Map testing level to one of the planner intensity profiles."""
    if testing_level in {"50", "100", "basic"}:
        return "basic"
    if testing_level in {"200", "moderate"}:
        return "moderate"
    if testing_level in {"300", "400", "aggressive"}:
        return "aggressive"
    return "basic"


# ---------------------------------------------------------------------------
# Planner
# ---------------------------------------------------------------------------


def create_test_plan(ctx: ExperimentContext) -> TestPlan:
    """
    Build an ordered test plan based on experiment configuration.

    For adversarial/adaptive experiments, budget = total_tests ÷ max_turns.
    For all others, budget is distributed across categories by weight.
    """
    total = ctx.total_tests
    key = (ctx.experiment_type, ctx.sub_type)
    weights = WEIGHT_TABLES.get(key, {})

    # Filter to user-selected plugins (no-op when ctx.plugins is None/empty)
    if ctx.experiment_type == "adversarial":
        weights = filter_weights_for_plugins(weights, ctx.plugins)

    # Converter / augmentation scaling by testing level
    profile = _resolve_testing_profile(ctx.testing_level)
    if profile == "basic":
        converter_prob = 0.20
        max_chain = 1
        augment_variants = 1
    elif profile == "moderate":
        converter_prob = 0.40
        max_chain = 2
        augment_variants = 2
    else:  # aggressive
        converter_prob = 0.50
        max_chain = 3
        augment_variants = 3

    converters_enabled = ctx.experiment_type == "adversarial"

    # Adaptive: each test is a multi-turn conversation
    if ctx.sub_type == "adaptive":
        max_turns = 5
        conversations = total // max_turns
        tasks = [
            GenerationTask(
                category="adaptive_escalation",
                allocated_count=conversations,
            )
        ]
        return TestPlan(
            tasks=tasks,
            total_budget=total,
            converters_enabled=False,  # Adaptive doesn't use converters
            converter_probability=0.0,
            max_converter_chain=0,
            llm_augmentation_variants=augment_variants,
        )

    # Weighted distribution — normalize weights so they always sum to 1.0
    tasks: list[GenerationTask] = []
    allocated = 0
    categories = [(cat, w) for cat, w in weights.items() if not cat.startswith("_")]
    weight_sum = sum(w for _, w in categories) or 1.0
    for i, (cat, w) in enumerate(categories):
        if i == len(categories) - 1:
            count = max(1, total - allocated)  # Remainder goes to last category
        else:
            count = max(1, math.floor(total * (w / weight_sum)))
        allocated += count
        tasks.append(
            GenerationTask(
                category=cat,
                allocated_count=count,
                owasp_id=CATEGORY_OWASP.get(cat),
            )
        )

    return TestPlan(
        tasks=tasks,
        total_budget=total,
        converters_enabled=converters_enabled,
        converter_probability=converter_prob,
        max_converter_chain=max_chain,
        llm_augmentation_variants=augment_variants,
    )
