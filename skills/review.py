from learner_model import LearnerModel
from memory import Memory
from tools.skill_loader import get_skill_section


class ReviewSkill:
    def run(self, learner: LearnerModel, memory: Memory, topic: str) -> str:
        _ = get_skill_section("review skill")
        accuracy = memory.topic_accuracy(topic)
        if accuracy < 0.7:
            learner.add_to_review(topic)
            return (
                f"[ReviewSkill] {topic} remains in review queue "
                f"(accuracy={accuracy:.2f})."
            )

        if topic in learner.review_queue:
            learner.review_queue.remove(topic)
        return f"[ReviewSkill] {topic} removed from review queue (accuracy={accuracy:.2f})."
