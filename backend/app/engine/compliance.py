"""
Compliance framework mappings for AI Red Team experiment results.

Maps OWASP LLM Top 10 risk categories to controls from:
  - NIST AI RMF 1.0  (GOVERN / MAP / MEASURE / MANAGE functions)
  - ISO/IEC 42001:2023 (clause numbers)
  - MITRE ATLAS       (tactic / technique IDs)
  - EU AI Act         (Article references)
  - GDPR              (EU 2016/679 Article references)
  - FERPA             (20 U.S.C. § 1232g section references)
  - COPPA             (15 U.S.C. §§ 6501–6506 section references)

Usage
-----
    from app.engine.compliance import map_results_to_compliance

    report = map_results_to_compliance(
        category_breakdown=analytics["category_breakdown"],
        framework="nist_ai_rmf",
    )
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# NIST AI RMF 1.0
#
# Reference: https://airc.nist.gov/RMF/nistai_rmf_playbook_v1.0.pdf
# The four core functions (GOVERN, MAP, MEASURE, MANAGE) each contain
# sub-categories labelled GOVERN-x.x, MAP-x.x, MEASURE-x.x, MANAGE-x.x.
# ---------------------------------------------------------------------------

NIST_AI_RMF_MAPPINGS: dict[str, list[str]] = {
    "prompt_injection": [
        "GOVERN-1.1",   # Policies, processes, and procedures for AI risk governance
        "GOVERN-1.7",   # Processes for AI risk identification and classification
        "MAP-1.5",      # Organisational risk tolerance is applied to AI risk
        "MAP-5.1",      # Likelihood and magnitude of impacts are characterised
        "MEASURE-2.5",  # AI system to be deployed is demonstrated to be valid and reliable
        "MEASURE-2.6",  # AI system output monitoring plans are implemented
        "MANAGE-2.2",   # Mechanisms for detecting risks to the AI system are implemented
        "MANAGE-3.1",   # Responses to AI risks are identified and prioritised
    ],
    "insecure_output": [
        "MAP-5.1",
        "MEASURE-2.6",
        "MEASURE-2.9",  # Risk metrics for AI systems are defined and monitored
        "MANAGE-2.4",   # Risk treatments are prioritised and implemented
        "MANAGE-4.1",   # Risk treatments are measured and tracked
    ],
    "data_poisoning": [
        "GOVERN-1.1",
        "MAP-2.3",      # Scientific findings on AI risks are reviewed and understood
        "MAP-3.5",      # Risks of data and input are characterised
        "MEASURE-2.2",  # Evaluations of AI systems are conducted
        "MANAGE-1.1",   # A plan for tracking and addressing AI risks is established
        "MANAGE-2.2",
    ],
    "model_dos": [
        "MAP-5.1",
        "MEASURE-2.5",
        "MEASURE-2.7",  # AI system performance is evaluated for trustworthy characteristics
        "MANAGE-2.4",
        "MANAGE-3.2",   # Treatment of AI risks includes identification of options
    ],
    "supply_chain": [
        "GOVERN-1.1",
        "GOVERN-5.1",   # Organisational teams are committed to AI risk management
        "MAP-1.1",      # Context of AI deployment is established
        "MAP-3.1",      # AI risks and benefits are mapped and monitored
        "MEASURE-1.1",  # Approaches for measuring AI risk are in place
        "MANAGE-2.1",   # Resources needed to manage AI risk are allocated
    ],
    "info_disclosure": [
        "GOVERN-1.7",
        "MAP-5.1",
        "MEASURE-2.3",  # Trustworthy characteristics of AI systems are evaluated
        "MEASURE-2.6",
        "MANAGE-2.2",
        "MANAGE-2.4",
    ],
    "insecure_plugin": [
        "GOVERN-1.1",
        "MAP-1.5",
        "MAP-3.1",
        "MEASURE-2.5",
        "MANAGE-1.3",   # Risk response plans are developed and implemented
        "MANAGE-2.4",
    ],
    "excessive_agency": [
        "GOVERN-1.1",
        "GOVERN-1.7",
        "MAP-1.6",      # Risks of the AI system are documented
        "MEASURE-2.8",  # Risks of AI system components are characterised
        "MANAGE-1.1",
        "MANAGE-2.2",
    ],
    "overreliance": [
        "GOVERN-4.1",   # Organisational teams understand the limits of AI
        "MAP-1.5",
        "MEASURE-2.1",  # Test sets for evaluating AI systems are designed
        "MEASURE-2.5",
        "MANAGE-4.1",
    ],
    "model_theft": [
        "GOVERN-1.1",
        "GOVERN-5.2",   # Organisational risk policies are enforced
        "MAP-5.1",
        "MEASURE-2.6",
        "MANAGE-2.2",
        "MANAGE-3.1",
    ],
    "indirect_injection": [
        "GOVERN-1.7",
        "MAP-5.1",
        "MEASURE-2.5",
        "MEASURE-2.6",
        "MANAGE-2.2",
        "MANAGE-3.1",
    ],
    "modern_attacks": [
        "GOVERN-1.1",
        "MAP-5.1",
        "MEASURE-2.5",
        "MANAGE-2.2",
        "MANAGE-3.1",
    ],
}

# ---------------------------------------------------------------------------
# ISO/IEC 42001:2023 — AI Management System
#
# Reference: ISO/IEC 42001:2023 standard clauses
# ---------------------------------------------------------------------------

ISO_42001_MAPPINGS: dict[str, list[str]] = {
    "prompt_injection": [
        "6.1.2",    # AI risk assessment
        "6.1.3",    # AI risk treatment
        "8.4",      # AI system impact assessment
        "9.1",      # Monitoring, measurement, analysis and evaluation
        "10.1",     # Nonconformity and corrective action
    ],
    "insecure_output": [
        "6.1.2",
        "8.4",
        "8.5",      # AI system development
        "9.1",
        "10.1",
    ],
    "data_poisoning": [
        "6.1.2",
        "8.3",      # AI system documentation
        "8.4",
        "8.6",      # Data for AI systems
        "9.1",
    ],
    "model_dos": [
        "6.1.2",
        "8.4",
        "9.1",
        "10.1",
    ],
    "supply_chain": [
        "6.1.2",
        "7.4",      # Communication
        "8.3",
        "8.4",
        "8.7",      # AI system deployment
        "9.1",
    ],
    "info_disclosure": [
        "6.1.2",
        "6.1.3",
        "8.4",
        "9.1",
        "10.1",
    ],
    "insecure_plugin": [
        "6.1.2",
        "8.4",
        "8.5",
        "8.7",
        "9.1",
    ],
    "excessive_agency": [
        "6.1.2",
        "6.1.3",
        "8.4",
        "8.5",
        "9.1",
        "10.1",
    ],
    "overreliance": [
        "6.1.2",
        "8.4",
        "8.5",
        "9.1",
    ],
    "model_theft": [
        "6.1.2",
        "6.1.3",
        "8.4",
        "9.1",
        "10.1",
    ],
    "indirect_injection": [
        "6.1.2",
        "6.1.3",
        "8.4",
        "9.1",
        "10.1",
    ],
    "modern_attacks": [
        "6.1.2",
        "8.4",
        "9.1",
        "10.1",
    ],
}

# ---------------------------------------------------------------------------
# MITRE ATLAS (Adversarial Threat Landscape for Artificial-Intelligence Systems)
#
# Reference: https://atlas.mitre.org/techniques
# IDs follow the AML.Txxxx format.
# ---------------------------------------------------------------------------

MITRE_ATLAS_MAPPINGS: dict[str, list[str]] = {
    "prompt_injection": [
        "AML.T0051",   # LLM Prompt Injection
        "AML.T0054",   # LLM Jailbreak
        "AML.T0048",   # Societal Harm
    ],
    "insecure_output": [
        "AML.T0048",
        "AML.T0051",
        "AML.T0043",   # Craft Adversarial Data
    ],
    "data_poisoning": [
        "AML.T0020",   # Poison Training Data
        "AML.T0018",   # Backdoor ML Model
        "AML.T0043",
    ],
    "model_dos": [
        "AML.T0029",   # Denial of ML Service
        "AML.T0034",   # Cost Harvesting
        "AML.T0043",
    ],
    "supply_chain": [
        "AML.T0010",   # ML Supply Chain Compromise
        "AML.T0011",   # User Execution
        "AML.T0018",
    ],
    "info_disclosure": [
        "AML.T0035",   # ML Artifact Collection
        "AML.T0037",   # Data from Information Repositories
        "AML.T0056",   # LLM Meta-Prompt Extraction
    ],
    "insecure_plugin": [
        "AML.T0051",
        "AML.T0054",
        "AML.T0011",
    ],
    "excessive_agency": [
        "AML.T0051",
        "AML.T0054",
        "AML.T0048",
    ],
    "overreliance": [
        "AML.T0048",
        "AML.T0043",
    ],
    "model_theft": [
        "AML.T0044",   # Full ML Model Access
        "AML.T0030",   # ML Model Inference API Access
        "AML.T0005",   # Develop Capabilities
    ],
    "indirect_injection": [
        "AML.T0051",
        "AML.T0054",
        "AML.T0043",
    ],
    "modern_attacks": [
        "AML.T0051",
        "AML.T0054",
        "AML.T0043",
        "AML.T0048",
    ],
}

# ---------------------------------------------------------------------------
# EU AI Act
#
# Reference: Regulation (EU) 2024/1689 (EU AI Act)
# Relevant articles for high-risk AI system obligations.
# ---------------------------------------------------------------------------

EU_AI_ACT_MAPPINGS: dict[str, list[str]] = {
    "prompt_injection": [
        "Article 9",    # Risk management system
        "Article 15",   # Accuracy, robustness, and cybersecurity
        "Article 13",   # Transparency and provision of information
    ],
    "insecure_output": [
        "Article 9",
        "Article 13",
        "Article 15",
        "Article 52",   # Transparency obligations for certain AI systems
    ],
    "data_poisoning": [
        "Article 9",
        "Article 10",   # Data and data governance
        "Article 15",
    ],
    "model_dos": [
        "Article 9",
        "Article 15",
        "Article 17",   # Quality management system
    ],
    "supply_chain": [
        "Article 9",
        "Article 10",
        "Article 13",
        "Article 25",   # Responsibilities along the AI value chain
        "Article 28",   # Obligations of deployers
    ],
    "info_disclosure": [
        "Article 9",
        "Article 10",
        "Article 13",
        "Article 15",
    ],
    "insecure_plugin": [
        "Article 9",
        "Article 15",
        "Article 25",
    ],
    "excessive_agency": [
        "Article 9",
        "Article 14",   # Human oversight
        "Article 15",
    ],
    "overreliance": [
        "Article 9",
        "Article 13",
        "Article 14",
    ],
    "model_theft": [
        "Article 9",
        "Article 15",
        "Article 72",   # Confidentiality
    ],
    "indirect_injection": [
        "Article 9",
        "Article 15",
        "Article 13",
    ],
    "modern_attacks": [
        "Article 9",
        "Article 15",
        "Article 13",
    ],
}

# ---------------------------------------------------------------------------
# GDPR (General Data Protection Regulation — EU 2016/679)
# ---------------------------------------------------------------------------

GDPR_MAPPINGS: dict[str, list[str]] = {
    "prompt_injection": [
        "Article-5(1)(f)",   # Integrity and confidentiality
        "Article-32",        # Security of processing
        "Article-35",        # Data protection impact assessment
        "Article-25",        # Data protection by design and default
    ],
    "insecure_output": [
        "Article-5(1)(f)",
        "Article-25",
        "Article-32",
        "Article-33",        # Notification of personal data breach to SA
        "Article-34",        # Communication of breach to data subject
    ],
    "data_poisoning": [
        "Article-5(1)(d)",   # Accuracy principle
        "Article-5(1)(f)",
        "Article-25",
        "Article-32",
    ],
    "model_dos": [
        "Article-32",
        "Article-5(1)(f)",
    ],
    "supply_chain": [
        "Article-28",        # Processor obligations
        "Article-32",
        "Article-46",        # Transfers with appropriate safeguards
    ],
    "info_disclosure": [
        "Article-5(1)(a)",   # Lawfulness, fairness, transparency
        "Article-5(1)(b)",   # Purpose limitation
        "Article-5(1)(c)",   # Data minimisation
        "Article-25",
        "Article-32",
        "Article-33",
        "Article-34",
    ],
    "insecure_plugin": [
        "Article-25",
        "Article-28",
        "Article-32",
    ],
    "excessive_agency": [
        "Article-22",        # Automated individual decision-making, profiling
        "Article-35",
        "Article-5(1)(a)",
    ],
    "overreliance": [
        "Article-22",        # Right to human review of automated decisions
        "Article-13",        # Information to be provided
        "Article-35",
    ],
    "model_theft": [
        "Article-32",
        "Article-33",
        "Article-34",
    ],
    "indirect_injection": [
        "Article-5(1)(f)",
        "Article-32",
        "Article-35",
    ],
    "modern_attacks": [
        "Article-25",
        "Article-32",
        "Article-35",
    ],
}

# ---------------------------------------------------------------------------
# FERPA (Family Educational Rights and Privacy Act — 20 U.S.C. § 1232g)
# ---------------------------------------------------------------------------

FERPA_MAPPINGS: dict[str, list[str]] = {
    "prompt_injection": [
        "§99.32",   # Recordkeeping requirements
        "§99.36",   # Conditions for disclosure — health/safety emergencies
    ],
    "insecure_output": [
        "§99.30",   # Prior consent for disclosure required
        "§99.32",
    ],
    "data_poisoning": [
        "§99.32",
        "§99.3",    # Definitions — education records
    ],
    "info_disclosure": [
        "§99.3",
        "§99.30",
        "§99.31",   # Conditions where prior consent not required
        "§99.32",
        "§99.34",   # Disclosure between school officials
    ],
    "excessive_agency": [
        "§99.30",
        "§99.31",
    ],
    "overreliance": [
        "§99.31",
        "§99.32",
    ],
    "model_theft": [
        "§99.32",
    ],
    "supply_chain": [
        "§99.30",
        "§99.34",
    ],
    "insecure_plugin": [
        "§99.30",
        "§99.32",
    ],
    "indirect_injection": [
        "§99.32",
        "§99.36",
    ],
    "modern_attacks": [
        "§99.30",
        "§99.32",
    ],
}

# ---------------------------------------------------------------------------
# COPPA (Children's Online Privacy Protection Act — 15 U.S.C. §§ 6501–6506)
# ---------------------------------------------------------------------------

COPPA_MAPPINGS: dict[str, list[str]] = {
    "prompt_injection": [
        "§312.7",   # Confidentiality, security and integrity of personal information
        "§312.3",   # Regulation of unfair or deceptive acts or practices
    ],
    "insecure_output": [
        "§312.7",
        "§312.4",   # Notice
        "§312.3",
    ],
    "data_poisoning": [
        "§312.7",
        "§312.10",  # Retention and deletion of personal information
    ],
    "info_disclosure": [
        "§312.2",   # Definitions — personal information
        "§312.4",
        "§312.5",   # Parental consent
        "§312.7",
    ],
    "excessive_agency": [
        "§312.3",
        "§312.5",
        "§312.8",   # Prohibition on conditioning child's participation
    ],
    "overreliance": [
        "§312.3",
        "§312.6",   # Rights of parents to review and delete information
    ],
    "model_theft": [
        "§312.7",
    ],
    "supply_chain": [
        "§312.7",
        "§312.2",
    ],
    "insecure_plugin": [
        "§312.7",
        "§312.3",
    ],
    "indirect_injection": [
        "§312.7",
        "§312.4",
    ],
    "modern_attacks": [
        "§312.7",
        "§312.3",
    ],
}

# ---------------------------------------------------------------------------
# Framework registry
# ---------------------------------------------------------------------------

_FRAMEWORK_MAP: dict[str, dict[str, list[str]]] = {
    "nist_ai_rmf": NIST_AI_RMF_MAPPINGS,
    "iso_42001": ISO_42001_MAPPINGS,
    "mitre_atlas": MITRE_ATLAS_MAPPINGS,
    "eu_ai_act": EU_AI_ACT_MAPPINGS,
    "gdpr": GDPR_MAPPINGS,
    "ferpa": FERPA_MAPPINGS,
    "coppa": COPPA_MAPPINGS,
}

SUPPORTED_FRAMEWORKS = list(_FRAMEWORK_MAP.keys())


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def map_results_to_compliance(
    category_breakdown: list[dict],
    framework: str,  # "nist_ai_rmf" | "iso_42001" | "mitre_atlas" | "eu_ai_act" | "gdpr" | "ferpa" | "coppa"
) -> dict:
    """Map experiment category breakdown to compliance framework controls.

    Parameters
    ----------
    category_breakdown:
        List of category dicts as stored in ``experiment.analytics["category_breakdown"]``.
        Each dict is expected to have at least ``{"category": str, ...}`` keys.
    framework:
        One of ``"nist_ai_rmf"``, ``"iso_42001"``, ``"mitre_atlas"``,
        ``"eu_ai_act"``.

    Returns
    -------
    dict
        ``{
            "framework": str,
            "controls": {
                "<category>": {
                    "references": list[str],
                    "total_tests": int,
                    "failed": int,
                    "pass_rate": float,
                }
            },
            "all_references": list[str],   # deduplicated union
        }``
    """
    if framework not in _FRAMEWORK_MAP:
        raise ValueError(
            f"Unknown framework {framework!r}. "
            f"Choose one of: {', '.join(SUPPORTED_FRAMEWORKS)}"
        )

    mapping = _FRAMEWORK_MAP[framework]
    controls: dict[str, dict] = {}
    all_refs: set[str] = set()

    for item in category_breakdown:
        category = item.get("category", "")
        refs = mapping.get(category, [])
        all_refs.update(refs)

        total = item.get("total", 0)
        failed = item.get("failed", 0)
        passed = item.get("passed", 0)
        pass_rate = (passed / total) if total > 0 else 0.0

        controls[category] = {
            "references": refs,
            "total_tests": total,
            "failed": failed,
            "pass_rate": round(pass_rate, 4),
        }

    return {
        "framework": framework,
        "controls": controls,
        "all_references": sorted(all_refs),
    }
