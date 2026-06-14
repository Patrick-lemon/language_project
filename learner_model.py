from dataclasses import dataclass, field
from typing import Any


def _string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []
    items: list[str] = []
    for raw in value:
        text = str(raw).strip()
        if text and text not in items:
            items.append(text)
    return items


def _float_map(value: object) -> dict[str, float]:
    if not isinstance(value, dict):
        return {}
    out: dict[str, float] = {}
    for raw_key, raw_score in value.items():
        key = str(raw_key).strip()
        if not key:
            continue
        try:
            score = float(raw_score)
        except (TypeError, ValueError):
            continue
        out[key] = max(0.0, min(1.0, score))
    return out


def _bounded_float(value: object, default: float) -> float:
    try:
        score = float(value)
    except (TypeError, ValueError):
        return default
    return max(0.0, min(1.0, score))


@dataclass
class LearnerModel:
    name: str
    level: str = "A2"
    target_language: str = "Cantonese"
    preferred_mode: str = "guided"
    active_goals: list[str] = field(default_factory=lambda: ["daily conversation"])
    confidence: float = 0.5
    mastery_by_topic: dict[str, float] = field(default_factory=dict)
    known_vocabulary: set[str] = field(default_factory=set)
    weak_grammar_points: set[str] = field(default_factory=set)
    recent_errors: list[str] = field(default_factory=list)
    review_queue: list[str] = field(default_factory=list)
    # Learner agency: what to prioritize (planner respects when possible).
    learning_focus: str = "balanced"  # balanced | survival | question | scenario | custom
    custom_focus_topics: list[str] = field(default_factory=list)

    def get_mastery(self, topic: str) -> float:
        return self.mastery_by_topic.get(topic, 0.3)

    def record_result(self, topic: str, correct: bool) -> None:
        current = self.get_mastery(topic)
        delta = 0.15 if correct else -0.1
        updated = max(0.0, min(1.0, current + delta))
        self.mastery_by_topic[topic] = updated

        if correct:
            self.confidence = min(1.0, self.confidence + 0.05)
            self.weak_grammar_points.discard(topic)
        else:
            self.confidence = max(0.0, self.confidence - 0.07)
            self.recent_errors.append(topic)
            self.weak_grammar_points.add(topic)
            self.add_to_review(topic)

    def add_vocabulary_item(self, token: str) -> None:
        normalized = token.strip().lower()
        if normalized:
            self.known_vocabulary.add(normalized)

    def add_to_review(self, topic: str) -> None:
        if topic not in self.review_queue:
            self.review_queue.append(topic)

    def to_dict(self) -> dict[str, object]:
        return {
            "name": self.name,
            "level": self.level,
            "target_language": self.target_language,
            "preferred_mode": self.preferred_mode,
            "active_goals": list(self.active_goals),
            "confidence": self.confidence,
            "mastery_by_topic": dict(self.mastery_by_topic),
            "known_vocabulary": sorted(self.known_vocabulary),
            "weak_grammar_points": sorted(self.weak_grammar_points),
            "recent_errors": list(self.recent_errors),
            "review_queue": list(self.review_queue),
            "learning_focus": self.learning_focus,
            "custom_focus_topics": list(self.custom_focus_topics),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "LearnerModel":
        if not isinstance(data, dict):
            return cls(name="Student")

        return cls(
            name=str(data.get("name") or "Student"),
            level=str(data.get("level") or "A2"),
            target_language=str(data.get("target_language") or "Cantonese"),
            preferred_mode=str(data.get("preferred_mode") or "guided"),
            active_goals=_string_list(data.get("active_goals")) or ["daily conversation"],
            confidence=_bounded_float(data.get("confidence"), 0.5),
            mastery_by_topic=_float_map(data.get("mastery_by_topic")),
            known_vocabulary=set(_string_list(data.get("known_vocabulary"))),
            weak_grammar_points=set(_string_list(data.get("weak_grammar_points"))),
            recent_errors=_string_list(data.get("recent_errors")),
            review_queue=_string_list(data.get("review_queue")),
            learning_focus=str(data.get("learning_focus") or "balanced"),
            custom_focus_topics=_string_list(data.get("custom_focus_topics")),
        )

    def snapshot(self) -> dict[str, object]:
        return {
            "name": self.name,
            "level": self.level,
            "target_language": self.target_language,
            "preferred_mode": self.preferred_mode,
            "active_goals": list(self.active_goals),
            "confidence": round(self.confidence, 2),
            "mastery_by_topic": {
                topic: round(score, 2) for topic, score in self.mastery_by_topic.items()
            },
            "weak_grammar_points": sorted(self.weak_grammar_points),
            "review_queue": list(self.review_queue),
            "recent_errors": list(self.recent_errors[-3:]),
            "learning_focus": self.learning_focus,
            "custom_focus_topics": list(self.custom_focus_topics),
        }
