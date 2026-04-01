from __future__ import annotations

from functools import lru_cache
from pathlib import Path


SKILL_PATH = Path(__file__).resolve().parent.parent / "skill" / "SKILL.md"


def _strip_frontmatter(text: str) -> str:
    if not text.startswith("---\n"):
        return text
    parts = text.split("\n---\n", 1)
    if len(parts) != 2:
        return text
    return parts[1]


@lru_cache(maxsize=1)
def load_skill_markdown() -> str:
    return SKILL_PATH.read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def load_skill_sections() -> dict[str, str]:
    text = _strip_frontmatter(load_skill_markdown())
    sections: dict[str, list[str]] = {}
    current = "root"
    sections[current] = []

    for line in text.splitlines():
        if line.startswith("## "):
            current = line[3:].strip().lower()
            sections.setdefault(current, [])
            continue
        sections.setdefault(current, []).append(line)

    return {
        name: "\n".join(lines).strip()
        for name, lines in sections.items()
        if "\n".join(lines).strip()
    }


def get_skill_section(name: str) -> str:
    return load_skill_sections().get(name.strip().lower(), "")
