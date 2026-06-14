"""
Tool layer: LLM-backed text generation (OpenAI-compatible Chat Completions API).

Enable by setting environment variables (see README). If disabled or on error,
falls back to deterministic stub text so the tutor still runs offline.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from tools.skill_loader import get_skill_section


def _llm_enabled() -> bool:
    return os.environ.get("TUTOR_LLM_ENABLED", "").strip().lower() in (
        "1",
        "true",
        "yes",
    )


def _api_key() -> str:
    return (
        os.environ.get("TUTOR_LLM_API_KEY", "").strip()
        or os.environ.get("OPENAI_API_KEY", "").strip()
        or os.environ.get("OPENROUTER_API_KEY", "").strip()
    )


def _base_url() -> str:
    explicit = os.environ.get("TUTOR_LLM_BASE_URL", "").strip().rstrip("/")
    if explicit:
        return explicit
    if os.environ.get("OPENROUTER_API_KEY", "").strip():
        return "https://openrouter.ai/api/v1"
    return "https://api.openai.com/v1"


def _model() -> str:
    return os.environ.get("TUTOR_LLM_MODEL", "gpt-4o-mini").strip()


def describe_runtime_mode() -> str:
    """One-line summary for the dialogue manager (startup banner)."""
    if not _llm_enabled():
        return (
            "LLM: off (stub text). Set TUTOR_LLM_ENABLED=1 and an API key to use a real model."
        )
    if not _api_key():
        return (
            "LLM: enabled but no API key set; requests will fall back to stub text."
        )
    return f"LLM: on | API base: {_base_url()} | model: {_model()}"


def _chat_completion(messages: list[dict[str, str]], *, max_tokens: int = 400) -> str:
    key = _api_key()
    if not key:
        raise RuntimeError("LLM enabled but no API key set")

    base = _base_url()
    url = f"{base}/chat/completions"
    payload = {
        "model": _model(),
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": 0.5,
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {key}",
    }
    # OpenRouter recommends these for attribution (optional).
    if "openrouter" in base.lower():
        ref = os.environ.get("OPENROUTER_HTTP_REFERER", "").strip()
        title = os.environ.get("OPENROUTER_APP_TITLE", "LanguageTutor").strip()
        if ref:
            headers["HTTP-Referer"] = ref
        if title:
            headers["X-Title"] = title

    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=90) as resp:
        body = json.loads(resp.read().decode("utf-8"))
    choices = body.get("choices") or []
    if not choices:
        raise RuntimeError("LLM response missing choices")
    message = choices[0].get("message") or {}
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("LLM response missing content")
    return content.strip()


def _compact_json(data: object) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def _topic_display_name(topic: str) -> str:
    return topic.replace("cantonese_", "").replace("_", " ")


def _recent_topic_history(
    recent_events: list[dict[str, object]] | None,
) -> list[dict[str, object]]:
    if not recent_events:
        return []
    trimmed: list[dict[str, object]] = []
    for event in recent_events[-4:]:
        if event.get("type") != "practice_attempt":
            continue
        trimmed.append(
            {
                "topic": event.get("topic"),
                "answer": event.get("answer"),
                "correct": event.get("correct"),
            }
        )
    return trimmed


def _extract_json_object(raw_text: str) -> dict[str, Any]:
    text = raw_text.strip()
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end < start:
        raise RuntimeError("LLM response missing JSON object")
    parsed = json.loads(text[start : end + 1])
    if not isinstance(parsed, dict):
        raise RuntimeError("LLM JSON response was not an object")
    return parsed


def _chat_json(
    messages: list[dict[str, str]],
    *,
    max_tokens: int = 400,
) -> dict[str, Any]:
    return _extract_json_object(_chat_completion(messages, max_tokens=max_tokens))


def _fallback_explanation(topic: str, base_text: str) -> str:
    return f"{base_text}\nTip: Focus on one short pattern at a time in {topic}."


def _fallback_feedback(topic: str, is_correct: bool) -> str:
    if is_correct:
        return f"You handled {topic} well. Keep the same pattern in your next sentence."
    return (
        f"Your {topic} answer needs adjustment. Try one corrected example before continuing."
    )


def generate_explanation(
    topic: str,
    base_text: str,
    learner_snapshot: dict[str, object] | None = None,
    recent_events: list[dict[str, object]] | None = None,
) -> str:
    if not _llm_enabled():
        return _fallback_explanation(topic, base_text)

    try:
        guidance = get_skill_section("explain skill")
        return _chat_completion(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a concise Cantonese tutor for English speakers. "
                        "Explain in 2-4 short sentences. No markdown headings. "
                        "Respect the curriculum note as ground truth."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Skill guidance:\n{guidance}\n\n"
                        f"Topic tag: {topic}\n"
                        f"Readable topic: {_topic_display_name(topic)}\n"
                        f"Curriculum note (ground truth): {base_text}\n\n"
                        f"Learner snapshot: {_compact_json(learner_snapshot or {})}\n"
                        f"Recent practice history: {_compact_json(_recent_topic_history(recent_events))}\n\n"
                        "Expand slightly with one concrete example that uses Cantonese "
                        "(Jyutping and/or characters) and an English gloss. Stay accurate "
                        "and adapt your wording to the learner level and recent mistakes."
                    ),
                },
            ],
            max_tokens=280,
        )
    except (
        OSError,
        urllib.error.URLError,
        RuntimeError,
        json.JSONDecodeError,
        KeyError,
        IndexError,
    ):
        return _fallback_explanation(topic, base_text)


def generate_practice_prompt(
    topic: str,
    base_question: str,
    learner_snapshot: dict[str, object] | None = None,
    recent_events: list[dict[str, object]] | None = None,
) -> str:
    if not _llm_enabled():
        return base_question

    try:
        guidance = get_skill_section("practice skill")
        result = _chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a Cantonese tutor building one learner prompt. "
                        "Return JSON with keys prompt and coaching_note. "
                        "The prompt must stay faithful to the curriculum task. "
                        "Keep everything concise."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Skill guidance:\n{guidance}\n\n"
                        f"Topic tag: {topic}\n"
                        f"Readable topic: {_topic_display_name(topic)}\n"
                        f"Base curriculum practice prompt: {base_question}\n"
                        f"Learner snapshot: {_compact_json(learner_snapshot or {})}\n"
                        f"Recent practice history: {_compact_json(_recent_topic_history(recent_events))}\n\n"
                        "Adapt the wording slightly to sound like a live tutor. "
                        "If the learner recently struggled, add a tiny hint. "
                        "Do not change the target meaning or add extra tasks."
                    ),
                },
            ],
            max_tokens=220,
        )
        prompt = str(result.get("prompt", "")).strip()
        coaching_note = str(result.get("coaching_note", "")).strip()
        if not prompt:
            raise RuntimeError("LLM prompt response missing prompt")
        return f"{prompt} {coaching_note}".strip()
    except (
        OSError,
        urllib.error.URLError,
        RuntimeError,
        json.JSONDecodeError,
        KeyError,
        IndexError,
    ):
        return base_question


def generate_feedback(
    topic: str,
    is_correct: bool,
    learner_answer: str = "",
) -> str:
    if not _llm_enabled():
        return _fallback_feedback(topic, is_correct)

    try:
        guidance = get_skill_section("correction skill")
        user_block = (
            f"Skill guidance:\n{guidance}\n\n"
            f"Topic: {topic}\n"
            f"Learner answer: {learner_answer!r}\n"
            f"Official correctness: {'correct' if is_correct else 'incorrect'}.\n\n"
            "Give one short sentence of encouragement if correct, "
            "or one actionable correction hint if incorrect. "
            "The hint should be phrased in English and reference Cantonese pronunciation/characters lightly. "
            "Do not contradict correctness."
        )
        return _chat_completion(
            [
                {
                    "role": "system",
                    "content": (
                        "You are a language tutor. Be brief and pedagogical. "
                        "Max 2 sentences."
                    ),
                },
                {"role": "user", "content": user_block},
            ],
            max_tokens=120,
        )
    except (
        OSError,
        urllib.error.URLError,
        RuntimeError,
        json.JSONDecodeError,
        KeyError,
        IndexError,
    ):
        return _fallback_feedback(topic, is_correct)


def evaluate_answer(
    topic: str,
    learner_answer: str,
    expected_answers: list[str],
    grammar_result: tuple[bool, str],
    learner_snapshot: dict[str, object] | None = None,
    recent_events: list[dict[str, object]] | None = None,
) -> dict[str, object]:
    """
    Hybrid evaluator:
    - deterministic grammar_result remains the first safety check
    - LLM can rescue near-miss but semantically correct variants and produce better coaching
    """
    is_correct, grammar_message = grammar_result
    feedback = generate_feedback(topic, is_correct, learner_answer)

    if is_correct or not _llm_enabled():
        return {
            "correct": is_correct,
            "grammar_message": grammar_message,
            "feedback": feedback,
        }

    try:
        guidance = get_skill_section("correction skill")
        result = _chat_json(
            [
                {
                    "role": "system",
                    "content": (
                        "You are grading a beginner Cantonese exercise. "
                        "Return JSON with keys correct, grammar_message, feedback. "
                        "Only mark correct when the learner answer is a clearly acceptable "
                        "variant of the expected Cantonese answer for this exact exercise. "
                        "Do not reward unrelated but plausible Cantonese phrases."
                    ),
                },
                {
                    "role": "user",
                    "content": (
                        f"Skill guidance:\n{guidance}\n\n"
                        f"Topic tag: {topic}\n"
                        f"Readable topic: {_topic_display_name(topic)}\n"
                        f"Accepted answers: {_compact_json(expected_answers)}\n"
                        f"Learner answer: {learner_answer}\n"
                        f"Deterministic checker verdict: {_compact_json({'correct': is_correct, 'message': grammar_message})}\n"
                        f"Learner snapshot: {_compact_json(learner_snapshot or {})}\n"
                        f"Recent practice history: {_compact_json(_recent_topic_history(recent_events))}\n\n"
                        "Judge whether the answer should count as correct. "
                        "If incorrect, explain the closest fix in simple English and include "
                        "one corrected Cantonese form. If correct, keep feedback encouraging "
                        "and brief."
                    ),
                },
            ],
            max_tokens=260,
        )
        llm_correct = bool(result.get("correct"))
        llm_grammar = str(result.get("grammar_message", "")).strip()
        llm_feedback = str(result.get("feedback", "")).strip()
        return {
            "correct": llm_correct,
            "grammar_message": llm_grammar or grammar_message,
            "feedback": llm_feedback or feedback,
        }
    except (
        OSError,
        urllib.error.URLError,
        RuntimeError,
        json.JSONDecodeError,
        KeyError,
        IndexError,
    ):
        return {
            "correct": is_correct,
            "grammar_message": grammar_message,
            "feedback": feedback,
        }
