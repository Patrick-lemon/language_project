from __future__ import annotations

from tools.content_bank import CONTENT_BANK
from tools.llm import generate_explanation


class ExplainSkill:
    def run(
        self,
        topic: str,
        learner_snapshot: dict[str, object] | None = None,
        recent_events: list[dict[str, object]] | None = None,
    ) -> str:
        base = CONTENT_BANK[topic]["explanation"]
        explanation = generate_explanation(topic, base, learner_snapshot, recent_events)
        return f"[ExplainSkill] Topic: {topic}\n{explanation}"
