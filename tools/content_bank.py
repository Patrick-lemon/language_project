"""
Minimal practice items for Cantonese (taught to English speakers).

Each topic provides:
- explanation (ground truth teaching note)
- question (what we prompt the learner for)
- answers (acceptable learner inputs: Jyutping/romanization and/or Traditional characters)
"""

# Minimum mastery on each prerequisite before scenario topics can be selected by the planner.
SCENARIO_PREREQUISITE_MASTERY = 0.55

CONTENT_BANK: dict[str, dict[str, object]] = {
    "cantonese_greetings": {
        "category": "survival",
        "explanation": (
            "A common neutral Cantonese greeting is '你好' (nei5 hou2). "
            "Use it when you want a friendly, general hello."
        ),
        "question": (
            "Practice: Type the Cantonese greeting for 'Hello'. "
            "You can answer with Jyutping (e.g., nei5 hou2) or Traditional characters (你好)."
        ),
        "answers": [
            "nei5 hou2",
            "neih hou2",
            "nei hou2",
            "你好",
        ],
    },
    "cantonese_how_are_you": {
        "category": "survival",
        "explanation": (
            "To ask 'How are you?' in a neutral way, you can say '你好嗎' (nei5 hou2 maa3). "
            "It’s essentially 'Hello, are you well?'"
        ),
        "question": (
            "Practice: Type 'How are you?' in Cantonese. "
            "Answer with Jyutping (nei5 hou2 maa3) or Traditional characters (你好嗎)."
        ),
        "answers": [
            "nei5 hou2 maa3",
            "neih hou2 maa3",
            "nei hou2 maa3",
            "你好嗎",
        ],
    },
    "cantonese_thank_you": {
        "category": "survival",
        "explanation": (
            "A standard way to say 'Thank you' is '多謝' (do1 ze6). "
            "It works well in everyday polite conversation."
        ),
        "question": (
            "Practice: Type 'Thank you' in Cantonese. "
            "Answer with Jyutping (do1 ze6) or Traditional characters (多謝)."
        ),
        "answers": [
            "do1 ze6",
            "do ze6",
            "多謝",
        ],
    },
    "cantonese_please": {
        "category": "survival",
        "explanation": (
            "A polite word 'please' in Cantonese is '請' (cing2). "
            "It’s commonly used in everyday requests."
        ),
        "question": (
            "Practice: Type 'please' in Cantonese. "
            "Answer with Jyutping (cing2) or Traditional characters (請)."
        ),
        "answers": ["cing2", "請"],
    },
    "cantonese_excuse_me": {
        "category": "survival",
        "explanation": (
            "A common 'excuse me' / 'sorry' style phrase is '唔該' (m4 goi1). "
            "It’s used to get attention politely."
        ),
        "question": (
            "Practice: Type 'excuse me' in Cantonese. "
            "Answer with Jyutping (m4 goi1) or Traditional characters (唔該)."
        ),
        "answers": ["m4 goi1", "m4goi1", "唔該"],
    },
    "cantonese_sorry": {
        "category": "survival",
        "explanation": (
            "A standard 'sorry / excuse me' is '對唔住' (deoi3 m4 zyu6). "
            "It’s more explicitly apologizing."
        ),
        "question": (
            "Practice: Type 'sorry' in Cantonese. "
            "Answer with Jyutping (deoi3 m4 zyu6) or Traditional characters (對唔住)."
        ),
        "answers": ["deoi3 m4 zyu6", "deoi3m4zyu6", "對唔住"],
    },
    "cantonese_yes": {
        "category": "survival",
        "explanation": "The Cantonese word for 'yes' is '係' (hai6).",
        "question": "Practice: Type the Cantonese word for 'Yes'. (係)",
        "answers": ["hai6", "係"],
    },
    "cantonese_no": {
        "category": "survival",
        "explanation": "The Cantonese word for 'no' is '唔係' (m4 hai6).",
        "question": "Practice: Type the Cantonese word for 'No'. (唔係)",
        "answers": ["m4 hai6", "m4hai6", "唔係"],
    },
    "cantonese_what": {
        "category": "question",
        "explanation": (
            "Cantonese 'what?' can be '咩' (me1) or more specifically '咩嘢' (me1 je5)."
        ),
        "question": "Practice: Type 'what?' in Cantonese. (咩 or 咩嘢)",
        "answers": ["me1", "咩", "me1 je5", "me1je5", "咩嘢"],
    },
    "cantonese_where": {
        "category": "question",
        "explanation": "Cantonese 'where?' is '邊度' (bin1 dou6).",
        "question": "Practice: Type 'where?' in Cantonese. (邊度)",
        "answers": ["bin1 dou6", "bin1dou6", "邊度"],
    },
    "cantonese_i_need": {
        "category": "survival",
        "explanation": (
            "A useful phrase 'I need ...' is '我需要 ...' (ngo5 seoi1 jiu3 ...). "
            "For this exercise we practice the fixed prefix."
        ),
        "question": (
            "Practice: Type the Cantonese prefix for 'I need'. "
            "Answer with Jyutping (ngo5 seoi1 jiu3) or Traditional characters (我需要)."
        ),
        "answers": ["ngo5 seoi1 jiu3", "ngo5seoi1jiu3", "我需要"],
    },
    "cantonese_goodbye": {
        "category": "survival",
        "explanation": (
            "A common way to say goodbye is '再見' (zoi6 gin3)."
        ),
        "question": "Practice: Type 'goodbye' in Cantonese. (再見)",
        "answers": ["zoi6 gin3", "zoi6gin3", "再見"],
    },

    "cantonese_where_is_bathroom": {
        "category": "scenario",
        "prerequisites": [
            "cantonese_where",
            "cantonese_i_need",
        ],
        "explanation": (
            "To ask where the bathroom is, a natural pattern is '洗手間係邊度' "
            "(sai2 sau2 gaan1 hai6 bin1 dou6)."
        ),
        "question": (
            "Scenario: You need the bathroom. Type 'Where is the bathroom?' in Cantonese. "
            "Answer with Jyutping or Traditional characters."
        ),
        "answers": [
            "sai2 sau2 gaan1 hai6 bin1 dou6",
            "sai2 sau2 gaan1 hai6 bindou6",
            "sai2 sau2 gaan1 bin1 dou6",
            "洗手間係邊度",
            "洗手間喺邊度",
        ],
    },
    "cantonese_how_much": {
        "category": "question",
        "explanation": (
            "To ask the price, '幾多錢' (gei2 do1 cin2) is a common question."
        ),
        "question": (
            "Question: Type 'How much is it?' in Cantonese. "
            "Answer with Jyutping or Traditional characters."
        ),
        "answers": [
            "gei2 do1 cin2",
            "gei2do1cin2",
            "幾多錢",
        ],
    },
    "cantonese_i_want": {
        "category": "survival",
        "explanation": (
            "A very common way to say 'I want' is '我要' (ngo5 jiu3) or '我想' (ngo5 soeng2)."
        ),
        "question": (
            "Practice: Type 'I want' in Cantonese. "
            "Answer with Jyutping or Traditional characters."
        ),
        "answers": [
            "ngo5 jiu3",
            "ngo5jiu3",
            "我要",
            "ngo5 soeng2",
            "ngo5soeng2",
            "我想",
        ],
    },
    "cantonese_cafe_order": {
        "category": "scenario",
        "prerequisites": [
            "cantonese_i_want",
            "cantonese_thank_you",
        ],
        "explanation": (
            "A simple cafe order pattern: '我要一杯咖啡' (ngo5 jiu3 jat1 bui1 kaa1 fi1)."
        ),
        "question": (
            "Scenario: At a cafe, order 'I want a cup of coffee' in Cantonese. "
            "Answer with Jyutping or Traditional characters."
        ),
        "answers": [
            "ngo5 jiu3 jat1 bui1 kaa1 fei1",
            "ngo5jiu3 jat1bui1 kaa1fei1",
            "我要一杯咖啡",
        ],
    },
}


def list_topics() -> list[str]:
    return list(CONTENT_BANK.keys())


def topic_category(topic: str) -> str:
    entry = CONTENT_BANK.get(topic) or {}
    cat = entry.get("category")
    return str(cat) if cat is not None else "general"


def topic_prerequisites(topic: str) -> list[str]:
    entry = CONTENT_BANK.get(topic) or {}
    prereqs = entry.get("prerequisites")
    if isinstance(prereqs, list):
        return [str(x) for x in prereqs]
    return []
