# Agent Language Tutor MVP

This project implements a minimum viable tutoring agent framework aligned to the slide architecture with:

- `learner_model.py`: structured learner profile, competence map, and review queue
- `planner.py`: rule-based planner choosing explicit tutoring actions
- `skill/SKILL.md`: markdown skill definition for tutor behavior
- `tools/`: tool-layer modules for LLM calls, grammar checks, skill loading, and tutoring actions
- `memory.py`: interaction history + task tracking + topic accuracy
- `runtime_support.py`: cross-platform `.env` loading and terminal output setup
- `session_store.py`: learner progress persistence across runs
- `main_dialogue.py`: interactive loop that connects everything
- `tests/`: regression tests for planning, persistence, and runtime-safe output

## Run In The Browser (recommended)

```bash
cd "/Users/patrickstar/Documents/LanguageProject"
python3 web_app.py
```

Then open `http://127.0.0.1:8765` in Chrome or Edge.

On Windows you can also double-click `start_voice_tutor.bat`.

The browser app is now the main experience:

- voice-first lesson flow instead of terminal prompts
- browser speech recognition for learner replies
- browser text-to-speech for the teacher voice
- lesson board showing the current target line, stage, focus, and review state
- the same saved learner progress under `state/<learner>.json`

`web_app.py` and `main_dialogue.py` both load `.env` automatically if the file exists, so the direct Python entry point works on macOS, Linux, and Windows.

## Run In The Terminal (legacy)

```bash
cd "/Users/patrickstar/Documents/LanguageProject"
python3 main_dialogue.py
```

## Run with a real LLM (Option 1)

1. Get an API key from **OpenAI** or **OpenRouter** (or use any OpenAI-compatible endpoint).

2. Copy the example env file and edit it:

```bash
cd "/Users/patrickstar/Documents/LanguageProject"
cp .env.example .env
# Edit .env: set TUTOR_LLM_ENABLED=1 and your key
```

3. Start the tutor:

```bash
python3 web_app.py
```

Or, if you still want the old command-line flow:

```bash
python3 main_dialogue.py
```

On startup you should see a line like `LLM: on | API base: ... | model: ...`. If the key is missing or a request fails, the app **falls back** to stub text and keeps running.

The loop demonstrates:

1. Read learner state
2. Generate a plan
3. Execute tutor actions from `tools/` guided by `skill/SKILL.md`
4. Update learner model and memory

## Persistence and Review Flow

- Learner state and session memory are now saved under `state/<learner>.json`.
- Re-entering the same learner name resumes progress automatically.
- Wrong answers now trigger an immediate review pass before the system falls back to the broader review queue.
- Only correct answers are added to the learner's known vocabulary set.

## Browser Voice Tutor

- `voice_tutor.py`: lesson engine for browser-based speaking rounds
- `web_app.py`: local HTTP server for the browser UI and session APIs
- `web/`: static HTML, CSS, and JavaScript for the voice-first interface
- each lesson uses a two-step speaking loop: guided production, then a more natural repeat
- topic progression still follows the learner model, planner, review queue, and scenario gating

## Option 1: LLM-backed tutor (recommended next step)

The agent stays the same (planner, skills, memory). A real model can now power:

- adaptive explanations that see learner state and recent mistakes
- live practice prompts that adjust phrasing and give tiny hints when needed
- hybrid answer grading that keeps deterministic checks but lets the model rescue valid near-miss variants and produce better coaching

All of this still uses **OpenAI-compatible** HTTP APIs (OpenAI, OpenRouter, many local servers).

1. Set an API key and turn the integration on:

```bash
export TUTOR_LLM_ENABLED=1
export TUTOR_LLM_API_KEY="your-key"
# Optional: model id (OpenAI or OpenRouter model string)
export TUTOR_LLM_MODEL="gpt-4o-mini"
```

2. **OpenRouter** example (uses `OPENROUTER_API_KEY` if you prefer):

```bash
export TUTOR_LLM_ENABLED=1
export OPENROUTER_API_KEY="your-key"
export TUTOR_LLM_MODEL="openai/gpt-4o-mini"
# Optional OpenRouter attribution
export OPENROUTER_HTTP_REFERER="https://localhost"
export OPENROUTER_APP_TITLE="LanguageTutor"
```

3. **Custom base URL** (local LLM, proxy, etc.):

```bash
export TUTOR_LLM_ENABLED=1
export TUTOR_LLM_API_KEY="your-key"
export TUTOR_LLM_BASE_URL="http://127.0.0.1:11434/v1"
export TUTOR_LLM_MODEL="llama3.2"
```

If `TUTOR_LLM_ENABLED` is not set, or the request fails, `tools/llm.py` **falls back** to the built-in stub text so you can still demo offline.

**Design note:** the tutor now uses a **hybrid evaluation** path. `tools/grammar.py` remains the first deterministic check for fixed exercises, and the LLM is only asked to adjudicate non-exact matches and generate more contextual coaching. That keeps the loop testable while making it feel much more like a real tutor.

## Current language content
The MVP is set up to practice **Cantonese for English speakers** using a small built-in content bank (currently more than 3 topics).

### Scenario gating
- Some scenario topics are now gated by prerequisite mastery.
- Example: before scenario prompts like bathroom/cafe tasks, the planner expects foundation topics (such as `where`, `I need`, `I want`) to reach a baseline mastery.
- This keeps progression more tutor-like: build basics first, then use them in scenarios.
- Each turn, `main_dialogue.py` prints a **scenario progress** block showing which scenarios are locked vs unlocked and which prerequisites are still below the threshold (see `SCENARIO_PREREQUISITE_MASTERY` in `tools/content_bank.py`).

## Your say in what you learn

At startup, pick a **priority** (balanced, survival-only, questions, scenarios, or custom topic ids).

You are **not** interrupted before every lesson. To change focus or topics, type **`menu`** at:

- the **continue** prompt after an explanation, or  
- the **practice answer** prompt  

That opens a small focus REPL (`focus ...`, `topics ...`, `list`, etc.). Press Enter on an empty `focus>` line to return.

The planner still prioritizes **review queue** and **recent mistakes** so you do not get stuck ignoring weak areas.

## Option 2: Train your own model (separate, heavier track)

Use this when you need a **custom** component (not just API calls):

| Goal | Typical approach |
|------|------------------|
| Better "next exercise" or difficulty | Tabular learner features -> classifier / small neural net; planner reads predicted label |
| Open-ended answer grading | Fine-tune a small LM on (prompt, student answer, score/rubric) pairs |
| Dialogue policy | Offline RL or supervised learning from logged (state, action, outcome) |

Reasonable student scope: **add a small trained classifier** that suggests `explain` vs `practice` from learner features, and keep the rule-based planner as fallback. Plug it in later as `planner_ml.py` without replacing memory or skills.

If you tell me your stack (e.g. PyTorch vs scikit-learn) and dataset size, we can sketch one concrete Option 2 milestone.
