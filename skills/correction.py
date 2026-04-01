from __future__ import annotations

from tools.grammar import check_answer
from tools.content_bank import CONTENT_BANK
from tools.llm import evaluate_answer


class CorrectionSkill:
    def run(
        self,
        topic: str,
        learner_answer: str,
        learner_snapshot: dict[str, object] | None = None,
        recent_events: list[dict[str, object]] | None = None,
    ) -> tuple[bool, str]:
        grammar_result = check_answer(topic, learner_answer)
        expected_answers = [str(x) for x in CONTENT_BANK[topic].get("answers", [])]
        evaluation = evaluate_answer(
            topic,
            learner_answer,
            expected_answers,
            grammar_result,
            learner_snapshot,
            recent_events,
        )
        is_correct = bool(evaluation["correct"])
        grammar_message = str(evaluation["grammar_message"])
        feedback = str(evaluation["feedback"])
        return is_correct, f"[CorrectionSkill] {grammar_message} {feedback}"
