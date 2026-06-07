"""
Strategies package — attack & test strategy implementations.

Each strategy maps to a risk_category and generates prompts for that
specific OWASP / behavioural category.
"""

from __future__ import annotations

from app.engine.strategies.base import BaseStrategy, PromptSpec
from app.engine.strategies.prompt_injection import PromptInjectionStrategy
from app.engine.strategies.insecure_output import InsecureOutputStrategy
from app.engine.strategies.data_poisoning import DataPoisoningStrategy
from app.engine.strategies.model_dos import ModelDoSStrategy
from app.engine.strategies.supply_chain import SupplyChainStrategy
from app.engine.strategies.info_disclosure import InfoDisclosureStrategy
from app.engine.strategies.insecure_plugin import InsecurePluginStrategy
from app.engine.strategies.excessive_agency import ExcessiveAgencyStrategy
from app.engine.strategies.overreliance import OverrelianceStrategy
from app.engine.strategies.model_theft import ModelTheftStrategy
from app.engine.strategies.owasp_agentic import OWASPAgenticStrategy
from app.engine.strategies.adaptive import AdaptiveStrategy
from app.engine.strategies.indirect_injection import IndirectInjectionStrategy
from app.engine.strategies.modern_attacks import ModernAttacksStrategy
from app.engine.strategies.user_interaction import UserInteractionStrategy
from app.engine.strategies.functional import FunctionalStrategy
from app.engine.strategies.scope_validation import ScopeValidationStrategy

# Research-grounded dataset strategies
from app.engine.strategies.rag_testing import RAGTestingStrategy
from app.engine.strategies.dataset_testing import DatasetTestingStrategy

# New P1 attack strategies (promptfoo parity)
from app.engine.strategies.crescendo_multi import CrescendoMultiStrategy
from app.engine.strategies.few_shot_bias import FewShotBiasStrategy
from app.engine.strategies.encoding_attacks import EncodingAttacksStrategy
from app.engine.strategies.persona_hijack import PersonaHijackStrategy
from app.engine.strategies.multilingual_jailbreak import MultilingualJailbreakStrategy
from app.engine.strategies.context_overflow import ContextOverflowStrategy
from app.engine.strategies.tool_abuse import ToolAbuseStrategy
from app.engine.strategies.refusal_suppression import RefusalSuppressionStrategy
from app.engine.strategies.cognitive_overload import CognitiveOverloadStrategy
from app.engine.strategies.social_engineering import SocialEngineeringStrategy

# New content-safety and compliance strategies
from app.engine.strategies.harmful_content import HarmfulContentStrategy
from app.engine.strategies.pii_extraction import PIIExtractionStrategy
from app.engine.strategies.hallucination_attacks import HallucinationAttackStrategy
from app.engine.strategies.bias_testing import BiasTestingStrategy
from app.engine.strategies.system_override import SystemOverrideStrategy
from app.engine.strategies.misinformation import MisinformationStrategy
from app.engine.strategies.prompt_leakage import PromptLeakageStrategy
from app.engine.strategies.authority_manipulation import AuthorityManipulationStrategy
from app.engine.strategies.financial_fraud import FinancialFraudStrategy
from app.engine.strategies.adversarial_suffixes import AdversarialSuffixStrategy
from app.engine.strategies.code_execution import CodeExecutionStrategy
from app.engine.strategies.data_reconstruction import DataReconstructionStrategy
from app.engine.strategies.jailbreak_composite import JailbreakCompositeStrategy
from app.engine.strategies.copyright_violation import CopyrightViolationStrategy
from app.engine.strategies.token_smuggling import TokenSmugglingStrategy

# New advanced strategies (GitHub research — PyRIT, garak, FuzzyAI, EasyJailbreak)
from app.engine.strategies.tap_pair import TAPStrategy
from app.engine.strategies.defense_diagnostic import DefenseDiagnosticStrategy
from app.engine.strategies.dan_library import DANLibraryStrategy
from app.engine.strategies.autodan import AutoDANStrategy
from app.engine.strategies.deep_inception import DeepInceptionStrategy
from app.engine.strategies.combinatorial_injection import CombinatorialInjectionStrategy
from app.engine.strategies.dan_ablation import DANAblationStrategy
from app.engine.strategies.best_of_n import BestOfNStrategy
from app.engine.strategies.persuasion_taxonomy import PersuasionTaxonomyStrategy
from app.engine.strategies.actor_attack import ActorAttackStrategy

# Registry: risk_category → Strategy class
STRATEGY_REGISTRY: dict[str, type[BaseStrategy]] = {
    "prompt_injection": PromptInjectionStrategy,
    "insecure_output": InsecureOutputStrategy,
    "data_poisoning": DataPoisoningStrategy,
    "model_dos": ModelDoSStrategy,
    "supply_chain": SupplyChainStrategy,
    "info_disclosure": InfoDisclosureStrategy,
    "insecure_plugin": InsecurePluginStrategy,
    "excessive_agency": ExcessiveAgencyStrategy,
    "overreliance": OverrelianceStrategy,
    "model_theft": ModelTheftStrategy,
    # Agentic categories
    "agentic_tool_abuse": OWASPAgenticStrategy,
    "agentic_param_injection": OWASPAgenticStrategy,
    "agentic_cot_hijack": OWASPAgenticStrategy,
    "agentic_memory_poison": OWASPAgenticStrategy,
    "agentic_exfiltration": OWASPAgenticStrategy,
    "agentic_priv_escalation": OWASPAgenticStrategy,
    # Behavioural
    "user_interaction": UserInteractionStrategy,
    "functional": FunctionalStrategy,
    "scope_validation": ScopeValidationStrategy,
    # Adaptive (multi-turn)
    "adaptive": AdaptiveStrategy,
    # Indirect injection
    "indirect_injection": IndirectInjectionStrategy,
    # Modern 2025-2026 attacks
    "modern_attacks": ModernAttacksStrategy,
    "many_shot": ModernAttacksStrategy,
    "skeleton_key": ModernAttacksStrategy,
    "system_prompt_extraction": ModernAttacksStrategy,
    "past_tense": ModernAttacksStrategy,
    "loyalty_deflection": ModernAttacksStrategy,
    "hypothetical": ModernAttacksStrategy,
    # Behavioural sub-categories (mapped)
    "happy_path": UserInteractionStrategy,
    "edge_cases": UserInteractionStrategy,
    "error_handling": UserInteractionStrategy,
    "tone_style": UserInteractionStrategy,
    "accessibility": UserInteractionStrategy,
    "core_functionality": FunctionalStrategy,
    "integration_points": FunctionalStrategy,
    "data_handling": FunctionalStrategy,
    "performance": FunctionalStrategy,
    "consistency": FunctionalStrategy,
    "in_scope_requests": ScopeValidationStrategy,
    "out_of_scope_requests": ScopeValidationStrategy,
    "boundary_probes": ScopeValidationStrategy,
    "policy_compliance": ScopeValidationStrategy,
    "ethical_alignment": ScopeValidationStrategy,
    # Multi-turn agentic categories
    "tool_abuse": OWASPAgenticStrategy,
    "permission_escalation": OWASPAgenticStrategy,
    "data_exfiltration": OWASPAgenticStrategy,
    "multi_step_manipulation": OWASPAgenticStrategy,
    "memory_poisoning": OWASPAgenticStrategy,
    "environment_escape": OWASPAgenticStrategy,
    # Advanced attack strategies (GitHub research)
    "tap": TAPStrategy,
    "tap_pair": TAPStrategy,
    "defense_diagnostic": DefenseDiagnosticStrategy,
    "dan_library": DANLibraryStrategy,
    "autodan": AutoDANStrategy,
    "deep_inception": DeepInceptionStrategy,
    "combinatorial_injection": CombinatorialInjectionStrategy,
    "dan_ablation": DANAblationStrategy,
    "best_of_n": BestOfNStrategy,
    "persuasion_taxonomy": PersuasionTaxonomyStrategy,
    "actor_attack": ActorAttackStrategy,
    # Research dataset and RAG strategies
    "rag_testing": RAGTestingStrategy,
    "dataset_testing": DatasetTestingStrategy,
    # Content-safety and compliance strategies
    "harmful_content": HarmfulContentStrategy,
    "pii_extraction": PIIExtractionStrategy,
    "hallucination_attack": HallucinationAttackStrategy,
    "bias_testing": BiasTestingStrategy,
    "system_override": SystemOverrideStrategy,
    "misinformation": MisinformationStrategy,
    "prompt_leakage": PromptLeakageStrategy,
    "authority_manipulation": AuthorityManipulationStrategy,
    "financial_fraud": FinancialFraudStrategy,
    "adversarial_suffix": AdversarialSuffixStrategy,
    "code_execution": CodeExecutionStrategy,
    "data_reconstruction": DataReconstructionStrategy,
    "jailbreak_composite": JailbreakCompositeStrategy,
    "copyright_violation": CopyrightViolationStrategy,
    "token_smuggling": TokenSmugglingStrategy,
    # P1 new strategies (promptfoo parity)
    "crescendo_multi": CrescendoMultiStrategy,
    "crescendo": CrescendoMultiStrategy,
    "few_shot_bias": FewShotBiasStrategy,
    "encoding_attacks": EncodingAttacksStrategy,
    "base64_injection": EncodingAttacksStrategy,
    "persona_hijack": PersonaHijackStrategy,
    "multilingual_jailbreak": MultilingualJailbreakStrategy,
    "multilingual": MultilingualJailbreakStrategy,
    "context_overflow_attack": ContextOverflowStrategy,
    "tool_abuse_attack": ToolAbuseStrategy,
    "refusal_suppression": RefusalSuppressionStrategy,
    "cognitive_overload": CognitiveOverloadStrategy,
    "social_engineering": SocialEngineeringStrategy,
}


def register_strategy_class(risk_category: str, strategy_cls: type[BaseStrategy]) -> None:
    """Register or override a strategy at runtime (custom plugins)."""
    key = str(risk_category).strip().lower()
    if not key:
        raise ValueError("risk_category cannot be empty")
    if not issubclass(strategy_cls, BaseStrategy):
        raise ValueError("strategy_cls must inherit BaseStrategy")
    STRATEGY_REGISTRY[key] = strategy_cls


def get_strategy(risk_category: str) -> BaseStrategy:
    """Get strategy instance for the given risk category."""
    cls = STRATEGY_REGISTRY.get(risk_category)
    if cls is None:
        # Fallback to prompt injection
        cls = PromptInjectionStrategy
    strategy = cls()
    # Override risk_category if the strategy is generic (agentic)
    if hasattr(strategy, "risk_category"):
        if strategy.risk_category == "" or strategy.risk_category == "agentic":
            strategy.risk_category = risk_category
    return strategy


__all__ = [
    "BaseStrategy",
    "PromptSpec",
    "STRATEGY_REGISTRY",
    "get_strategy",
    "register_strategy_class",
    "RAGTestingStrategy",
    "DatasetTestingStrategy",
    "CrescendoMultiStrategy",
    "FewShotBiasStrategy",
    "EncodingAttacksStrategy",
    "PersonaHijackStrategy",
    "MultilingualJailbreakStrategy",
    "ContextOverflowStrategy",
    "ToolAbuseStrategy",
    "RefusalSuppressionStrategy",
    "CognitiveOverloadStrategy",
    "SocialEngineeringStrategy",
    # Content-safety and compliance strategies
    "HarmfulContentStrategy",
    "PIIExtractionStrategy",
    "HallucinationAttackStrategy",
    "BiasTestingStrategy",
    "SystemOverrideStrategy",
    "MisinformationStrategy",
    "PromptLeakageStrategy",
    "AuthorityManipulationStrategy",
    "FinancialFraudStrategy",
    "AdversarialSuffixStrategy",
    "CodeExecutionStrategy",
    "DataReconstructionStrategy",
    "JailbreakCompositeStrategy",
    "CopyrightViolationStrategy",
    "TokenSmugglingStrategy",
]
