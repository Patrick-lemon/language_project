from __future__ import annotations

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from learner_model import LearnerModel
from memory import Memory
from planner import Planner
import session_store
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


if __name__ == "__main__":
    unittest.main()
