from tools.content_bank import CONTENT_BANK


def _normalize_text(s: str) -> str:
    # Normalize common formatting differences for Jyutping/romanization input.
    return "".join(s.strip().lower().split())


def check_answer(topic: str, answer: str) -> tuple[bool, str]:
    entry = CONTENT_BANK[topic]
    expected_answers = entry.get("answers")
    if isinstance(expected_answers, list) and expected_answers:
        expected_list = [str(x) for x in expected_answers]
        expected_norm = {_normalize_text(x) for x in expected_list}
        actual_norm = _normalize_text(answer)
        if actual_norm in expected_norm:
            return True, "Correct form."
        pretty = ", ".join(expected_list[:3])
        return False, f"Expected one of: {pretty}"

    # Backward-compatible fallback (older single-answer schema).
    expected_single = entry.get("answer")
    if isinstance(expected_single, str):
        expected = _normalize_text(expected_single)
        actual = _normalize_text(answer)
        if actual == expected:
            return True, "Correct form."
        return False, f"Expected '{expected_single}'."

    return False, "No expected answer configured for this topic."
