from dataclasses import dataclass, field


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
