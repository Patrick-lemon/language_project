from __future__ import annotations

from tools.content_bank import CONTENT_BANK
from tools.llm import generate_practice_prompt


class PracticeSkill:
    def build_prompt(
        self,
        topic: str,
        learner_snapshot: dict[str, object] | None = None,
        recent_events: list[dict[str, object]] | None = None,
    ) -> str:
        base_question = CONTENT_BANK[topic]["question"]
        return generate_practice_prompt(
            topic,
            base_question,
            learner_snapshot,
            recent_events,
        )
