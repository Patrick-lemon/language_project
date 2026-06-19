"""
Minimal practice items for Cantonese (taught to English speakers).

Each topic provides:
- explanation (ground truth teaching note)
- question (what we prompt the learner for)
- answers (acceptable learner inputs: Jyutping/romanization and/or Traditional characters)
"""

# Minimum mastery on each prerequisite before scenario topics can be selected by the planner.
SCENARIO_PREREQUISITE_MASTERY = 0.55
PREREQUISITE_MASTERY = 0.55

# Lightweight curriculum metadata used by the planner. Keeping this separate from
# the lesson text makes it easier to tune sequencing without rewriting prompts.
CURRICULUM_METADATA: dict[str, dict[str, object]] = {
    "cantonese_greetings": {"difficulty": 1, "tags": ["basics", "greeting"]},
    "cantonese_how_are_you": {"difficulty": 1, "tags": ["basics", "greeting"]},
    "cantonese_thank_you": {"difficulty": 1, "tags": ["basics", "politeness"]},
    "cantonese_please": {"difficulty": 1, "tags": ["basics", "politeness"]},
    "cantonese_excuse_me": {"difficulty": 1, "tags": ["basics", "politeness"]},
    "cantonese_sorry": {"difficulty": 1, "tags": ["basics", "politeness"]},
    "cantonese_yes": {"difficulty": 1, "tags": ["basics", "conversation_glue"]},
    "cantonese_no": {"difficulty": 1, "tags": ["basics", "conversation_glue"]},
    "cantonese_i_dont_understand": {"difficulty": 1, "tags": ["repair"]},
    "cantonese_say_again": {"difficulty": 2, "tags": ["repair", "politeness"]},
    "cantonese_speak_slowly": {"difficulty": 2, "tags": ["repair"]},
    "cantonese_learning_cantonese": {"difficulty": 3, "tags": ["repair", "identity"]},
    "cantonese_speak_english": {"difficulty": 3, "tags": ["repair", "question"]},
    "cantonese_what": {"difficulty": 1, "tags": ["question", "repair"]},
    "cantonese_where": {"difficulty": 1, "tags": ["question", "directions"]},
    "cantonese_i_need": {"difficulty": 2, "tags": ["request"]},
    "cantonese_goodbye": {"difficulty": 1, "tags": ["basics", "greeting"]},
    "cantonese_where_is_bathroom": {
        "difficulty": 3,
        "tags": ["scenario", "directions", "survival"],
        "prerequisites": ["cantonese_where", "cantonese_i_need"],
    },
    "cantonese_how_much": {"difficulty": 2, "tags": ["shopping", "question"]},
    "cantonese_i_want": {"difficulty": 2, "tags": ["request", "shopping"]},
    "cantonese_left": {"difficulty": 1, "tags": ["directions"]},
    "cantonese_right": {"difficulty": 1, "tags": ["directions"]},
    "cantonese_straight_ahead": {"difficulty": 2, "tags": ["directions"]},
    "cantonese_where_mtr": {
        "difficulty": 3,
        "tags": ["scenario", "directions", "transit"],
        "prerequisites": ["cantonese_where"],
    },
    "cantonese_near_here": {
        "difficulty": 3,
        "tags": ["directions", "question"],
        "prerequisites": ["cantonese_where"],
    },
    "cantonese_how_to_get_to": {
        "difficulty": 3,
        "tags": ["directions", "question"],
        "prerequisites": ["cantonese_where"],
    },
    "cantonese_this_one": {"difficulty": 1, "tags": ["shopping", "cafe"]},
    "cantonese_no_ice": {"difficulty": 1, "tags": ["cafe"]},
    "cantonese_less_sugar": {"difficulty": 1, "tags": ["cafe"]},
    "cantonese_takeaway": {"difficulty": 1, "tags": ["cafe"]},
    "cantonese_bill_please": {
        "difficulty": 2,
        "tags": ["cafe", "payment", "politeness"],
        "prerequisites": ["cantonese_excuse_me"],
    },
    "cantonese_numbers_1_to_10": {"difficulty": 2, "tags": ["numbers", "shopping"]},
    "cantonese_too_expensive": {"difficulty": 2, "tags": ["shopping", "payment"]},
    "cantonese_pay_by_card": {
        "difficulty": 3,
        "tags": ["payment", "shopping"],
        "prerequisites": ["cantonese_i_want"],
    },
    "cantonese_pay_cash": {
        "difficulty": 3,
        "tags": ["payment", "shopping"],
        "prerequisites": ["cantonese_i_want"],
    },
    "cantonese_really": {"difficulty": 1, "tags": ["conversation_glue"]},
    "cantonese_okay": {"difficulty": 1, "tags": ["conversation_glue"]},
    "cantonese_no_problem": {"difficulty": 2, "tags": ["conversation_glue"]},
    "cantonese_one_moment": {"difficulty": 2, "tags": ["conversation_glue"]},
    "cantonese_what_does_this_mean": {
        "difficulty": 3,
        "tags": ["conversation_glue", "question", "repair"],
        "prerequisites": ["cantonese_what", "cantonese_this_one"],
    },
    "cantonese_cafe_order": {
        "difficulty": 3,
        "tags": ["scenario", "cafe", "shopping"],
        "prerequisites": ["cantonese_i_want", "cantonese_thank_you"],
    },
}

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
            "To ask 'How are you?' in a neutral way, you can say '你好嗎？' (nei5 hou2 maa3). "
            "It's essentially 'Hello, are you well?'"
        ),
        "question": (
            "Practice: Type 'How are you?' in Cantonese. "
            "Answer with Jyutping (nei5 hou2 maa3) or Traditional characters (你好嗎？)."
        ),
        "answers": [
            "nei5 hou2 maa3",
            "neih hou2 maa3",
            "nei hou2 maa3",
            "你好嗎？",
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
            "It's commonly used in everyday requests."
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
            "It's used to get attention politely."
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
            "It's more explicitly apologizing."
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
    "cantonese_i_dont_understand": {
        "category": "survival",
        "explanation": (
            "A useful repair phrase is '我唔明' (ngo5 m4 ming4), meaning "
            "'I don't understand.' Use it when you need the other person to clarify."
        ),
        "question": (
            "Practice: Type 'I don't understand' in Cantonese. "
            "Answer with Jyutping (ngo5 m4 ming4) or Traditional characters (我唔明)."
        ),
        "answers": ["ngo5 m4 ming4", "ngo5m4ming4", "我唔明"],
    },
    "cantonese_say_again": {
        "category": "survival",
        "explanation": (
            "To ask someone to repeat something, say '請再講一次' "
            "(cing2 zoi3 gong2 jat1 ci3), meaning 'Please say it again.'"
        ),
        "question": (
            "Practice: Type 'Please say it again' in Cantonese. "
            "Answer with Jyutping or Traditional characters."
        ),
        "answers": [
            "cing2 zoi3 gong2 jat1 ci3",
            "cing2zoi3gong2jat1ci3",
            "請再講一次",
        ],
    },
    "cantonese_speak_slowly": {
        "category": "survival",
        "explanation": (
            "To ask someone to slow down, say '講慢啲' "
            "(gong2 maan6 di1), meaning 'Speak more slowly.'"
        ),
        "question": (
            "Practice: Type 'Speak slowly' in Cantonese. "
            "Answer with Jyutping (gong2 maan6 di1) or Traditional characters (講慢啲)."
        ),
        "answers": ["gong2 maan6 di1", "gong2maan6di1", "講慢啲"],
    },
    "cantonese_learning_cantonese": {
        "category": "survival",
        "explanation": (
            "To say you are learning Cantonese, use '我學緊廣東話' "
            "(ngo5 hok6 gan2 gwong2 dung1 waa2)."
        ),
        "question": (
            "Practice: Type 'I am learning Cantonese' in Cantonese. "
            "Answer with Jyutping or Traditional characters."
        ),
        "answers": [
            "ngo5 hok6 gan2 gwong2 dung1 waa2",
            "ngo5hok6gan2gwong2dung1waa2",
            "我學緊廣東話",
        ],
    },
    "cantonese_speak_english": {
        "category": "survival",
        "explanation": (
            "To ask 'Do you speak English?', say '你識唔識講英文？' "
            "(nei5 sik1 m4 sik1 gong2 jing1 man2)."
        ),
        "question": (
            "Practice: Type 'Do you speak English?' in Cantonese. "
            "Answer with Jyutping or Traditional characters."
        ),
        "answers": [
            "nei5 sik1 m4 sik1 gong2 jing1 man2",
            "nei5sik1m4sik1gong2jing1man2",
            "你識唔識講英文？",
            "你識唔識講英文",
        ],
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
            "A useful phrase 'I need ...' is '我需要...' (ngo5 seoi1 jiu3 ...). "
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
        "explanation": "A common way to say goodbye is '再見' (zoi6 gin3).",
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
            "To ask where the bathroom is, a natural pattern is '洗手間係邊度？' "
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
            "洗手間係邊度？",
            "洗手間係邊度",
        ],
    },
    "cantonese_how_much": {
        "category": "question",
        "explanation": (
            "To ask the price, '幾多錢？' (gei2 do1 cin2) is a common question."
        ),
        "question": (
            "Question: Type 'How much is it?' in Cantonese. "
            "Answer with Jyutping or Traditional characters."
        ),
        "answers": [
            "gei2 do1 cin2",
            "gei2do1cin2",
            "幾多錢？",
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
    "cantonese_left": {
        "category": "survival",
        "explanation": "The direction word 'left' is '左邊' (zo2 bin1).",
        "question": (
            "Practice: Type 'left' in Cantonese. "
            "Answer with Jyutping (zo2 bin1) or Traditional characters (左邊)."
        ),
        "answers": ["zo2 bin1", "zo2bin1", "左邊"],
    },
    "cantonese_right": {
        "category": "survival",
        "explanation": "The direction word 'right' is '右邊' (jau6 bin1).",
        "question": (
            "Practice: Type 'right' in Cantonese. "
            "Answer with Jyutping (jau6 bin1) or Traditional characters (右邊)."
        ),
        "answers": ["jau6 bin1", "jau6bin1", "右邊"],
    },
    "cantonese_straight_ahead": {
        "category": "survival",
        "explanation": "For 'straight ahead,' say '一直行' (jat1 zik6 haang4).",
        "question": (
            "Practice: Type 'go straight ahead' in Cantonese. "
            "Answer with Jyutping or Traditional characters."
        ),
        "answers": [
            "jat1 zik6 haang4",
            "jat1zik6haang4",
            "一直行",
        ],
    },
    "cantonese_where_mtr": {
        "category": "scenario",
        "prerequisites": ["cantonese_where"],
        "explanation": (
            "To ask where the MTR is, say '港鐵站喺邊度？' "
            "(gong2 tit3 zaam6 hai2 bin1 dou6)."
        ),
        "question": (
            "Scenario: Ask 'Where is the MTR station?' in Cantonese. "
            "Answer with Jyutping or Traditional characters."
        ),
        "answers": [
            "gong2 tit3 zaam6 hai2 bin1 dou6",
            "gong2tit3zaam6hai2bin1dou6",
            "港鐵站喺邊度？",
            "港鐵站喺邊度",
        ],
    },
    "cantonese_near_here": {
        "category": "question",
        "explanation": (
            "To ask whether something is nearby, say '近唔近呢度？' "
            "(kan5 m4 kan5 ni1 dou6)."
        ),
        "question": (
            "Practice: Type 'Is it near here?' in Cantonese. "
            "Answer with Jyutping or Traditional characters."
        ),
        "answers": [
            "kan5 m4 kan5 ni1 dou6",
            "kan5m4kan5ni1dou6",
            "近唔近呢度？",
            "近唔近呢度",
        ],
    },
    "cantonese_how_to_get_to": {
        "category": "question",
        "explanation": (
            "To ask how to get somewhere, say '點去...？' "
            "(dim2 heoi3 ...), with the place after it."
        ),
        "question": (
            "Practice: Type the Cantonese starter for 'How do I get to ...?' "
            "Answer with Jyutping (dim2 heoi3) or Traditional characters (點去)."
        ),
        "answers": ["dim2 heoi3", "dim2heoi3", "點去"],
    },
    "cantonese_this_one": {
        "category": "survival",
        "explanation": "When ordering or pointing, 'this one' is '呢個' (ni1 go3).",
        "question": (
            "Practice: Type 'this one' in Cantonese. "
            "Answer with Jyutping (ni1 go3) or Traditional characters (呢個)."
        ),
        "answers": ["ni1 go3", "ni1go3", "呢個"],
    },
    "cantonese_no_ice": {
        "category": "survival",
        "explanation": "To ask for no ice, say '走冰' (zau2 bing1).",
        "question": (
            "Practice: Type 'no ice' in Cantonese. "
            "Answer with Jyutping (zau2 bing1) or Traditional characters (走冰)."
        ),
        "answers": ["zau2 bing1", "zau2bing1", "走冰"],
    },
    "cantonese_less_sugar": {
        "category": "survival",
        "explanation": "To ask for less sugar, say '少甜' (siu2 tim4).",
        "question": (
            "Practice: Type 'less sugar' in Cantonese. "
            "Answer with Jyutping (siu2 tim4) or Traditional characters (少甜)."
        ),
        "answers": ["siu2 tim4", "siu2tim4", "少甜"],
    },
    "cantonese_takeaway": {
        "category": "survival",
        "explanation": "For takeaway or to-go, say '外賣' (ngoi6 maai6).",
        "question": (
            "Practice: Type 'takeaway' in Cantonese. "
            "Answer with Jyutping (ngoi6 maai6) or Traditional characters (外賣)."
        ),
        "answers": ["ngoi6 maai6", "ngoi6maai6", "外賣"],
    },
    "cantonese_bill_please": {
        "category": "survival",
        "explanation": (
            "To ask for the bill, say '埋單唔該' "
            "(maai4 daan1 m4 goi1), meaning 'The bill, please.'"
        ),
        "question": (
            "Practice: Type 'The bill, please' in Cantonese. "
            "Answer with Jyutping or Traditional characters."
        ),
        "answers": [
            "maai4 daan1 m4 goi1",
            "maai4daan1m4goi1",
            "埋單唔該",
        ],
    },
    "cantonese_numbers_1_to_10": {
        "category": "survival",
        "explanation": (
            "Cantonese numbers 1-10 are: 一, 二, 三, 四, 五, 六, 七, 八, 九, 十 "
            "(jat1, ji6, saam1, sei3, ng5, luk6, cat1, baat3, gau2, sap6)."
        ),
        "question": (
            "Practice: Type Cantonese numbers 1 to 10 in order. "
            "Answer with Jyutping or Traditional characters."
        ),
        "answers": [
            "jat1 ji6 saam1 sei3 ng5 luk6 cat1 baat3 gau2 sap6",
            "jat1ji6saam1sei3ng5luk6cat1baat3gau2sap6",
            "一二三四五六七八九十",
        ],
    },
    "cantonese_too_expensive": {
        "category": "survival",
        "explanation": "To say something is too expensive, say '太貴' (taai3 gwai3).",
        "question": (
            "Practice: Type 'too expensive' in Cantonese. "
            "Answer with Jyutping (taai3 gwai3) or Traditional characters (太貴)."
        ),
        "answers": ["taai3 gwai3", "taai3gwai3", "太貴"],
    },
    "cantonese_pay_by_card": {
        "category": "survival",
        "explanation": (
            "To say you will pay by card, say '我用卡俾錢' "
            "(ngo5 jung6 kaat1 bei2 cin2)."
        ),
        "question": (
            "Practice: Type 'I will pay by card' in Cantonese. "
            "Answer with Jyutping or Traditional characters."
        ),
        "answers": [
            "ngo5 jung6 kaat1 bei2 cin2",
            "ngo5jung6kaat1bei2cin2",
            "我用卡俾錢",
        ],
    },
    "cantonese_pay_cash": {
        "category": "survival",
        "explanation": (
            "To say you will pay cash, say '我俾現金' "
            "(ngo5 bei2 jin6 gam1)."
        ),
        "question": (
            "Practice: Type 'I will pay cash' in Cantonese. "
            "Answer with Jyutping or Traditional characters."
        ),
        "answers": [
            "ngo5 bei2 jin6 gam1",
            "ngo5bei2jin6gam1",
            "我俾現金",
        ],
    },
    "cantonese_really": {
        "category": "survival",
        "explanation": "A natural way to say 'Really?' is '真係？' (zan1 hai6).",
        "question": (
            "Practice: Type 'Really?' in Cantonese. "
            "Answer with Jyutping (zan1 hai6) or Traditional characters (真係)."
        ),
        "answers": ["zan1 hai6", "zan1hai6", "真係？", "真係"],
    },
    "cantonese_okay": {
        "category": "survival",
        "explanation": "For 'Okay' or 'fine,' say '好呀' (hou2 aa3).",
        "question": (
            "Practice: Type 'Okay' in Cantonese. "
            "Answer with Jyutping (hou2 aa3) or Traditional characters (好呀)."
        ),
        "answers": ["hou2 aa3", "hou2aa3", "好呀"],
    },
    "cantonese_no_problem": {
        "category": "survival",
        "explanation": "To say 'No problem,' use '冇問題' (mou5 man6 tai4).",
        "question": (
            "Practice: Type 'No problem' in Cantonese. "
            "Answer with Jyutping or Traditional characters."
        ),
        "answers": [
            "mou5 man6 tai4",
            "mou5man6tai4",
            "冇問題",
        ],
    },
    "cantonese_one_moment": {
        "category": "survival",
        "explanation": (
            "To ask for a moment, say '等陣' (dang2 zan6), meaning "
            "'wait a moment.'"
        ),
        "question": (
            "Practice: Type 'One moment' in Cantonese. "
            "Answer with Jyutping (dang2 zan6) or Traditional characters (等陣)."
        ),
        "answers": ["dang2 zan6", "dang2zan6", "等陣"],
    },
    "cantonese_what_does_this_mean": {
        "category": "question",
        "explanation": (
            "To ask what something means, say '呢個係咩意思？' "
            "(ni1 go3 hai6 me1 ji3 si1)."
        ),
        "question": (
            "Practice: Type 'What does this mean?' in Cantonese. "
            "Answer with Jyutping or Traditional characters."
        ),
        "answers": [
            "ni1 go3 hai6 me1 ji3 si1",
            "ni1go3hai6me1ji3si1",
            "呢個係咩意思？",
            "呢個係咩意思",
        ],
    },
    "cantonese_cafe_order": {
        "category": "scenario",
        "prerequisites": [
            "cantonese_i_want",
            "cantonese_thank_you",
        ],
        "explanation": (
            "A simple cafe order pattern: '我要一杯咖啡。' (ngo5 jiu3 jat1 bui1 kaa1 fei1)."
        ),
        "question": (
            "Scenario: At a cafe, order 'I want a cup of coffee' in Cantonese. "
            "Answer with Jyutping or Traditional characters."
        ),
        "answers": [
            "ngo5 jiu3 jat1 bui1 kaa1 fei1",
            "ngo5jiu3 jat1bui1 kaa1fei1",
            "我要一杯咖啡",
            "我要一杯咖啡。",
        ],
    },
}


def list_topics() -> list[str]:
    return list(CONTENT_BANK.keys())


def topic_category(topic: str) -> str:
    entry = CONTENT_BANK.get(topic) or {}
    cat = entry.get("category")
    return str(cat) if cat is not None else "general"


def topic_difficulty(topic: str) -> int:
    metadata = CURRICULUM_METADATA.get(topic) or {}
    try:
        difficulty = int(metadata.get("difficulty", 1))
    except (TypeError, ValueError):
        difficulty = 1
    return max(1, min(5, difficulty))


def topic_tags(topic: str) -> list[str]:
    metadata = CURRICULUM_METADATA.get(topic) or {}
    raw_tags = metadata.get("tags")
    if not isinstance(raw_tags, list):
        return []
    tags: list[str] = []
    for raw in raw_tags:
        tag = str(raw).strip()
        if tag and tag not in tags:
            tags.append(tag)
    return tags


def topic_prerequisites(topic: str) -> list[str]:
    metadata = CURRICULUM_METADATA.get(topic) or {}
    metadata_prereqs = metadata.get("prerequisites")
    if isinstance(metadata_prereqs, list):
        return [str(x) for x in metadata_prereqs if str(x).strip()]

    entry = CONTENT_BANK.get(topic) or {}
    prereqs = entry.get("prerequisites")
    if isinstance(prereqs, list):
        return [str(x) for x in prereqs]
    return []
