from dataclasses import dataclass, field
from typing import Any, Optional


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

    def to_dict(self) -> dict[str, object]:
        return {
            "interaction_log": list(self.interaction_log),
            "topic_history": {
                topic: [bool(item) for item in attempts]
                for topic, attempts in self.topic_history.items()
            },
            "completed_tasks": list(self.completed_tasks),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Memory":
        if not isinstance(data, dict):
            return cls()

        interaction_log: list[dict[str, object]] = []
        raw_log = data.get("interaction_log")
        if isinstance(raw_log, list):
            for item in raw_log:
                if isinstance(item, dict):
                    interaction_log.append(dict(item))

        topic_history: dict[str, list[bool]] = {}
        raw_history = data.get("topic_history")
        if isinstance(raw_history, dict):
            for raw_topic, raw_attempts in raw_history.items():
                topic = str(raw_topic).strip()
                if not topic or not isinstance(raw_attempts, list):
                    continue
                topic_history[topic] = [bool(item) for item in raw_attempts]

        completed_tasks: list[str] = []
        raw_tasks = data.get("completed_tasks")
        if isinstance(raw_tasks, list):
            for item in raw_tasks:
                task = str(item).strip()
                if task:
                    completed_tasks.append(task)

        return cls(
            interaction_log=interaction_log,
            topic_history=topic_history,
            completed_tasks=completed_tasks,
        )
