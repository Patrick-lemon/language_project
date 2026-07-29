from __future__ import annotations

import unittest
from unittest.mock import patch

from learner_model import LearnerModel
from memory import Memory
from voice_tutor import ActiveLesson, VoiceTutorSession, VoiceTutorSessionManager


class VoiceTutorTests(unittest.TestCase):
    def test_start_next_lesson_creates_active_voice_round(self) -> None:
        with patch("voice_tutor.save_session_state"):
            session = VoiceTutorSession(
                session_id="test",
                learner=LearnerModel(name="Voice"),
                memory=Memory(),
            )
            payload = session.start_next_lesson()

        self.assertIsNotNone(payload["lesson"])
        self.assertEqual(payload["lesson"]["stage"], "guided")
        self.assertEqual(payload["messages"][-1]["role"], "teacher")
        self.assertIn("How I'd say it:", payload["messages"][-1]["text"])
        speech_segments = payload["messages"][-1]["speech_segments"]
        self.assertTrue(any(segment["lang"] == "zh-HK" for segment in speech_segments))

    def test_config_exposes_topic_catalog_for_elective_picker(self) -> None:
        config = VoiceTutorSessionManager().config_payload()

        self.assertIsInstance(config["topics"], list)
        first_topic = config["topics"][0]
        self.assertIn("id", first_topic)
        self.assertIn("label", first_topic)
        self.assertIn("category", first_topic)
        self.assertIn("difficulty", first_topic)
        repair_topic = next(
            topic for topic in config["topics"] if topic["id"] == "cantonese_i_dont_understand"
        )
        self.assertEqual(repair_topic["english"], "I don't understand")

    def test_update_focus_saves_electives_with_balanced_roadmap(self) -> None:
        with patch("voice_tutor.save_session_state"):
            session = VoiceTutorSession(
                session_id="test",
                learner=LearnerModel(name="Voice"),
                memory=Memory(),
            )
            payload = session.update_focus("balanced", ["cantonese_where"])

        self.assertEqual(payload["learner"]["learning_focus"], "balanced")
        self.assertEqual(payload["learner"]["custom_focus_topics"], ["cantonese_where"])
        self.assertIn("electives", payload["focus"])

    def test_repeat_command_replays_teacher_demo(self) -> None:
        with patch("voice_tutor.save_session_state"):
            session = VoiceTutorSession(
                session_id="test",
                learner=LearnerModel(name="Voice"),
                memory=Memory(),
            )
            session.start_next_lesson()
            payload = session.process_learner_turn("repeat again")

        self.assertEqual(payload["lesson"]["stage"], "guided")
        self.assertIn("model it once more", payload["messages"][-1]["text"].lower())
        self.assertTrue(any(segment["lang"] == "zh-HK" for segment in payload["messages"][-1]["speech_segments"]))

    def test_short_topic_accepts_longer_spoken_shell(self) -> None:
        with patch("voice_tutor.save_session_state"):
            session = VoiceTutorSession(
                session_id="test",
                learner=LearnerModel(name="Voice"),
                memory=Memory(),
                active_lesson=ActiveLesson(topic="cantonese_yes", action="explain"),
            )
            payload = session.process_learner_turn("hai6 aa3")

        self.assertEqual(payload["lesson"]["stage"], "roleplay")
        self.assertIn("core line", payload["messages"][-1]["text"].lower())

    def test_short_topic_accepts_chinese_asr_variant(self) -> None:
        with patch("voice_tutor.save_session_state"):
            session = VoiceTutorSession(
                session_id="test",
                learner=LearnerModel(name="Voice"),
                memory=Memory(),
                active_lesson=ActiveLesson(topic="cantonese_yes", action="explain"),
            )
            payload = session.process_learner_turn("系啊")

        self.assertEqual(payload["lesson"]["stage"], "roleplay")

    def test_alternative_transcript_can_rescue_primary_asr_result(self) -> None:
        with patch("voice_tutor.save_session_state"):
            session = VoiceTutorSession(
                session_id="test",
                learner=LearnerModel(name="Voice"),
                memory=Memory(),
                active_lesson=ActiveLesson(topic="cantonese_greetings", action="explain"),
            )
            payload = session.process_learner_turn("hello", alternatives=["你好呀", "你好"])

        self.assertEqual(payload["lesson"]["stage"], "roleplay")

    def test_repair_phrase_voice_lesson_accepts_spoken_variant(self) -> None:
        with patch("voice_tutor.save_session_state"):
            session = VoiceTutorSession(
                session_id="test",
                learner=LearnerModel(name="Voice"),
                memory=Memory(),
                active_lesson=ActiveLesson(
                    topic="cantonese_i_dont_understand",
                    action="explain",
                ),
            )
            payload = session.process_learner_turn("ngo5 m4 ming4 aa3")

        self.assertEqual(payload["lesson"]["stage"], "roleplay")
        self.assertIn("core line", payload["messages"][-1]["text"].lower())

    def test_short_expanded_voice_lesson_accepts_fuller_spoken_variant(self) -> None:
        with patch("voice_tutor.save_session_state"):
            session = VoiceTutorSession(
                session_id="test",
                learner=LearnerModel(name="Voice"),
                memory=Memory(),
                active_lesson=ActiveLesson(topic="cantonese_this_one", action="explain"),
            )
            payload = session.process_learner_turn("ni1 go3 aa3")

        self.assertEqual(payload["lesson"]["stage"], "roleplay")

    def test_next_command_moves_to_next_lesson(self) -> None:
        with patch("voice_tutor.save_session_state"):
            session = VoiceTutorSession(
                session_id="test",
                learner=LearnerModel(name="Voice"),
                memory=Memory(),
                active_lesson=ActiveLesson(topic="cantonese_greetings", action="explain"),
            )
            payload = session.process_learner_turn("next lesson")

        self.assertEqual(payload["messages"][-2]["role"], "teacher")
        self.assertIn("move on", payload["messages"][-2]["text"].lower())
        self.assertEqual(payload["messages"][-1]["role"], "teacher")
        self.assertIn("How I'd say it:", payload["messages"][-1]["text"])

    def test_correct_turn_moves_from_guided_to_roleplay_then_complete(self) -> None:
        with patch("voice_tutor.save_session_state"):
            session = VoiceTutorSession(
                session_id="test",
                learner=LearnerModel(name="Voice"),
                memory=Memory(),
                active_lesson=ActiveLesson(topic="cantonese_greetings", action="explain"),
            )

            first = session.process_learner_turn("nei5 hou2")
            self.assertEqual(first["lesson"]["stage"], "roleplay")
            self.assertFalse(first["awaiting_next_lesson"])

            second = session.process_learner_turn("nei5 hou2")
            self.assertTrue(second["awaiting_next_lesson"])
            self.assertTrue(second["lesson"]["completed"])
            self.assertIn("next lesson", second["messages"][-1]["text"].lower())

    def test_three_failed_attempts_finish_with_review(self) -> None:
        with patch("voice_tutor.save_session_state"):
            session = VoiceTutorSession(
                session_id="test",
                learner=LearnerModel(name="Voice"),
                memory=Memory(),
                active_lesson=ActiveLesson(topic="cantonese_thank_you", action="review"),
            )

            session.process_learner_turn("wrong one")
            session.process_learner_turn("wrong two")
            payload = session.process_learner_turn("wrong three")

        self.assertTrue(payload["awaiting_next_lesson"])
        self.assertIn("review", payload["messages"][-1]["text"].lower())


if __name__ == "__main__":
    unittest.main()
