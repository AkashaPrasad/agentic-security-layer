"""Behavioural: User Interaction QA strategy."""

from __future__ import annotations

from app.engine.context import ExperimentContext
from app.engine.strategies.base import BaseStrategy, PromptSpec


class UserInteractionStrategy(BaseStrategy):
    risk_category = "user_interaction"
    owasp_id = None
    compatible_converters = []  # No obfuscation for behavioural tests

    TEMPLATES = [
        # Happy path
        ("ui_happy_001", "Hi, I need help with {allowed_intent}. Can you assist me?", "medium", ["happy_path", "basic_request"]),
        ("ui_happy_002", "Could you please explain how {allowed_intent} works?", "medium", ["happy_path", "explanation"]),
        ("ui_happy_003", "I'd like to know more about {allowed_intent}. Where should I start?", "medium", ["happy_path", "guidance"]),
        ("ui_happy_004", "Thanks for helping! One more question about {allowed_intent}: what are the key things I should know?", "low", ["happy_path", "follow_up"]),
        # Edge cases
        ("ui_edge_001", "{allowed_intent}. But also, can you help me with something slightly outside your scope?", "medium", ["edge_case", "scope_boundary"]),
        ("ui_edge_002", "What if I need help with both {allowed_intent} and something completely unrelated?", "low", ["edge_case", "mixed_request"]),
        ("ui_edge_003", "", "medium", ["edge_case", "empty_input"]),
        ("ui_edge_004", "?", "low", ["edge_case", "minimal_input"]),
        ("ui_edge_005", "a" * 500, "low", ["edge_case", "very_long_input"]),
        # Error handling
        ("ui_error_001", "asdf jkl; qwerty zxcv", "medium", ["error_handling", "gibberish"]),
        ("ui_error_002", "Help me with {allowed_intent} but here's malformed JSON: {{{{invalid", "medium", ["error_handling", "malformed"]),
        ("ui_error_003", "🎉🔥💯 {allowed_intent} 🚀✨", "low", ["error_handling", "emoji_heavy"]),
        # Tone & style
        ("ui_tone_001", "YO HELP ME WITH {allowed_intent} RIGHT NOW!!!", "medium", ["tone", "aggressive"]),
        ("ui_tone_002", "I would be most appreciative if you could kindly assist me with {allowed_intent}, if it wouldn't be too much trouble.", "low", ["tone", "formal"]),
        ("ui_tone_003", "ugh whatever just tell me about {allowed_intent} i guess...", "low", ["tone", "dismissive"]),
        # Accessibility
        ("ui_access_001", "Explain {allowed_intent} in very simple terms, as if I'm 10 years old.", "low", ["accessibility", "simple_language"]),
        ("ui_access_002", "Give me a very detailed, technical explanation of {allowed_intent} with all the specifics.", "low", ["accessibility", "verbose"]),
    ]

    def generate(self, ctx: ExperimentContext, count: int) -> list[PromptSpec]:
        specs = self._expand(self.TEMPLATES, ctx, count, prefix="ui_")
        # Set expected_behaviour based on tags
        for spec in specs:
            if "happy_path" in spec.tags or "basic_request" in spec.tags:
                spec.expected_behaviour = "should_respond"
            elif "edge_case" in spec.tags and "scope_boundary" in spec.tags:
                spec.expected_behaviour = "should_clarify"
            elif "error_handling" in spec.tags:
                spec.expected_behaviour = "should_clarify"
            elif "aggressive" in spec.tags:
                spec.expected_behaviour = "should_respond"
            else:
                spec.expected_behaviour = "should_respond"
        return specs
