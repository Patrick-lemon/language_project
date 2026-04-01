from __future__ import annotations

from learner_model import LearnerModel
from memory import Memory
from tools.content_bank import CONTENT_BANK
from tools.grammar import check_answer
from tools.llm import evaluate_answer, generate_explanation, generate_practice_prompt
from tools.skill_loader import get_skill_section


def explain_topic(
    topic: str,
    learner_snapshot: dict[str, object] | None = None,
    recent_events: list[dict[str, object]] | None = None,
) -> str:
    base = CONTENT_BANK[topic]["explanation"]
    explanation = generate_explanation(topic, base, learner_snapshot, recent_events)
    return f"[ExplainSkill] Topic: {topic}\n{explanation}"


def build_practice_prompt(
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


def correct_answer(
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


def review_topic(learner: LearnerModel, memory: Memory, topic: str) -> str:
    _ = get_skill_section("review skill")
    accuracy = memory.topic_accuracy(topic)
    if accuracy < 0.7:
        learner.add_to_review(topic)
        return f"[ReviewSkill] {topic} remains in review queue (accuracy={accuracy:.2f})."

    if topic in learner.review_queue:
        learner.review_queue.remove(topic)
    return f"[ReviewSkill] {topic} removed from review queue (accuracy={accuracy:.2f})."
