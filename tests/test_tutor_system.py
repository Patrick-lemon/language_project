from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from learner_model import LearnerModel
from memory import Memory
from planner import Planner
import session_store
from tools.content_bank import CONTENT_BANK
from tools.content_bank import topic_difficulty, topic_prerequisites, topic_tags
from tools.grammar import check_answer
from tools.progress import format_scenario_progress
from tools.tutor_actions import review_topic_intro, update_review_status


class TutorSystemTests(unittest.TestCase):
    def test_session_state_round_trip(self) -> None:
        learner = LearnerModel(name="Alice")
        learner.learning_focus = "custom"
        learner.custom_focus_topics = ["cantonese_where", "cantonese_i_need"]
        learner.record_result("cantonese_where", False)

        memory = Memory()
        memory.remember({"type": "practice_attempt", "topic": "cantonese_where"})
        memory.update_topic_result("cantonese_where", False)
        memory.mark_task_completed("review:cantonese_where")

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.object(session_store, "STATE_DIR", Path(tmpdir)):
                session_store.save_session_state(learner, memory)
                loaded = session_store.load_session_state("Alice")

        self.assertIsNotNone(loaded)
        loaded_learner, loaded_memory = loaded or (LearnerModel("Student"), Memory())
        self.assertEqual(loaded_learner.name, "Alice")
        self.assertEqual(loaded_learner.review_queue, ["cantonese_where"])
        self.assertEqual(
            loaded_learner.custom_focus_topics,
            ["cantonese_where", "cantonese_i_need"],
        )
        self.assertEqual(loaded_memory.topic_history["cantonese_where"], [False])

    def test_planner_prioritizes_recent_wrong_answer(self) -> None:
        learner = LearnerModel(name="Student")
        learner.add_to_review("cantonese_thank_you")
        learner.record_result("cantonese_where", False)

        memory = Memory()
        memory.update_topic_result("cantonese_where", False)
        memory.remember(
            {
                "type": "practice_attempt",
                "topic": "cantonese_where",
                "answer": "wrong",
                "correct": False,
                "planner_action": "practice",
            }
        )

        plan = Planner().choose_plan(learner, memory)

        self.assertEqual(plan.action, "review")
        self.assertEqual(plan.topic, "cantonese_where")

    def test_planner_waits_until_spaced_review_is_due(self) -> None:
        learner = LearnerModel(name="Student")
        learner.add_to_review("cantonese_thank_you")
        memory = Memory()
        memory.update_topic_result("cantonese_thank_you", False)
        memory.schedule_review("cantonese_thank_you", 2)

        early_plan = Planner().choose_plan(learner, memory)
        self.assertNotEqual(early_plan.topic, "cantonese_thank_you")

        for i in range(2):
            memory.remember(
                {
                    "type": "practice_attempt",
                    "topic": f"cantonese_dummy_{i}",
                    "correct": True,
                }
            )

        due_plan = Planner().choose_plan(learner, memory)
        self.assertEqual(due_plan.action, "review")
        self.assertEqual(due_plan.topic, "cantonese_thank_you")

    def test_planner_gates_difficult_topics_until_prerequisites_are_stable(self) -> None:
        learner = LearnerModel(name="Student")
        learner.learning_focus = "custom"
        learner.custom_focus_topics = ["cantonese_where_mtr", "cantonese_where"]
        memory = Memory()

        locked_plan = Planner().choose_plan(learner, memory)
        self.assertEqual(locked_plan.topic, "cantonese_where")

        learner.mastery_by_topic["cantonese_where"] = 0.65
        for topic in (
            "cantonese_greetings",
            "cantonese_thank_you",
            "cantonese_yes",
            "cantonese_no",
            "cantonese_please",
            "cantonese_excuse_me",
        ):
            learner.mastery_by_topic[topic] = 0.7

        unlocked_plan = Planner().choose_plan(learner, memory)
        self.assertEqual(unlocked_plan.topic, "cantonese_where_mtr")

    def test_scenario_progress_is_ascii_safe(self) -> None:
        report = format_scenario_progress(LearnerModel(name="Student"))
        self.assertTrue(report.isascii())
        self.assertIn("LOCKED - raise:", report)

    def test_review_status_and_intro(self) -> None:
        learner = LearnerModel(name="Student")
        learner.add_to_review("cantonese_thank_you")
        memory = Memory()
        memory.update_topic_result("cantonese_thank_you", True)

        intro = review_topic_intro("cantonese_thank_you", learner, memory)
        status = update_review_status(learner, memory, "cantonese_thank_you")

        self.assertIn("[ReviewSkill]", intro)
        self.assertIn("accuracy=1.00", intro)
        self.assertEqual(learner.review_queue, [])
        self.assertIn("removed from review queue", status)

    def test_repair_phrase_lessons_are_available(self) -> None:
        expected_topics = {
            "cantonese_i_dont_understand": "ngo5 m4 ming4",
            "cantonese_say_again": "請再講一次",
            "cantonese_speak_slowly": "gong2 maan6 di1",
            "cantonese_learning_cantonese": "我學緊廣東話",
            "cantonese_speak_english": "你識唔識講英文",
        }

        for topic, answer in expected_topics.items():
            self.assertEqual(CONTENT_BANK[topic]["category"], "survival")
            self.assertTrue(check_answer(topic, answer)[0])

    def test_expanded_travel_food_number_and_glue_lessons_are_available(self) -> None:
        expected_topics = {
            "cantonese_left": ("survival", "左邊"),
            "cantonese_right": ("survival", "jau6 bin1"),
            "cantonese_straight_ahead": ("survival", "一直行"),
            "cantonese_where_mtr": ("scenario", "港鐵站喺邊度"),
            "cantonese_near_here": ("question", "近唔近呢度"),
            "cantonese_how_to_get_to": ("question", "dim2 heoi3"),
            "cantonese_this_one": ("survival", "呢個"),
            "cantonese_no_ice": ("survival", "走冰"),
            "cantonese_less_sugar": ("survival", "siu2 tim4"),
            "cantonese_takeaway": ("survival", "外賣"),
            "cantonese_bill_please": ("survival", "埋單唔該"),
            "cantonese_numbers_1_to_10": ("survival", "一二三四五六七八九十"),
            "cantonese_too_expensive": ("survival", "太貴"),
            "cantonese_pay_by_card": ("survival", "我用卡俾錢"),
            "cantonese_pay_cash": ("survival", "ngo5 bei2 jin6 gam1"),
            "cantonese_really": ("survival", "真係"),
            "cantonese_okay": ("survival", "hou2 aa3"),
            "cantonese_no_problem": ("survival", "冇問題"),
            "cantonese_one_moment": ("survival", "等陣"),
            "cantonese_what_does_this_mean": ("question", "呢個係咩意思"),
        }

        for topic, (category, answer) in expected_topics.items():
            self.assertEqual(CONTENT_BANK[topic]["category"], category)
            self.assertTrue(check_answer(topic, answer)[0])

    def test_curriculum_metadata_covers_all_topics(self) -> None:
        for topic in CONTENT_BANK:
            self.assertGreaterEqual(topic_difficulty(topic), 1)
            self.assertLessEqual(topic_difficulty(topic), 5)
            self.assertIsInstance(topic_tags(topic), list)

        self.assertIn("cantonese_where", topic_prerequisites("cantonese_where_mtr"))
        self.assertIn("directions", topic_tags("cantonese_where_mtr"))


if __name__ == "__main__":
    unittest.main()
