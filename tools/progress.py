"""Scenario unlock progress for the dialogue manager (visible tutoring progression)."""

from __future__ import annotations

from learner_model import LearnerModel
from tools.content_bank import (
    SCENARIO_PREREQUISITE_MASTERY,
    list_topics,
    topic_category,
    topic_prerequisites,
)


def format_scenario_progress(learner: LearnerModel) -> str:
    """Human-readable locked/unlocked lines for each scenario topic."""
    threshold = SCENARIO_PREREQUISITE_MASTERY
    scenario_topics = [t for t in list_topics() if topic_category(t) == "scenario"]
    if not scenario_topics:
        return "Scenario progress: (no scenario topics in content bank)"

    lines: list[str] = [
        f"Scenario progress (unlock at mastery >= {threshold:.2f} on each prerequisite):"
    ]
    for topic in scenario_topics:
        prereqs = topic_prerequisites(topic)
        if not prereqs:
            lines.append(f"  - {topic}: UNLOCKED (no prerequisites)")
            continue
        missing: list[str] = []
        for p in prereqs:
            m = learner.get_mastery(p)
            if m < threshold:
                missing.append(f"{p}={m:.2f}")
        if not missing:
            lines.append(f"  - {topic}: UNLOCKED")
        else:
            lines.append(f"  - {topic}: LOCKED - raise: {', '.join(missing)}")
    return "\n".join(lines)
