from __future__ import annotations

from learner_model import LearnerModel
from memory import Memory
from tools.content_bank import CONTENT_BANK
from tools.grammar import check_answer
from tools.llm import evaluate_answer, generate_explanation, generate_practice_prompt


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


def review_topic_intro(
    topic: str,
    learner: LearnerModel,
    memory: Memory,
    learner_snapshot: dict[str, object] | None = None,
    recent_events: list[dict[str, object]] | None = None,
) -> str:
    base = CONTENT_BANK[topic]["explanation"]
    recap = generate_explanation(topic, base, learner_snapshot, recent_events)
    recent_attempts = memory.topic_history.get(topic, [])[-3:]
    recent_summary = ", ".join(
        "correct" if item else "incorrect" for item in recent_attempts
    ) or "no graded attempts yet"
    return (
        f"[ReviewSkill] Topic: {topic}\n"
        f"Quick review before retrying. "
        f"mastery={learner.get_mastery(topic):.2f}, "
        f"accuracy={memory.topic_accuracy(topic):.2f}, "
        f"recent={recent_summary}.\n"
        f"{recap}"
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


def update_review_status(learner: LearnerModel, memory: Memory, topic: str) -> str:
    accuracy = memory.topic_accuracy(topic)
    if accuracy < 0.7:
        learner.add_to_review(topic)
        delay = 2 if accuracy < 0.4 else 4
        due_turn = memory.schedule_review(topic, delay)
        return (
            f"[ReviewSkill] {topic} remains in review queue "
            f"(accuracy={accuracy:.2f}, due_turn={due_turn})."
        )

    if topic in learner.review_queue:
        learner.review_queue.remove(topic)
    memory.clear_review_schedule(topic)
    return f"[ReviewSkill] {topic} removed from review queue (accuracy={accuracy:.2f})."
