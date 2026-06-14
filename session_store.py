from __future__ import annotations

import json
import re
from pathlib import Path

from learner_model import LearnerModel
from memory import Memory


STATE_DIR = Path(__file__).resolve().parent / "state"


def _slugify(name: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "_", name.strip().lower())
    return cleaned.strip("_") or "student"


def state_path_for_learner(name: str) -> Path:
    return STATE_DIR / f"{_slugify(name)}.json"


def save_session_state(learner: LearnerModel, memory: Memory) -> Path:
    path = state_path_for_learner(learner.name)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": 1,
        "learner": learner.to_dict(),
        "memory": memory.to_dict(),
    }
    path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return path


def load_session_state(name: str) -> tuple[LearnerModel, Memory] | None:
    path = state_path_for_learner(name)
    if not path.exists():
        return None

    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None

    learner = LearnerModel.from_dict(payload.get("learner", {}))
    memory = Memory.from_dict(payload.get("memory", {}))
    if not learner.name.strip():
        learner.name = name
    return learner, memory
