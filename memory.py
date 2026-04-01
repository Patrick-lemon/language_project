from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Memory:
    interaction_log: list[dict[str, object]] = field(default_factory=list)
    topic_history: dict[str, list[bool]] = field(default_factory=dict)
    completed_tasks: list[str] = field(default_factory=list)

    def remember(self, event: dict[str, object]) -> None:
        self.interaction_log.append(event)

    def update_topic_result(self, topic: str, correct: bool) -> None:
        self.topic_history.setdefault(topic, []).append(correct)

    def topic_accuracy(self, topic: str) -> float:
        attempts = self.topic_history.get(topic, [])
        if not attempts:
            return 0.0
        return sum(1 for item in attempts if item) / len(attempts)

    def recent_events(self, n: int = 5) -> list[dict[str, object]]:
        return self.interaction_log[-n:]

    def mark_task_completed(self, task: str) -> None:
        self.completed_tasks.append(task)

    def practice_attempts(self) -> list[dict[str, object]]:
        return [e for e in self.interaction_log if e.get("type") == "practice_attempt"]

    def last_practice_attempt(self) -> Optional[dict[str, object]]:
        attempts = self.practice_attempts()
        if not attempts:
            return None
        last = attempts[-1]
        return last

    def recent_practice_topics(self, n: int = 2) -> list[str]:
        attempts = self.practice_attempts()
        recent = attempts[-n:] if n > 0 else []
        topics: list[str] = []
        for e in recent:
            topic = e.get("topic")
            if isinstance(topic, str):
                topics.append(topic)
        return topics
