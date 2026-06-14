from dialogue_focus import (
    apply_initial_focus_choice,
    focus_summary,
    print_topic_catalog,
    run_focus_menu,
)
from learner_model import LearnerModel
from memory import Memory
from planner import Planner
from runtime_support import configure_text_output, load_dotenv
from session_store import load_session_state, save_session_state
from tools.llm import describe_runtime_mode
from tools.progress import format_scenario_progress
from tools.tutor_actions import (
    build_practice_prompt,
    correct_answer,
    explain_topic,
    review_topic_intro,
    update_review_status,
)


def _initialize_session(name: str) -> tuple[LearnerModel, Memory]:
    saved_state = load_session_state(name)
    if saved_state is not None:
        learner, memory = saved_state
        print(f"Loaded saved progress for {learner.name}.")
        print(f"Starting focus: {focus_summary(learner)}")
        print("Tip: type `menu` at the continue or answer prompt anytime to change topics/focus.\n")
        return learner, memory

    learner = LearnerModel(name=name)
    print(
        """
What do you want to prioritize today?
  1) Balanced - tutor mixes categories
  2) Survival - polite phrases and essentials
  3) Questions - question words and patterns
  4) Scenarios - situational lines (still gated until prerequisites are met)
  5) Custom - you pick topic ids (comma-separated; you can `list` on the next prompt)
"""
    )
    choice = input("Enter 1-5 [default 1]: ").strip() or "1"
    if choice == "5":
        print_topic_catalog()
    apply_initial_focus_choice(learner, choice)
    print(f"Starting focus: {focus_summary(learner)}")
    print("Tip: type `menu` at the continue or answer prompt anytime to change topics/focus.\n")

    memory = Memory()
    save_session_state(learner, memory)
    return learner, memory


def run_tutoring_session() -> None:
    load_dotenv()
    configure_text_output()
    print("=== Agent Language Tutor (MVP) ===")
    print(describe_runtime_mode())
    name = input("Learner name: ").strip() or "Student"

    learner, memory = _initialize_session(name)
    planner = Planner()

    while True:
        learner_snapshot = learner.snapshot()
        recent_events = memory.recent_events(5)

        print("\nCurrent learner state:", learner_snapshot)
        print(f"Your focus: {focus_summary(learner)}")
        print(format_scenario_progress(learner))
        plan = planner.choose_plan(learner, memory)
        print(f"Planner decision -> action={plan.action}, topic={plan.topic}")
        print(f"Reason: {plan.reason}")

        if plan.action == "explain":
            message = explain_topic(plan.topic, learner_snapshot, recent_events)
        elif plan.action == "review":
            message = review_topic_intro(
                plan.topic,
                learner,
                memory,
                learner_snapshot,
                recent_events,
            )
        else:
            message = ""

        if message:
            print(message)
            memory.remember(
                {"type": "instruction", "topic": plan.topic, "content": message}
            )
            save_session_state(learner, memory)

            cont_prompt = (
                f"Press Enter to continue practice on {plan.topic} "
                f"(q=quit, menu=change focus): "
            )
            while True:
                user_signal = input(cont_prompt).strip().lower()
                if user_signal == "q":
                    break
                if user_signal == "menu":
                    run_focus_menu(learner)
                    save_session_state(learner, memory)
                    continue
                break
            if user_signal == "q":
                break

        prompt_text = build_practice_prompt(plan.topic, learner_snapshot, recent_events)
        print(f"\n[PracticeSkill] {prompt_text}")
        while True:
            answer = input("Your answer (q=quit, menu=change focus): ").strip()
            if answer.lower() == "q":
                break
            if answer.lower() == "menu":
                run_focus_menu(learner)
                save_session_state(learner, memory)
                continue
            break
        if answer.lower() == "q":
            break

        is_correct, correction_message = correct_answer(
            plan.topic,
            answer,
            learner_snapshot,
            recent_events,
        )
        print(correction_message)

        learner.record_result(plan.topic, is_correct)
        memory.update_topic_result(plan.topic, is_correct)
        if is_correct:
            learner.add_vocabulary_item(answer)

        review_message = update_review_status(learner, memory, plan.topic)
        print(review_message)

        memory.mark_task_completed(f"{plan.action}:{plan.topic}")
        memory.remember(
            {
                "type": "practice_attempt",
                "topic": plan.topic,
                "answer": answer,
                "correct": is_correct,
                "planner_action": plan.action,
            }
        )

        print("Recent memory:", memory.recent_events(3))
        save_session_state(learner, memory)

    save_session_state(learner, memory)
    print("\nSession ended.")
    print("Final learner state:", learner.snapshot())


if __name__ == "__main__":
    run_tutoring_session()
