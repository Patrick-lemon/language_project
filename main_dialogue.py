from dialogue_focus import (
    apply_initial_focus_choice,
    focus_summary,
    print_topic_catalog,
    run_focus_menu,
)
from learner_model import LearnerModel
from memory import Memory
from planner import Planner
from skills import CorrectionSkill, ExplainSkill, PracticeSkill, ReviewSkill
from tools.llm import describe_runtime_mode
from tools.progress import format_scenario_progress


def run_tutoring_session() -> None:
    print("=== Agent Language Tutor (MVP) ===")
    print(describe_runtime_mode())
    name = input("Learner name: ").strip() or "Student"

    learner = LearnerModel(name=name)
    print(
        """
What do you want to prioritize today?
  1) Balanced — tutor mixes categories
  2) Survival — polite phrases & essentials
  3) Questions — question words & patterns
  4) Scenarios — situational lines (still gated until prerequisites are met)
  5) Custom — you pick topic ids (comma-separated; you can `list` on the next prompt)
"""
    )
    choice = input("Enter 1–5 [default 1]: ").strip() or "1"
    if choice == "5":
        print_topic_catalog()
    apply_initial_focus_choice(learner, choice)
    print(f"Starting focus: {focus_summary(learner)}")
    print(
        "Tip: type **menu** at the continue or answer prompt anytime to change topics/focus.\n"
    )

    memory = Memory()
    planner = Planner()
    explain_skill = ExplainSkill()
    practice_skill = PracticeSkill()
    correction_skill = CorrectionSkill()
    review_skill = ReviewSkill()

    while True:
        learner_snapshot = learner.snapshot()
        recent_events = memory.recent_events(5)

        print("\nCurrent learner state:", learner_snapshot)
        print(f"Your focus: {focus_summary(learner)}")
        print(format_scenario_progress(learner))
        plan = planner.choose_plan(learner, memory)
        print(f"Planner decision -> action={plan.action}, topic={plan.topic}")
        print(f"Reason: {plan.reason}")

        if plan.action in {"explain", "review"}:
            message = explain_skill.run(plan.topic, learner_snapshot, recent_events)
            print(message)
            memory.remember(
                {"type": "instruction", "topic": plan.topic, "content": message}
            )

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
                    continue
                break
            if user_signal == "q":
                break

        prompt_text = practice_skill.build_prompt(plan.topic, learner_snapshot, recent_events)
        print(f"\n[PracticeSkill] {prompt_text}")
        while True:
            answer = input("Your answer (q=quit, menu=change focus): ").strip()
            if answer.lower() == "q":
                break
            if answer.lower() == "menu":
                run_focus_menu(learner)
                continue
            break
        if answer.lower() == "q":
            break

        is_correct, correction_message = correction_skill.run(
            plan.topic,
            answer,
            learner_snapshot,
            recent_events,
        )
        print(correction_message)

        learner.record_result(plan.topic, is_correct)
        memory.update_topic_result(plan.topic, is_correct)
        learner.add_vocabulary_item(answer)

        review_message = review_skill.run(learner, memory, plan.topic)
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

    print("\nSession ended.")
    print("Final learner state:", learner.snapshot())


if __name__ == "__main__":
    run_tutoring_session()
