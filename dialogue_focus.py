"""Learner-driven focus: onboarding + per-turn commands for what to study."""

from __future__ import annotations

from typing import Optional

from learner_model import LearnerModel
from tools.content_bank import list_topics, topic_category


VALID_FOCUS_MODES = ("balanced", "survival", "question", "scenario", "custom")


def print_topic_catalog() -> None:
    topics = list_topics()
    print("\nAvailable topics (id → category):")
    for t in topics:
        print(f"  • {t}  [{topic_category(t)}]")
    print()


def apply_initial_focus_choice(learner: LearnerModel, choice: str) -> None:
    c = choice.strip()
    if c == "2":
        learner.learning_focus = "survival"
    elif c == "3":
        learner.learning_focus = "question"
    elif c == "4":
        learner.learning_focus = "scenario"
    elif c == "5":
        learner.learning_focus = "custom"
        raw = input(
            "Enter topic ids separated by commas (or type `menu` later for `list`): "
        ).strip()
        learner.custom_focus_topics = _parse_topic_list(raw)
    else:
        learner.learning_focus = "balanced"


def _parse_topic_list(raw: str) -> list[str]:
    valid = set(list_topics())
    out: list[str] = []
    for part in raw.replace(";", ",").split(","):
        key = part.strip()
        if key and key in valid and key not in out:
            out.append(key)
    return out


def process_focus_command(learner: LearnerModel, line: str) -> Optional[str]:
    """
    Handle one learner command line. Returns a short user-facing message, or None if no command.
    """
    s = line.strip()
    if not s:
        return None
    lower = s.lower()

    if lower == "list":
        print_topic_catalog()
        return "Listed topic ids above."

    if lower.startswith("focus "):
        mode = lower.split(None, 1)[1].strip()
        if mode not in VALID_FOCUS_MODES:
            return f"Unknown focus '{mode}'. Use: {', '.join(VALID_FOCUS_MODES)}"
        learner.learning_focus = mode
        if mode != "custom":
            learner.custom_focus_topics = []
        return f"Focus set to: {mode}"

    if lower.startswith("topics "):
        rest = s.split(None, 1)[1].strip()
        if rest.lower() == "clear":
            learner.custom_focus_topics = []
            if learner.learning_focus == "custom":
                learner.learning_focus = "balanced"
            return "Cleared custom topic list; focus is balanced."
        topics = _parse_topic_list(rest)
        if not topics:
            return "No valid topic ids found. Type `list` to see ids."
        learner.learning_focus = "custom"
        learner.custom_focus_topics = topics
        return f"Custom topics: {', '.join(topics)}"

    return (
        "Unknown command. Try: `focus balanced`, `focus survival`, `topics id1,id2`, "
        "`topics clear`, or `list`."
    )


def run_focus_menu(learner: LearnerModel) -> None:
    """Small REPL for changing focus; blank line exits."""
    print(
        "\n--- Focus menu (press Enter on an empty line to close) ---\n"
        "Examples: `focus survival` | `topics id1,id2` | `topics clear` | `list`\n"
    )
    while True:
        line = input("focus> ").strip()
        if not line:
            print("--- Back to the lesson ---\n")
            return
        msg = process_focus_command(learner, line)
        if msg:
            print(msg)
        print(f"Current focus: {focus_summary(learner)}")


def focus_summary(learner: LearnerModel) -> str:
    if learner.learning_focus == "custom" and learner.custom_focus_topics:
        return f"custom → {', '.join(learner.custom_focus_topics)}"
    if learner.learning_focus == "custom":
        return "custom (no topics yet — use `topics id1,id2`)"
    return learner.learning_focus
