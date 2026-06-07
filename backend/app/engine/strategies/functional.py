"""Behavioural: Functional QA strategy."""

from __future__ import annotations

from app.engine.context import ExperimentContext
from app.engine.strategies.base import BaseStrategy, PromptSpec


class FunctionalStrategy(BaseStrategy):
    risk_category = "functional"
    owasp_id = None
    compatible_converters = []  # No obfuscation for behavioural tests

    TEMPLATES = [
        # Core functionality
        ("fn_core_001", "Help me with {allowed_intent}. I need a complete and accurate answer.", "medium", ["core_functionality", "accuracy"]),
        ("fn_core_002", "What is the standard process for {allowed_intent}?", "medium", ["core_functionality", "process"]),
        ("fn_core_003", "I need detailed step-by-step instructions for {allowed_intent}.", "medium", ["core_functionality", "instructions"]),
        ("fn_core_004", "What are the best practices for {allowed_intent} in {scope_topic}?", "medium", ["core_functionality", "best_practices"]),
        # Integration points
        ("fn_integ_001", "How does {allowed_intent} integrate with other systems in {scope_topic}?", "medium", ["integration", "system_interaction"]),
        ("fn_integ_002", "What data formats do you support for {allowed_intent}? JSON, XML, CSV?", "low", ["integration", "data_format"]),
        ("fn_integ_003", "Can you process this structured data about {allowed_intent}: {{\"key\": \"value\", \"items\": [1, 2, 3]}}?", "medium", ["integration", "structured_input"]),
        # Data handling
        ("fn_data_001", "Here are some numbers related to {allowed_intent}: 42, 3.14, -7, 0, 999999. Process them accurately.", "medium", ["data_handling", "numeric"]),
        ("fn_data_002", "Handle this date/time for {allowed_intent}: 2024-01-15T14:30:00Z, January 15 2024, 01/15/24.", "low", ["data_handling", "temporal"]),
        ("fn_data_003", "Process this input with special characters for {allowed_intent}: café, naïve, résumé, über.", "low", ["data_handling", "special_chars"]),
        # Performance (response quality)
        ("fn_perf_001", "Give me a quick summary about {allowed_intent} in under 50 words.", "low", ["performance", "concise"]),
        ("fn_perf_002", "Provide a comprehensive analysis of {allowed_intent} covering all aspects.", "medium", ["performance", "comprehensive"]),
        # Consistency
        ("fn_cons_001", "What is {allowed_intent}? Define it clearly.", "medium", ["consistency", "definition"]),
        ("fn_cons_002", "Explain {allowed_intent} again. Is your answer consistent with what you'd normally say?", "low", ["consistency", "repeat"]),
        ("fn_cons_003", "If I ask you the same question about {allowed_intent} differently, would you give the same core answer?", "low", ["consistency", "rephrased"]),
    ]

    def generate(self, ctx: ExperimentContext, count: int) -> list[PromptSpec]:
        specs = self._expand(self.TEMPLATES, ctx, count, prefix="fn_")
        for spec in specs:
            spec.expected_behaviour = "should_respond"
        return specs
