from .provider_contract import InternalIntelligenceProvider
from internal_intelligence.learning.learning_manager import (
    pending_lessons,
    approved_knowledge,
    learned_skills,
    propose_lesson,
    propose_improvement,
)
from internal_intelligence.learning.thinking_manager import think_about_learning
from internal_intelligence.reasoning.reasoning_manager import reason
from internal_intelligence.runtime.gguf_runtime import GGUFRuntime


class GMAProvider(InternalIntelligenceProvider):

    def provider_name(self):
        return "gma"

    def provider_status(self):
        return {
            "provider": "gma",
            "enabled": True,
            "learning_connected": True,
            "thinking_connected": True
        }

    def think(self, prompt, context=None):
        context = context or {}
        mode = context.get("mode", "conversation")

        if mode == "learning":
            thought = think_about_learning(
                prompt,
                approved_knowledge=self.get_approved_knowledge(),
                learned_skills=self.get_learned_skills()
            )
        else:
            runtime = GGUFRuntime(model_asset="GerfexModels/google_gemma-3-4b-it-Q2_K.gguf")
            generated = runtime.generate(prompt)

            if generated.get("ok"):
                thought = {
                    "ok": True,
                    "kind": "conversation",
                    "answer": generated.get("reply", ""),
                    "reason": "gguf_runtime_generated"
                }
            else:
                thought = reason(
                    prompt,
                    mode="conversation",
                    approved_knowledge=self.get_approved_knowledge(),
                    learned_skills=self.get_learned_skills()
                )
                thought["runtime_status"] = generated.get("reason")

        return {
            "ok": thought.get("ok", False),
            "provider": "gma",
            "mode": mode,
            "thought": thought,
            "approved_knowledge_count": len(self.get_approved_knowledge()),
            "learned_skills_count": len(self.get_learned_skills())
        }

    def learn(self, lesson):
        return {
            "ok": False,
            "reason": "direct_learning_requires_mashel_approval"
        }

    def propose_learning(self, lesson):
        thought = self.think(lesson).get("thought", {})
        kind = thought.get("kind")

        if kind == "question":
            return {
                "ok": True,
                "type": "question",
                "saved": False,
                "reason": "question_not_saved_as_learning",
                "thought": thought
            }

        if kind == "improvement":
            item = propose_improvement(thought.get("proposal") or lesson)
            return {
                "ok": True,
                "type": "improvement",
                "pending": item,
                "thought": thought
            }

        if kind == "lesson":
            item = propose_lesson(thought.get("proposal") or lesson)
            return {
                "ok": True,
                "type": "lesson",
                "pending": item,
                "thought": thought
            }

        return {
            "ok": True,
            "type": "unknown",
            "saved": False,
            "reason": "unknown_learning_kind_not_saved",
            "thought": thought
        }

    def get_pending_lessons(self):
        return pending_lessons()

    def get_approved_knowledge(self):
        return approved_knowledge()

    def get_learned_skills(self):
        return learned_skills()
