from __future__ import annotations

import re
import secrets
import unicodedata
from dataclasses import dataclass, field
from threading import Lock

from dialogue_focus import VALID_FOCUS_MODES, focus_summary
from learner_model import LearnerModel
from memory import Memory
from planner import Planner
from session_store import load_session_state, save_session_state
from tools.content_bank import CONTENT_BANK, list_topics, topic_category
from tools.llm import (
    describe_runtime_mode,
    evaluate_answer,
    generate_explanation,
)
from tools.tutor_actions import review_topic_intro, update_review_status


def _topic_title(topic: str) -> str:
    return topic.replace("cantonese_", "").replace("_", " ").title()


def _parse_custom_topics(raw_topics: str | list[str] | None) -> list[str]:
    valid = set(list_topics())
    if raw_topics is None:
        return []
    if isinstance(raw_topics, list):
        parts = raw_topics
    else:
        parts = raw_topics.replace(";", ",").split(",")
    out: list[str] = []
    for part in parts:
        key = str(part).strip()
        if key and key in valid and key not in out:
            out.append(key)
    return out


def _extract_english_gloss(question: str, topic: str) -> str:
    matches = re.findall(r"'([^']+)'", question)
    for match in matches:
        text = match.strip()
        if text:
            return text
    return _topic_title(topic)


def _is_written_form(text: str) -> bool:
    return any(ord(ch) > 127 for ch in text)


ASR_TEXT_REPLACEMENTS: tuple[tuple[str, str], ...] = (
    ("啊", "呀"),
    ("您好", "你好"),
    ("谢谢", "多謝"),
    ("謝謝", "多謝"),
    ("对不起", "對唔住"),
    ("對不起", "對唔住"),
    ("再见", "再見"),
    ("系", "係"),
    ("边", "邊"),
    ("哪裡", "邊度"),
    ("哪里", "邊度"),
    ("在哪裡", "喺邊度"),
    ("在哪里", "喺邊度"),
    ("不是", "唔係"),
    ("不明白", "唔明"),
    ("不懂", "唔明"),
    ("说", "講"),
    ("說", "講"),
    ("慢点", "慢啲"),
    ("慢點", "慢啲"),
    ("这里", "呢度"),
    ("這裡", "呢度"),
    ("这个", "呢個"),
    ("這個", "呢個"),
    ("地铁站", "港鐵站"),
    ("地鐵站", "港鐵站"),
    ("港铁站", "港鐵站"),
    ("买单", "埋單"),
    ("買單", "埋單"),
    ("外卖", "外賣"),
    ("太贵", "太貴"),
    ("现金", "現金"),
    ("问题", "問題"),
    ("没问题", "冇問題"),
    ("沒有問題", "冇問題"),
    ("什么意思", "咩意思"),
    ("什麼意思", "咩意思"),
)


def _normalize_asr_variants(text: str) -> str:
    normalized = unicodedata.normalize("NFKC", text.strip().lower())
    for source, target in ASR_TEXT_REPLACEMENTS:
        normalized = normalized.replace(source, target)
    return normalized


def _normalize_spoken_text(text: str, *, strip_digits: bool = False) -> str:
    lowered = _normalize_asr_variants(text)
    if strip_digits:
        lowered = "".join(ch for ch in lowered if not ch.isdigit())
    return "".join(ch for ch in lowered if ch.isalnum())


def _is_short_target(romanization: str, characters: str) -> bool:
    compact = _normalize_spoken_text(romanization, strip_digits=True)
    if compact and len(compact) <= 6:
        return True
    written = "".join(ch for ch in characters if not ch.isspace())
    return bool(written) and len(written) <= 2


def _spoken_checker(topic: str, learner_answer: str) -> tuple[bool, str]:
    target = _target_bundle(topic)
    answers = [str(x) for x in CONTENT_BANK[topic].get("answers", [])]
    answers.extend(str(x) for x in target.get("voice_answers", []))
    actual = _normalize_spoken_text(learner_answer)
    actual_nodigit = _normalize_spoken_text(learner_answer, strip_digits=True)
    if not actual:
        return False, "I did not catch a usable spoken answer."

    for answer in answers:
        expected = _normalize_spoken_text(answer)
        expected_nodigit = _normalize_spoken_text(answer, strip_digits=True)
        if actual == expected or actual_nodigit == expected_nodigit:
            return True, "Spoken form matched the target line."
        if expected_nodigit and actual_nodigit and expected_nodigit in actual_nodigit:
            if len(expected_nodigit) <= 6:
                return True, "Short target detected inside a longer spoken answer."
        if len(expected) >= 4 and (
            expected in actual
            or actual in expected
            or (expected_nodigit and expected_nodigit in actual_nodigit)
            or (actual_nodigit and actual_nodigit in expected_nodigit)
        ):
            return True, "Close spoken match."

    examples = ", ".join(answers[:2]) if answers else _topic_title(topic)
    return False, f"Target line: {examples}"


def _candidate_texts(primary: str, alternatives: list[str] | None = None) -> list[str]:
    ordered: list[str] = []
    for candidate in [primary, *(alternatives or [])]:
        text = str(candidate or "").strip()
        if text and text not in ordered:
            ordered.append(text)
    return ordered


def _pick_best_candidate(
    topic: str | None,
    primary: str,
    alternatives: list[str] | None = None,
) -> tuple[str, str | None]:
    candidates = _candidate_texts(primary, alternatives)
    if not candidates:
        return primary, None

    for candidate in candidates:
        command = _voice_command(candidate)
        if command:
            return candidate, command

    if not topic:
        return candidates[0], None

    best = candidates[0]
    best_score = -1
    for candidate in candidates:
        correct, message = _spoken_checker(topic, candidate)
        score = 0
        if correct:
            score = 100 if "matched the target line" in message.lower() else 80
        elif "target line:" in message.lower():
            score = 10
        if score > best_score:
            best = candidate
            best_score = score
    return best, None


def _voice_command(text: str) -> str | None:
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    repeat_phrases = (
        "repeat again",
        "repeat it",
        "say it again",
        "say that again",
        "again please",
        "one more time",
        "demo again",
        "model again",
        "repeat",
        "再讲一次",
        "再講一次",
        "再说一次",
        "再說一次",
        "再来一次",
        "再來一次",
        "示范一次",
        "示範一次",
        "重复一次",
        "重複一次",
    )
    next_phrases = (
        "next lesson",
        "next one",
        "move on",
        "keep going",
        "continue",
        "go on",
        "下一课",
        "下一課",
        "下一个",
        "下一個",
        "继续",
        "繼續",
        "换一个",
        "換一個",
    )
    if any(phrase in normalized for phrase in repeat_phrases):
        return "repeat"
    if any(phrase in normalized for phrase in next_phrases):
        return "next"
    return None


VOICE_PRACTICE_OVERRIDES: dict[str, dict[str, object]] = {
    "cantonese_greetings": {
        "spoken_characters": "你好呀",
        "spoken_romanization": "nei5 hou2 aa3",
        "voice_answers": ["你好呀", "nei5 hou2 aa3", "nei hou2 aa3"],
    },
    "cantonese_thank_you": {
        "spoken_characters": "多謝你呀",
        "spoken_romanization": "do1 ze6 nei5 aa3",
        "voice_answers": ["多謝你呀", "do1 ze6 nei5 aa3", "do ze6 nei5 aa3"],
    },
    "cantonese_please": {
        "spoken_characters": "請幫我",
        "spoken_romanization": "cing2 bong1 ngo5",
        "spoken_english": "please help me",
        "voice_answers": ["請幫我", "cing2 bong1 ngo5", "cing bong ngo"],
    },
    "cantonese_excuse_me": {
        "spoken_characters": "唔該呀",
        "spoken_romanization": "m4 goi1 aa3",
        "voice_answers": ["唔該呀", "m4 goi1 aa3", "m4 goi aa3"],
    },
    "cantonese_sorry": {
        "spoken_characters": "對唔住呀",
        "spoken_romanization": "deoi3 m4 zyu6 aa3",
        "voice_answers": ["對唔住呀", "deoi3 m4 zyu6 aa3", "deoi m zyu aa"],
    },
    "cantonese_yes": {
        "spoken_characters": "係呀",
        "spoken_romanization": "hai6 aa3",
        "voice_answers": ["係呀", "hai6 aa3", "hai aa3"],
    },
    "cantonese_no": {
        "spoken_characters": "唔係呀",
        "spoken_romanization": "m4 hai6 aa3",
        "voice_answers": ["唔係呀", "m4 hai6 aa3", "m hai aa3"],
    },
    "cantonese_i_dont_understand": {
        "spoken_characters": "我唔明呀",
        "spoken_romanization": "ngo5 m4 ming4 aa3",
        "voice_answers": ["我唔明呀", "ngo5 m4 ming4 aa3", "ngo m ming aa"],
    },
    "cantonese_say_again": {
        "spoken_characters": "請再講一次",
        "spoken_romanization": "cing2 zoi3 gong2 jat1 ci3",
        "voice_answers": [
            "請再講一次",
            "cing2 zoi3 gong2 jat1 ci3",
            "cing zoi gong jat ci",
        ],
    },
    "cantonese_speak_slowly": {
        "spoken_characters": "講慢啲呀",
        "spoken_romanization": "gong2 maan6 di1 aa3",
        "voice_answers": ["講慢啲呀", "gong2 maan6 di1 aa3", "gong maan di aa"],
    },
    "cantonese_learning_cantonese": {
        "spoken_characters": "我學緊廣東話",
        "spoken_romanization": "ngo5 hok6 gan2 gwong2 dung1 waa2",
        "voice_answers": [
            "我學緊廣東話",
            "ngo5 hok6 gan2 gwong2 dung1 waa2",
            "ngo hok gan gwong dung waa",
        ],
    },
    "cantonese_speak_english": {
        "spoken_characters": "你識唔識講英文呀？",
        "spoken_romanization": "nei5 sik1 m4 sik1 gong2 jing1 man2 aa3",
        "voice_answers": [
            "你識唔識講英文呀",
            "你識唔識講英文呀？",
            "nei5 sik1 m4 sik1 gong2 jing1 man2 aa3",
            "nei sik m sik gong jing man aa",
        ],
    },
    "cantonese_what": {
        "spoken_characters": "咩話呀？",
        "spoken_romanization": "me1 waa6 aa3",
        "spoken_english": "what did you say",
        "voice_answers": ["咩話呀", "咩話呀？", "me1 waa6 aa3", "me waa aa"],
    },
    "cantonese_where": {
        "spoken_characters": "喺邊度呀？",
        "spoken_romanization": "hai2 bin1 dou6 aa3",
        "spoken_english": "where is it",
        "voice_answers": ["喺邊度呀", "喺邊度呀？", "hai2 bin1 dou6 aa3", "hai bin dou aa"],
    },
    "cantonese_left": {
        "spoken_characters": "左邊呀",
        "spoken_romanization": "zo2 bin1 aa3",
        "voice_answers": ["左邊呀", "zo2 bin1 aa3", "zo bin aa"],
    },
    "cantonese_right": {
        "spoken_characters": "右邊呀",
        "spoken_romanization": "jau6 bin1 aa3",
        "voice_answers": ["右邊呀", "jau6 bin1 aa3", "jau bin aa"],
    },
    "cantonese_straight_ahead": {
        "spoken_characters": "一直行呀",
        "spoken_romanization": "jat1 zik6 haang4 aa3",
        "voice_answers": ["一直行呀", "jat1 zik6 haang4 aa3", "jat zik haang aa"],
    },
    "cantonese_this_one": {
        "spoken_characters": "呢個呀",
        "spoken_romanization": "ni1 go3 aa3",
        "voice_answers": ["呢個呀", "ni1 go3 aa3", "ni go aa"],
    },
    "cantonese_no_ice": {
        "spoken_characters": "走冰呀",
        "spoken_romanization": "zau2 bing1 aa3",
        "voice_answers": ["走冰呀", "zau2 bing1 aa3", "zau bing aa"],
    },
    "cantonese_less_sugar": {
        "spoken_characters": "少甜呀",
        "spoken_romanization": "siu2 tim4 aa3",
        "voice_answers": ["少甜呀", "siu2 tim4 aa3", "siu tim aa"],
    },
    "cantonese_takeaway": {
        "spoken_characters": "外賣呀",
        "spoken_romanization": "ngoi6 maai6 aa3",
        "voice_answers": ["外賣呀", "ngoi6 maai6 aa3", "ngoi maai aa"],
    },
    "cantonese_numbers_1_to_10": {
        "spoken_characters": "一二三四五六七八九十",
        "spoken_romanization": "jat1 ji6 saam1 sei3 ng5 luk6 cat1 baat3 gau2 sap6",
        "voice_answers": [
            "一二三四五六七八九十",
            "jat1 ji6 saam1 sei3 ng5 luk6 cat1 baat3 gau2 sap6",
            "jat ji saam sei ng luk cat baat gau sap",
        ],
    },
    "cantonese_really": {
        "spoken_characters": "真係呀？",
        "spoken_romanization": "zan1 hai6 aa3",
        "voice_answers": ["真係呀", "真係呀？", "zan1 hai6 aa3", "zan hai aa"],
    },
    "cantonese_okay": {
        "spoken_characters": "好呀",
        "spoken_romanization": "hou2 aa3",
        "voice_answers": ["好呀", "hou2 aa3", "hou aa"],
    },
    "cantonese_one_moment": {
        "spoken_characters": "等陣呀",
        "spoken_romanization": "dang2 zan6 aa3",
        "voice_answers": ["等陣呀", "dang2 zan6 aa3", "dang zan aa"],
    },
    "cantonese_goodbye": {
        "spoken_characters": "再見啦",
        "spoken_romanization": "zoi6 gin3 laa1",
        "voice_answers": ["再見啦", "zoi6 gin3 laa1", "zoi gin laa"],
    },
}


def _spoken_forms(topic: str, romanization: str, characters: str, english: str) -> dict[str, object]:
    override = VOICE_PRACTICE_OVERRIDES.get(topic, {})
    spoken_characters = str(override.get("spoken_characters") or characters or "").strip()
    spoken_romanization = str(override.get("spoken_romanization") or romanization or "").strip()
    spoken_english = str(override.get("spoken_english") or english or "").strip()
    voice_answers = [str(x).strip() for x in override.get("voice_answers", []) if str(x).strip()]
    return {
        "spoken_characters": spoken_characters,
        "spoken_romanization": spoken_romanization,
        "spoken_english": spoken_english,
        "voice_answers": voice_answers,
        "voice_note": (
            "For voice practice, the tutor uses a slightly fuller spoken line so the mic has more to catch."
            if override
            else ""
        ),
    }


def _target_bundle(topic: str) -> dict[str, str]:
    entry = CONTENT_BANK[topic]
    answers = [str(x) for x in entry.get("answers", [])]
    romanization = next((x for x in answers if x.isascii()), "")
    characters = next((x for x in answers if _is_written_form(x)), "")
    question = str(entry.get("question", ""))
    spoken = _spoken_forms(topic, romanization, characters, _extract_english_gloss(question, topic))
    quick_replies: list[str] = []
    for candidate in (
        spoken["spoken_characters"],
        characters,
        spoken["spoken_romanization"],
        romanization,
    ):
        if candidate and candidate not in quick_replies:
            quick_replies.append(candidate)
    is_short = _is_short_target(romanization, characters)
    voice_note = str(spoken["voice_note"]).strip()
    support_tip = (
        "Short target: browser speech recognition may miss very short answers. "
        "You can tap a quick reply or type the line if the mic misses you. "
        "Teacher audio reads the Cantonese characters; Jyutping is for your eyes."
        if is_short
        else (
            "You can speak naturally, or type the line if the microphone misses part of it. "
            "Teacher audio reads the Cantonese characters; Jyutping is for your eyes."
        )
    )
    return {
        "english": _extract_english_gloss(question, topic),
        "romanization": romanization,
        "characters": characters,
        "category": topic_category(topic),
        "label": _topic_title(topic),
        "is_short": is_short,
        "support_tip": f"{support_tip} {voice_note}".strip(),
        "quick_replies": quick_replies,
        "spoken_characters": str(spoken["spoken_characters"]),
        "spoken_romanization": str(spoken["spoken_romanization"]),
        "spoken_english": str(spoken["spoken_english"]),
        "voice_answers": list(spoken["voice_answers"]),
    }


def _stage_display(stage: str) -> str:
    labels = {
        "intro": "Teacher demo",
        "guided": "Teacher demo + your reply",
        "roleplay": "Open conversation",
    }
    return labels.get(stage, stage.replace("_", " ").title())


def _advance_label(stage: str) -> str:
    if stage == "roleplay":
        return "Give Me Another Example"
    return "Show Demo Again"


def _topic_frame(topic: str, target: dict[str, str]) -> dict[str, str]:
    english = target["spoken_english"] or target["english"]
    spoken = (
        target["spoken_characters"]
        or target["characters"]
        or target["spoken_romanization"]
        or target["romanization"]
        or target["label"]
    )
    default = {
        "setup": f"We are working on a natural way to say {english}.",
        "demo_me": f"Me: {spoken}",
        "demo_you": f"You can answer with the same line, or stay close to it.",
        "guided_prompt": f"Now say {english} to me in Cantonese.",
        "roleplay_prompt": "Nice. Now say it again like you are talking to a real person, not reading a prompt.",
    }
    frames = {
        "cantonese_greetings": {
            "setup": "This is a friendly, neutral way to greet someone.",
            "demo_you": f"You can answer me with the same line: {spoken}",
            "guided_prompt": "I walk up to you and smile. Greet me in Cantonese.",
            "roleplay_prompt": "Nice. Now greet me once more like you have just seen me in real life.",
        },
        "cantonese_how_are_you": {
            "setup": "This is how you ask someone how they are doing.",
            "demo_you": "You can ask me the same question back.",
            "guided_prompt": "We have already said hello. Ask me how I am in Cantonese.",
            "roleplay_prompt": "Good. Ask it again like you genuinely want to know how I am.",
        },
        "cantonese_thank_you": {
            "setup": "Use this when someone helps you or gives you something.",
            "demo_you": f"If I hand you something, you can say: {spoken}",
            "guided_prompt": "I just handed you your drink. What do you say to me?",
            "roleplay_prompt": "Good. Say thank you again like I really helped you just now.",
        },
        "cantonese_please": {
            "setup": "This helps you begin a polite request.",
            "demo_you": f"You can start politely with: {spoken}",
            "guided_prompt": "You want to ask me for help politely. What would you say first?",
            "roleplay_prompt": "Nice. Say it once more like you are getting someone's attention politely.",
        },
        "cantonese_excuse_me": {
            "setup": "Use this to get attention politely in a busy place.",
            "demo_you": f"You can say: {spoken}",
            "guided_prompt": "You need to get my attention in a busy place. What do you say?",
            "roleplay_prompt": "Good. Say it again like you really need me to notice you.",
        },
        "cantonese_sorry": {
            "setup": "Use this when you need to apologize clearly.",
            "demo_you": f"You can say: {spoken}",
            "guided_prompt": "You bumped into me by accident. What do you say?",
            "roleplay_prompt": "Good. Now say it again like you are apologizing sincerely.",
        },
        "cantonese_yes": {
            "setup": "This is the short word for agreeing or confirming.",
            "demo_you": f"You can answer with: {spoken}",
            "guided_prompt": "I ask, 'Is that right?' Answer yes in Cantonese.",
            "roleplay_prompt": "Nice. Say yes once more, but make it sound like a real reply.",
        },
        "cantonese_no": {
            "setup": "This is the short way to say no.",
            "demo_you": f"You can answer with: {spoken}",
            "guided_prompt": "I ask, 'Is that yours?' Answer no in Cantonese.",
            "roleplay_prompt": "Nice. Say no once more like you mean it in conversation.",
        },
        "cantonese_i_dont_understand": {
            "setup": "Use this when the other person says something you cannot follow.",
            "demo_you": f"You can repair the conversation with: {spoken}",
            "guided_prompt": "I just explained something too fast. Tell me you do not understand in Cantonese.",
            "roleplay_prompt": "Good. Say it again like you are calmly asking for help.",
        },
        "cantonese_say_again": {
            "setup": "Use this when you need the person to repeat what they said.",
            "demo_you": f"You can ask politely with: {spoken}",
            "guided_prompt": "You did not catch what I said. Ask me to say it again in Cantonese.",
            "roleplay_prompt": "Nice. Ask again like you are speaking to a real person at the counter.",
        },
        "cantonese_speak_slowly": {
            "setup": "Use this when the person is speaking too quickly.",
            "demo_you": f"You can ask them to slow down with: {spoken}",
            "guided_prompt": "I am speaking too fast. Ask me to speak slowly in Cantonese.",
            "roleplay_prompt": "Good. Say it again like you genuinely need the pace to slow down.",
        },
        "cantonese_learning_cantonese": {
            "setup": "Use this to explain why you may need patience or simpler language.",
            "demo_you": f"You can tell someone: {spoken}",
            "guided_prompt": "Tell me that you are learning Cantonese.",
            "roleplay_prompt": "Nice. Say it again like you are introducing yourself to a friendly local speaker.",
        },
        "cantonese_speak_english": {
            "setup": "Use this when you need to check whether English is available.",
            "demo_you": f"You can ask politely: {spoken}",
            "guided_prompt": "You need help and want to know if I speak English. Ask me in Cantonese.",
            "roleplay_prompt": "Good. Ask again like you are in a real travel situation.",
        },
        "cantonese_what": {
            "setup": "Use this when you did not catch what someone said.",
            "demo_you": f"You can ask: {spoken}",
            "guided_prompt": "I just said something unclear. Ask me 'what?' in Cantonese.",
            "roleplay_prompt": "Good. Ask it again like you genuinely need me to repeat myself.",
        },
        "cantonese_where": {
            "setup": "This gives you the key question word for asking where something is.",
            "demo_you": f"You can ask: {spoken}",
            "guided_prompt": "You are trying to find something. Ask me 'where?' in Cantonese.",
            "roleplay_prompt": "Nice. Ask it again like you are in the middle of looking for something.",
        },
        "cantonese_i_need": {
            "setup": "This is a fixed starter you can build longer sentences from later.",
            "demo_you": f"You can begin with: {spoken}",
            "guided_prompt": "Tell me 'I need ...' in Cantonese. It is fine to stop after the fixed part.",
            "roleplay_prompt": "Good. Say it again like you are starting a real request.",
        },
        "cantonese_goodbye": {
            "setup": "Use this when you are leaving or ending the conversation.",
            "demo_you": f"You can say: {spoken}",
            "guided_prompt": "We are about to part ways. What do you say to me?",
            "roleplay_prompt": "Nice. Say goodbye again like you are actually leaving now.",
        },
        "cantonese_where_is_bathroom": {
            "setup": "This full line is useful when you urgently need the bathroom.",
            "demo_you": f"If you need help fast, you can ask: {spoken}",
            "guided_prompt": "You need the bathroom right now. Ask me where it is.",
            "roleplay_prompt": "Good. Ask it again like you are really in that situation.",
        },
        "cantonese_how_much": {
            "setup": "Use this when you want to ask the price.",
            "demo_you": f"You can ask: {spoken}",
            "guided_prompt": "You are in a shop. Ask me how much it is.",
            "roleplay_prompt": "Nice. Ask it again like you are speaking to a shopkeeper.",
        },
        "cantonese_i_want": {
            "setup": "This is a very common starter for saying what you want.",
            "demo_you": f"You can begin with: {spoken}",
            "guided_prompt": "Tell me 'I want ...' in Cantonese. It is fine to stop after the fixed part.",
            "roleplay_prompt": "Good. Say it again like you are making a real request.",
        },
        "cantonese_left": {
            "setup": "Use this when someone asks which side or direction.",
            "demo_you": f"You can point someone left with: {spoken}",
            "guided_prompt": "I ask which way to go. Tell me left in Cantonese.",
            "roleplay_prompt": "Nice. Say it again like you are giving a quick direction.",
        },
        "cantonese_right": {
            "setup": "Use this when someone needs the right side or direction.",
            "demo_you": f"You can point someone right with: {spoken}",
            "guided_prompt": "I ask which way to go. Tell me right in Cantonese.",
            "roleplay_prompt": "Good. Say it again like you are giving a clear direction.",
        },
        "cantonese_straight_ahead": {
            "setup": "Use this when giving simple walking directions.",
            "demo_you": f"You can tell someone to keep going with: {spoken}",
            "guided_prompt": "I am lost and ask where to walk. Tell me to go straight ahead.",
            "roleplay_prompt": "Nice. Say it again like you are helping someone on the street.",
        },
        "cantonese_where_mtr": {
            "setup": "This is useful when you need the train station.",
            "demo_you": f"You can ask for the MTR station with: {spoken}",
            "guided_prompt": "You need to find the MTR station. Ask me where it is.",
            "roleplay_prompt": "Good. Ask again like you are actually trying to catch a train.",
        },
        "cantonese_near_here": {
            "setup": "Use this to check whether a place is close by.",
            "demo_you": f"You can ask: {spoken}",
            "guided_prompt": "You hear about a shop and want to know if it is near here. Ask me.",
            "roleplay_prompt": "Nice. Ask again like you are deciding whether to walk there.",
        },
        "cantonese_how_to_get_to": {
            "setup": "This starter helps you ask for directions to a place.",
            "demo_you": f"You can begin your question with: {spoken}",
            "guided_prompt": "You need directions. Ask 'how do I get to...' in Cantonese.",
            "roleplay_prompt": "Good. Say it again like you are about to add a place name.",
        },
        "cantonese_this_one": {
            "setup": "Use this when pointing to something you want.",
            "demo_you": f"At a counter, you can say: {spoken}",
            "guided_prompt": "You are pointing at an item. Tell me 'this one' in Cantonese.",
            "roleplay_prompt": "Nice. Say it again like you are ordering from a display case.",
        },
        "cantonese_no_ice": {
            "setup": "Use this when ordering a cold drink.",
            "demo_you": f"You can ask for no ice with: {spoken}",
            "guided_prompt": "You are ordering a drink. Ask for no ice in Cantonese.",
            "roleplay_prompt": "Good. Say it again like you are talking to the cashier.",
        },
        "cantonese_less_sugar": {
            "setup": "Use this when customizing a sweet drink.",
            "demo_you": f"You can ask for less sugar with: {spoken}",
            "guided_prompt": "You are ordering milk tea. Ask for less sugar in Cantonese.",
            "roleplay_prompt": "Nice. Say it again like you are making a real drink order.",
        },
        "cantonese_takeaway": {
            "setup": "Use this when you want food or drink to go.",
            "demo_you": f"You can say: {spoken}",
            "guided_prompt": "You want your order to go. Say takeaway in Cantonese.",
            "roleplay_prompt": "Good. Say it again like you are finishing an order.",
        },
        "cantonese_bill_please": {
            "setup": "Use this when you are ready to pay at a restaurant.",
            "demo_you": f"You can ask for the bill with: {spoken}",
            "guided_prompt": "You finished eating. Ask me for the bill in Cantonese.",
            "roleplay_prompt": "Nice. Ask again like you are catching the server's attention.",
        },
        "cantonese_numbers_1_to_10": {
            "setup": "These numbers help with prices, quantities, and table numbers.",
            "demo_you": f"You can count from one to ten like this: {spoken}",
            "guided_prompt": "Count from one to ten in Cantonese.",
            "roleplay_prompt": "Good. Count again a little more naturally, like you are confirming a quantity.",
        },
        "cantonese_too_expensive": {
            "setup": "Use this when a price feels too high.",
            "demo_you": f"You can react with: {spoken}",
            "guided_prompt": "I tell you a high price. Say 'too expensive' in Cantonese.",
            "roleplay_prompt": "Nice. Say it again like you are reacting naturally in a shop.",
        },
        "cantonese_pay_by_card": {
            "setup": "Use this when you want to pay with a card.",
            "demo_you": f"You can tell the cashier: {spoken}",
            "guided_prompt": "You are checking out. Say you will pay by card.",
            "roleplay_prompt": "Good. Say it again like you are at the register.",
        },
        "cantonese_pay_cash": {
            "setup": "Use this when you want to pay with cash.",
            "demo_you": f"You can tell the cashier: {spoken}",
            "guided_prompt": "You are checking out. Say you will pay cash.",
            "roleplay_prompt": "Nice. Say it again like you are choosing how to pay.",
        },
        "cantonese_really": {
            "setup": "Use this to show surprise or check that something is true.",
            "demo_you": f"You can react with: {spoken}",
            "guided_prompt": "I tell you something surprising. Say 'really?' in Cantonese.",
            "roleplay_prompt": "Good. Say it again like you are genuinely surprised.",
        },
        "cantonese_okay": {
            "setup": "Use this as a simple agreeable reply.",
            "demo_you": f"You can answer with: {spoken}",
            "guided_prompt": "I suggest a plan. Say okay in Cantonese.",
            "roleplay_prompt": "Nice. Say it again like a natural quick reply.",
        },
        "cantonese_no_problem": {
            "setup": "Use this to reassure someone or accept a small request.",
            "demo_you": f"You can say: {spoken}",
            "guided_prompt": "I ask if something is okay. Tell me no problem in Cantonese.",
            "roleplay_prompt": "Good. Say it again like you are being friendly and easygoing.",
        },
        "cantonese_one_moment": {
            "setup": "Use this when you need a little time.",
            "demo_you": f"You can ask for a pause with: {spoken}",
            "guided_prompt": "You need a moment before answering. Say one moment in Cantonese.",
            "roleplay_prompt": "Nice. Say it again like you are politely buying time.",
        },
        "cantonese_what_does_this_mean": {
            "setup": "Use this when you see or hear something you do not understand.",
            "demo_you": f"You can ask: {spoken}",
            "guided_prompt": "You see a sign and do not understand it. Ask what this means.",
            "roleplay_prompt": "Good. Ask again like you are showing me something on your phone.",
        },
        "cantonese_cafe_order": {
            "setup": "This is a simple cafe order you can use right away.",
            "demo_you": f"At the counter, you can say: {spoken}",
            "guided_prompt": "You are at the cafe counter. Order a cup of coffee from me in Cantonese.",
            "roleplay_prompt": "Nice. Order it again like you are speaking to the cashier for real.",
        },
    }
    return {**default, **frames.get(topic, {})}


def _coach_note(grammar_message: str, feedback: str, target: dict[str, str]) -> str:
    notes: list[str] = []
    grammar_text = grammar_message.strip()
    feedback_text = feedback.strip()
    lower_grammar = grammar_text.lower()
    if grammar_text:
        if "did not catch a usable spoken answer" in lower_grammar:
            notes.append("I did not catch a clear Cantonese line that time.")
        elif lower_grammar.startswith("target line:"):
            line = target["characters"] or target["romanization"] or target["label"]
            notes.append(f"The line we are aiming for here is {line}.")
        elif "short target detected" not in lower_grammar and "matched the target line" not in lower_grammar:
            notes.append(grammar_text)
    if feedback_text and feedback_text not in notes:
        notes.append(feedback_text)
    return " ".join(notes).strip()


def _success_note(grammar_message: str, feedback: str, target: dict[str, str]) -> str:
    feedback_text = feedback.strip()
    lower_grammar = grammar_message.strip().lower()
    if feedback_text:
        return feedback_text
    if "close spoken match" in lower_grammar:
        return "Nice. I could still understand that as the target line."
    if "matched the target line" in lower_grammar or "short target detected" in lower_grammar:
        return f"Nice. That sounded right for {target['english']}."
    return "Nice. That works."


def _speech_segment(text: str, lang: str, *, rate: float = 1.0) -> dict[str, object]:
    return {"text": text, "lang": lang, "rate": rate}


def _model_speech_segments(
    target: dict[str, str],
    intro_english: str,
    prompt_english: str,
    *,
    include_meaning: bool = True,
) -> list[dict[str, object]]:
    segments: list[dict[str, object]] = []
    if intro_english.strip():
        segments.append(_speech_segment(intro_english.strip(), "en-US"))
    characters = str(target.get("spoken_characters") or target.get("characters") or "").strip()
    if characters:
        base_rate = 0.82 if target["is_short"] else 0.9
        repeat_rate = 0.74 if target["is_short"] else 0.82
        segments.append(_speech_segment(characters, "zh-HK", rate=base_rate))
        segments.append(_speech_segment(characters, "zh-HK", rate=repeat_rate))
    elif str(target.get("spoken_romanization") or target.get("romanization") or "").strip():
        segments.append(
            _speech_segment(
                "The Cantonese model is shown on screen in Jyutping.",
                "en-US",
            )
        )
    meaning = str(target.get("spoken_english") or target.get("english") or "").strip()
    if include_meaning and meaning:
        segments.append(
            _speech_segment(f"It means {meaning}.", "en-US", rate=0.98)
        )
    if prompt_english.strip():
        segments.append(_speech_segment(prompt_english.strip(), "en-US"))
    return segments


def _english_speech_segments(*parts: str) -> list[dict[str, object]]:
    return [
        _speech_segment(part.strip(), "en-US")
        for part in parts
        if part and part.strip()
    ]


def _spoken_prompt_for_stage(topic: str, stage: str) -> tuple[str, str]:
    target = _target_bundle(topic)
    frame = _topic_frame(topic, target)
    if stage == "roleplay":
        return frame["roleplay_prompt"], frame["roleplay_prompt"]
    return frame["guided_prompt"], frame["guided_prompt"]


def _warm_intro_text(
    topic: str,
    action: str,
    base_explanation: str,
    target: dict[str, str],
) -> tuple[str, str, list[dict[str, object]]]:
    line = (
        target["spoken_characters"]
        or target["characters"]
        or target["spoken_romanization"]
        or target["romanization"]
        or target["label"]
    )
    roman = target["spoken_romanization"] or target["romanization"]
    english = target["spoken_english"] or target["english"]
    core_line = target["characters"] or target["romanization"] or target["label"]
    prompt_text, prompt_speech = _spoken_prompt_for_stage(topic, "guided")
    frame = _topic_frame(topic, target)
    prefix = {
        "review": "Let's revisit this like a real conversation, not a worksheet.",
        "practice": "Let's turn this into a short real exchange.",
        "explain": "Let's learn this like a real tutor would: I go first, then you answer me.",
    }.get(action, "Let's work on this together like a real conversation.")
    display = (
        f"[Speaking Lesson] {target['label']}\n"
        f"{prefix}\n\n"
        f"Teaching note:\n{base_explanation}\n\n"
        f"How I'd say it:\n{line}\n"
        f"Jyutping: {roman or '-'}\n"
        f"Meaning: {english}\n"
        f"Core target: {core_line}\n"
        f"Support: {target['support_tip']}\n\n"
        f"Mini demo:\n"
        f"{frame['setup']}\n"
        f"{frame['demo_me']}\n"
        f"{frame['demo_you']}\n\n"
        f"My turn to you:\n{prompt_text}\n"
        f"Reply in Cantonese however you can. If you want the demo again, just say 'repeat again'."
    )
    speech = f"{prefix} Listen to my Cantonese model on screen."
    speech_segments = _model_speech_segments(
        target,
        f"{prefix} {frame['setup']} Listen to my Cantonese model.",
        prompt_speech,
    )
    return display, speech, speech_segments


@dataclass
class ActiveLesson:
    topic: str
    action: str
    stage: str = "guided"
    attempts_in_stage: int = 0
    total_attempts: int = 0
    successes: int = 0
    completed: bool = False
    completion_reason: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "topic": self.topic,
            "action": self.action,
            "stage": self.stage,
            "stage_label": _stage_display(self.stage),
            "attempts_in_stage": self.attempts_in_stage,
            "total_attempts": self.total_attempts,
            "successes": self.successes,
            "completed": self.completed,
            "completion_reason": self.completion_reason,
            "target": _target_bundle(self.topic),
            "can_advance": not self.completed,
            "advance_label": _advance_label(self.stage),
        }


@dataclass
class VoiceTutorSession:
    session_id: str
    learner: LearnerModel
    memory: Memory
    planner: Planner = field(default_factory=Planner)
    transcript: list[dict[str, str]] = field(default_factory=list)
    active_lesson: ActiveLesson | None = None

    def _append_teacher(
        self,
        text: str,
        speech: str,
        *,
        kind: str = "teacher",
        speech_segments: list[dict[str, object]] | None = None,
    ) -> dict[str, object]:
        message: dict[str, object] = {"role": kind, "text": text, "speech": speech}
        if speech_segments:
            message["speech_segments"] = speech_segments
        self.transcript.append(message)
        return message

    def _append_learner(self, text: str) -> None:
        self.transcript.append({"role": "learner", "text": text, "speech": text})

    def _remember_instruction(self, topic: str, text: str) -> None:
        self.memory.remember({"type": "instruction", "topic": topic, "content": text})

    def _save(self) -> None:
        save_session_state(self.learner, self.memory)

    def _requeue_topic_to_end(self, topic: str) -> None:
        if topic in self.learner.review_queue and len(self.learner.review_queue) > 1:
            self.learner.review_queue = [
                item for item in self.learner.review_queue if item != topic
            ] + [topic]

    def _session_state(self) -> dict[str, object]:
        snapshot = self.learner.snapshot()
        return {
            "session_id": self.session_id,
            "runtime_mode": describe_runtime_mode(),
            "focus": focus_summary(self.learner),
            "messages": self.transcript[-20:],
            "awaiting_next_lesson": bool(
                self.active_lesson is not None and self.active_lesson.completed
            ),
            "lesson": self.active_lesson.to_dict() if self.active_lesson else None,
            "learner": {
                "name": self.learner.name,
                "confidence": snapshot["confidence"],
                "review_queue": list(snapshot["review_queue"]),
                "weak_grammar_points": list(snapshot["weak_grammar_points"]),
                "mastery_by_topic": dict(snapshot["mastery_by_topic"]),
            },
        }

    def _build_intro_turn(
        self,
        lesson: ActiveLesson,
    ) -> tuple[str, str, list[dict[str, object]]]:
        learner_snapshot = self.learner.snapshot()
        recent_events = self.memory.recent_events(5)
        target = _target_bundle(lesson.topic)

        if lesson.action == "review":
            recap = review_topic_intro(
                lesson.topic,
                self.learner,
                self.memory,
                learner_snapshot,
                recent_events,
            )
            return _warm_intro_text(lesson.topic, lesson.action, recap, target)

        explanation = generate_explanation(
            lesson.topic,
            str(CONTENT_BANK[lesson.topic]["explanation"]),
            learner_snapshot,
            recent_events,
        )
        return _warm_intro_text(lesson.topic, lesson.action, explanation, target)

    def _repeat_current_demo(self) -> dict[str, object]:
        if self.active_lesson is None:
            return self.start_next_lesson()

        target = _target_bundle(self.active_lesson.topic)
        frame = _topic_frame(self.active_lesson.topic, target)
        model_line = (
            target["spoken_characters"]
            or target["characters"]
            or target["spoken_romanization"]
            or target["romanization"]
            or target["label"]
        )
        core_line = target["characters"] or target["romanization"] or target["label"]
        prompt_text, prompt_speech = _spoken_prompt_for_stage(
            self.active_lesson.topic,
            self.active_lesson.stage,
        )
        display = (
            f"Sure, let me model it once more.\n\n"
            f"How I'd say it:\n{model_line}\n"
            f"Jyutping: {target['spoken_romanization'] or target['romanization'] or '-'}\n"
            f"Meaning: {target['spoken_english'] or target['english']}\n"
            f"Core target: {core_line}\n\n"
            f"Mini demo:\n"
            f"{frame['setup']}\n"
            f"{frame['demo_me']}\n"
            f"{frame['demo_you']}\n\n"
            f"My turn to you:\n{prompt_text}"
        )
        speech = "Sure. Listen to my Cantonese model again."
        speech_segments = _model_speech_segments(
            target,
            "Sure. Listen to my Cantonese model again.",
            prompt_speech,
        )
        self._append_teacher(display, speech, speech_segments=speech_segments)
        self._save()
        return self._session_state()

    def _move_to_next_lesson(self, *, spoken_request: bool) -> dict[str, object]:
        if self.active_lesson is not None and not self.active_lesson.completed:
            topic = self.active_lesson.topic
            update_review_status(self.learner, self.memory, topic)
            self._requeue_topic_to_end(topic)
            self.memory.mark_task_completed(f"skip:{topic}")
            if spoken_request:
                self._append_teacher(
                    "Okay, let's move on. I will keep this line in review and bring in the next one.",
                    "Okay, let's move on. I will keep this line in review and bring in the next one.",
                    speech_segments=_english_speech_segments(
                        "Okay, let's move on.",
                        "I will keep this line in review and bring in the next one.",
                    ),
                )
        elif spoken_request:
            self._append_teacher(
                "Okay, let's move on to the next one.",
                "Okay, let's move on to the next one.",
                speech_segments=_english_speech_segments(
                    "Okay, let's move on to the next one."
                ),
            )

        self.active_lesson = None
        self._save()
        return self.start_next_lesson()

    def advance_lesson(self) -> dict[str, object]:
        return self._repeat_current_demo()

    def start_next_lesson(self) -> dict[str, object]:
        if self.active_lesson is not None and not self.active_lesson.completed:
            return self._session_state()

        plan = self.planner.choose_plan(self.learner, self.memory)
        self.active_lesson = ActiveLesson(topic=plan.topic, action=plan.action)
        display, speech, speech_segments = self._build_intro_turn(self.active_lesson)
        self._append_teacher(display, speech, speech_segments=speech_segments)
        self._remember_instruction(plan.topic, display)
        self._save()
        return self._session_state()

    def _finalize_lesson(self, *, success: bool, closing_note: str) -> dict[str, object]:
        if self.active_lesson is None:
            return self._session_state()

        topic = self.active_lesson.topic
        queue_status = update_review_status(self.learner, self.memory, topic)
        if not success:
            self._requeue_topic_to_end(topic)

        self.memory.mark_task_completed(f"{self.active_lesson.action}:{topic}")
        target = _target_bundle(topic)
        if success:
            display = (
                f"{closing_note}\n\n"
                f"{queue_status}\n"
                f"Say 'next lesson' when you want the next speaking turn."
            )
            speech = "Nice work. Say next lesson when you're ready for the next speaking turn."
            speech_segments = _english_speech_segments(
                closing_note,
                "Say next lesson when you're ready for the next speaking turn.",
            )
            reason = "mastered_current_round"
        else:
            line = (
                target["spoken_characters"]
                or target["characters"]
                or target["spoken_romanization"]
                or target["romanization"]
                or target["label"]
            )
            display = (
                f"{closing_note}\n\n"
                f"We will keep this in review.\n"
                f"Target line: {line}\n"
                f"{queue_status}\n"
                f"Say 'next lesson' when you're ready to continue."
            )
            speech = (
                "We will keep this in review. Say next lesson when you're ready to continue."
            )
            speech_segments = _model_speech_segments(
                target,
                "We will keep this in review.",
                "Say next lesson when you're ready to continue.",
                include_meaning=False,
            )
            reason = "needs_review"

        self.active_lesson.completed = True
        self.active_lesson.completion_reason = reason
        self._append_teacher(display, speech, speech_segments=speech_segments)
        self._save()
        return self._session_state()

    def process_learner_turn(
        self,
        learner_text: str,
        alternatives: list[str] | None = None,
    ) -> dict[str, object]:
        clean_text = learner_text.strip()
        if not clean_text:
            self._append_teacher(
                "I did not hear anything usable yet. Try speaking again, or type your line.",
                "I did not hear anything usable yet. Try speaking again.",
            )
            return self._session_state()

        if self.active_lesson is None:
            return self.start_next_lesson()
        selected_text, command = _pick_best_candidate(
            self.active_lesson.topic if self.active_lesson else None,
            clean_text,
            alternatives,
        )
        if command == "repeat":
            self._append_learner(clean_text)
            return self._repeat_current_demo()
        if command == "next":
            self._append_learner(clean_text)
            return self._move_to_next_lesson(spoken_request=True)
        if self.active_lesson.completed:
            self._append_teacher(
                "That round is complete. Say 'next lesson' to move on, or say 'repeat again' if you want the model one more time.",
                "That round is complete. Say next lesson to move on, or say repeat again if you want the model one more time.",
                speech_segments=_english_speech_segments(
                    "That round is complete.",
                    "Say next lesson to move on, or say repeat again if you want the model one more time.",
                ),
            )
            return self._session_state()

        topic = self.active_lesson.topic
        if self.active_lesson.stage == "intro":
            self.active_lesson.stage = "guided"
            self.active_lesson.attempts_in_stage = 0
        self._append_learner(clean_text)

        learner_snapshot = self.learner.snapshot()
        recent_events = self.memory.recent_events(5)
        grammar_result = _spoken_checker(topic, selected_text)
        expected_answers = [str(x) for x in CONTENT_BANK[topic].get("answers", [])]
        expected_answers.extend(str(x) for x in _target_bundle(topic).get("voice_answers", []))
        evaluation = evaluate_answer(
            topic,
            selected_text,
            expected_answers,
            grammar_result,
            learner_snapshot,
            recent_events,
        )
        is_correct = bool(evaluation["correct"])
        grammar_message = str(evaluation["grammar_message"])
        feedback = str(evaluation["feedback"])

        self.learner.record_result(topic, is_correct)
        self.memory.update_topic_result(topic, is_correct)
        if is_correct:
            self.learner.add_vocabulary_item(selected_text)

        self.memory.remember(
            {
                "type": "practice_attempt",
                "topic": topic,
                "answer": selected_text,
                "correct": is_correct,
                "planner_action": self.active_lesson.action,
            }
        )

        self.active_lesson.total_attempts += 1
        self.active_lesson.attempts_in_stage += 1

        if is_correct:
            self.active_lesson.successes += 1
            if self.active_lesson.stage == "guided":
                self.active_lesson.stage = "roleplay"
                self.active_lesson.attempts_in_stage = 0
                target = _target_bundle(topic)
                frame = _topic_frame(topic, target)
                success_note = _success_note(grammar_message, feedback, target)
                _, prompt_speech = _spoken_prompt_for_stage(topic, "roleplay")
                display = (
                    f"{success_note}\n\n"
                    f"That works. You have the core line.\n"
                    f"If I say it naturally, it sounds like this: {target['spoken_characters'] or target['characters'] or target['spoken_romanization'] or target['romanization'] or target['label']}\n"
                    f"{frame['roleplay_prompt']}"
                )
                speech = (
                    f"{success_note} Good. Now keep the conversation going."
                )
                self._append_teacher(
                    display,
                    speech,
                    speech_segments=_model_speech_segments(
                        target,
                        f"{success_note} Good. Now keep the conversation going.",
                        prompt_speech,
                        include_meaning=False,
                    ),
                )
                self._save()
                return self._session_state()

            target = _target_bundle(topic)
            return self._finalize_lesson(
                success=True,
                closing_note=_success_note(grammar_message, feedback, target),
            )

        target = _target_bundle(topic)
        model_line = (
            target["spoken_characters"]
            or target["characters"]
            or target["spoken_romanization"]
            or target["romanization"]
            or target["label"]
        )
        core_line = target["characters"] or target["romanization"] or target["label"]
        coaching_note = _coach_note(grammar_message, feedback, target)
        if self.active_lesson.attempts_in_stage >= 3:
            return self._finalize_lesson(
                success=False,
                closing_note=(
                    f"{coaching_note}\n"
                    f"Let's park this one for now, but keep the model line in your ear: {model_line}."
                ),
            )

        prompt_text, prompt_speech = _spoken_prompt_for_stage(topic, self.active_lesson.stage)
        frame = _topic_frame(topic, target)
        display = (
            f"{coaching_note}\n\n"
            f"Let me model it once more.\n"
            f"How I'd say it:\n{model_line}\n"
            f"Jyutping: {target['spoken_romanization'] or target['romanization'] or '-'}\n"
            f"Meaning: {target['spoken_english'] or target['english']}\n"
            f"Core target: {core_line}\n\n"
            f"Mini demo:\n"
            f"{frame['demo_me']}\n"
            f"{frame['demo_you']}\n\n"
            f"Your turn:\n{prompt_text}"
        )
        speech = "Let me model it once more."
        self._append_teacher(
            display,
            speech,
            speech_segments=_model_speech_segments(
                target,
                f"{coaching_note} Let me model it once more.",
                prompt_speech,
                include_meaning=False,
            ),
        )
        self._save()
        return self._session_state()

    def update_focus(self, mode: str, custom_topics: str | list[str] | None) -> dict[str, object]:
        normalized = (mode or "balanced").strip().lower()
        if normalized not in VALID_FOCUS_MODES:
            normalized = "balanced"
        self.learner.learning_focus = normalized
        if normalized == "custom":
            self.learner.custom_focus_topics = _parse_custom_topics(custom_topics)
        else:
            self.learner.custom_focus_topics = []

        self.active_lesson = None
        summary = focus_summary(self.learner)
        self._append_teacher(
            f"Focus updated. We will study with: {summary}.",
            f"Focus updated. We will study with {summary}.",
            kind="system",
        )
        self._save()
        return self.start_next_lesson()


class VoiceTutorSessionManager:
    def __init__(self) -> None:
        self._sessions: dict[str, VoiceTutorSession] = {}
        self._lock = Lock()

    def config_payload(self) -> dict[str, object]:
        return {
            "runtime_mode": describe_runtime_mode(),
            "topics": list_topics(),
            "focus_modes": list(VALID_FOCUS_MODES),
            "speech_locales": [
                {"label": "Cantonese (Hong Kong)", "value": "zh-HK"},
                {"label": "English", "value": "en-US"},
            ],
        }

    def start_session(
        self,
        *,
        learner_name: str,
        focus_mode: str,
        custom_topics: str | list[str] | None = None,
    ) -> dict[str, object]:
        learner, memory = load_session_state(learner_name) or (
            LearnerModel(name=learner_name),
            Memory(),
        )
        session_id = secrets.token_urlsafe(12)
        session = VoiceTutorSession(session_id=session_id, learner=learner, memory=memory)
        session.update_focus(focus_mode, custom_topics)
        with self._lock:
            self._sessions[session_id] = session
        return session._session_state()

    def _get(self, session_id: str) -> VoiceTutorSession:
        with self._lock:
            session = self._sessions.get(session_id)
        if session is None:
            raise KeyError("Unknown session id")
        return session

    def respond(
        self,
        session_id: str,
        learner_text: str,
        alternatives: list[str] | None = None,
    ) -> dict[str, object]:
        return self._get(session_id).process_learner_turn(learner_text, alternatives)

    def advance(self, session_id: str) -> dict[str, object]:
        return self._get(session_id).advance_lesson()

    def next_lesson(self, session_id: str) -> dict[str, object]:
        return self._get(session_id)._move_to_next_lesson(spoken_request=False)

    def update_focus(
        self,
        session_id: str,
        *,
        focus_mode: str,
        custom_topics: str | list[str] | None = None,
    ) -> dict[str, object]:
        return self._get(session_id).update_focus(focus_mode, custom_topics)
