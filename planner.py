from dataclasses import dataclass
from typing import Optional, Tuple

from learner_model import LearnerModel
from memory import Memory
from tools.content_bank import (
    PREREQUISITE_MASTERY,
    SCENARIO_PREREQUISITE_MASTERY,
    list_topics,
    topic_category,
    topic_difficulty,
    topic_prerequisites,
    topic_tags,
)


@dataclass
class Plan:
    action: str
    topic: str
    reason: str


class Planner:
    def _apply_learner_focus(
        self, learner: LearnerModel, candidates: list[str]
    ) -> Tuple[list[str], Optional[str]]:
        """Narrow candidate topics when the learner set a preference; never return empty."""
        mode = (getattr(learner, "learning_focus", None) or "balanced").strip().lower()
        if mode == "balanced":
            return candidates, None
        if mode == "custom":
            keys = list(getattr(learner, "custom_focus_topics", None) or [])
            if not keys:
                return candidates, None
            keyset = set(keys)
            filt = [t for t in candidates if t in keyset]
            if filt:
                return filt, "Learner-requested topic list."
            return candidates, None
        if mode in ("survival", "question", "scenario"):
            filt = [t for t in candidates if topic_category(t) == mode]
            if filt:
                return filt, f"Learner prefers {mode} lessons."
            return candidates, None
        return candidates, None

    def _max_difficulty(self, learner: LearnerModel, memory: Memory) -> int:
        stable_topics = [
            topic
            for topic in list_topics()
            if learner.get_mastery(topic) >= PREREQUISITE_MASTERY
            or memory.topic_accuracy(topic) >= 0.75
        ]
        if learner.confidence < 0.45:
            return 1
        if len(stable_topics) >= 7:
            return 3
        if len(stable_topics) >= 3:
            return 2
        return 1

    def _topic_unlocked(self, learner: LearnerModel, memory: Memory, topic: str) -> bool:
        prereqs = topic_prerequisites(topic)
        required_mastery = (
            SCENARIO_PREREQUISITE_MASTERY
            if topic_category(topic) == "scenario"
            else PREREQUISITE_MASTERY
        )
        if prereqs and not all(learner.get_mastery(t) >= required_mastery for t in prereqs):
            return False
        return topic_difficulty(topic) <= self._max_difficulty(learner, memory)

    def choose_plan(self, learner: LearnerModel, memory: Memory) -> Plan:
        topics = list_topics()

        # Immediate remediation takes priority over the broader review queue.
        last_attempt = memory.last_practice_attempt()
        if last_attempt and not bool(last_attempt.get("correct")):
            last_topic = last_attempt.get("topic")
            if isinstance(last_topic, str):
                attempts = memory.topic_history.get(last_topic, [])
                last_mastery = learner.get_mastery(last_topic)
                if last_mastery < 0.65 and len(attempts) < 3:
                    return Plan(
                        action="review",
                        topic=last_topic,
                        reason=(
                            "Learner struggled recently on this topic; "
                            "review it before another practice attempt."
                        ),
                    )
                return Plan(
                    action="practice",
                    topic=last_topic,
                    reason="Learner made an error; practice this topic again.",
                )

        due_reviews = memory.due_review_topics(list(learner.review_queue))
        if due_reviews:
            topic = due_reviews[0]
            accuracy = memory.topic_accuracy(topic)
            return Plan(
                action="review",
                topic=topic,
                reason=(
                    "Topic is due for spaced review "
                    f"(accuracy={accuracy:.2f}, turn={memory.current_turn()})."
                ),
            )

        # Adaptation: avoid repeating very recent topics and avoid repeating the same
        # content category/tag back-to-back when possible.
        recent_topics = set(memory.recent_practice_topics(n=2))
        recent_categories = {topic_category(t) for t in recent_topics}
        recent_tags = set()
        for topic in recent_topics:
            recent_tags.update(topic_tags(topic))
        unlocked_topics = [
            t for t in topics if self._topic_unlocked(learner, memory, t)
        ]
        if not unlocked_topics:
            unlocked_topics = topics

        candidates = [
            t
            for t in unlocked_topics
            if t not in recent_topics
            and topic_category(t) not in recent_categories
            and not (set(topic_tags(t)) & recent_tags)
        ]
        if not candidates:
            candidates = [
                t for t in unlocked_topics if t not in recent_topics
            ] or unlocked_topics

        candidates, focus_note = self._apply_learner_focus(learner, candidates)

        weakest_topic = min(candidates, key=lambda t: learner.get_mastery(t))
        weakest_score = learner.get_mastery(weakest_topic)
        attempts = memory.topic_history.get(weakest_topic, [])
        accuracy = memory.topic_accuracy(weakest_topic)

        def with_focus(reason: str) -> str:
            return f"{reason} {focus_note}".strip() if focus_note else reason

        # Adaptation: use both confidence and topic accuracy to decide teach vs practice.
        if learner.confidence < 0.45:
            return Plan(
                action="explain",
                topic=weakest_topic,
                reason=with_focus(
                    "Learner confidence is low overall; scaffold with an explanation."
                ),
            )

        if weakest_score < 0.55 or accuracy < 0.55 and len(attempts) < 2:
            return Plan(
                action="explain",
                topic=weakest_topic,
                reason=with_focus(
                    "Low mastery / early-stage topic; explain before practice."
                ),
            )

        if accuracy < 0.7 and len(attempts) >= 1:
            return Plan(
                action="practice",
                topic=weakest_topic,
                reason=with_focus(
                    "Topic accuracy is still weak; keep it in practice mode."
                ),
            )

        # Default: practice even for mostly stable topics to keep the loop going.
        return Plan(
            action="practice",
            topic=weakest_topic,
            reason=with_focus("Continue guided practice to improve retention."),
        )
