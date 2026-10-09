from __future__ import annotations

import random
import unittest

from courier_game.animation import ActionPhase, AttackState, AttackTiming, GroundedEntity, update_entity
from courier_game.audio import AudioBus, spatial_event
from courier_game.dialogue import DialogueChoice, DialogueGraph, DialogueNode, EndingRule, resolve_ending
from courier_game.state import StoryState, migrate_save


class AnimationTests(unittest.TestCase):
    def test_attack_emits_one_hit_and_lands_entity(self) -> None:
        entity = GroundedEntity(x=10, ground_y=120, visual_y=-14, airborne=True)
        attack = AttackState()
        attack.start(AttackTiming(windup=0.1, active=0.1, recovery=0.1))

        self.assertEqual(update_entity(entity, attack, 0.1), ActionPhase.ACTIVE)
        self.assertTrue(attack.consume_hit())
        self.assertFalse(attack.consume_hit())
        self.assertEqual(update_entity(entity, attack, 0.21), ActionPhase.IDLE)
        self.assertEqual(entity.draw_y, 120)
        self.assertFalse(entity.airborne)


class StoryTests(unittest.TestCase):
    def test_legacy_karma_does_not_survive_migration(self) -> None:
        state = migrate_save({"version": 1, "karma": -999, "quests": {"lex_truth": "complete"}})
        self.assertNotIn("karma", state.__dict__)
        self.assertTrue(state.has_completed("lex_truth"))

    def test_dialogue_once_node_and_targets_are_validated(self) -> None:
        graph = DialogueGraph({
            "intro": DialogueNode(
                "intro", "Лёха", "Поговорим?",
                (DialogueChoice("accept", "Да", "after", frozenset({"lex_trust"})),),
                once=True,
            ),
            "after": DialogueNode("after", "Лёха", "Хорошо."),
        })
        self.assertEqual(graph.validate(), [])
        state = StoryState()
        graph.visit("intro", state)
        self.assertEqual(graph.choose("intro", "accept", state), "after")
        self.assertIn("lex_trust", state.flags)
        self.assertEqual(graph.available("intro", state), ())

    def test_bootstrap_dialogue_shape_exposes_choices(self) -> None:
        graph = DialogueGraph({
            "lex_intro": DialogueNode(
                "lex_intro", "Лёха", "Ты расскажешь правду?",
                (
                    DialogueChoice("tell", "Рассказать", "lex_after", frozenset({"lex_trust"})),
                    DialogueChoice("stay", "Остаться рядом", "lex_after", frozenset({"lex_trust"})),
                ),
            ),
            "lex_after": DialogueNode("lex_after", "Лёха", "Тогда пойдём вместе."),
        })
        state = StoryState()
        self.assertEqual({choice.choice_id for choice in graph.available("lex_intro", state)}, {"tell", "stay"})
        self.assertEqual(graph.choose("lex_intro", "tell", state), "lex_after")
        self.assertIn("lex_trust", state.flags)

    def test_endings_use_explicit_requirements(self) -> None:
        state = StoryState(final_choice="stay")
        state.complete("lex_truth")
        state.set_flag("lex_trust")
        rules = [EndingRule("together", frozenset({"lex_trust"}), frozenset({"lex_truth"}), "stay")]
        self.assertEqual(resolve_ending(state, rules), "together")


class AudioTests(unittest.TestCase):
    def test_audio_event_spatialization_and_ducking(self) -> None:
        event = spatial_event("punch_a", 20, 0, 40, random.Random(1))
        self.assertAlmostEqual(event.volume, 0.5)
        self.assertAlmostEqual(event.pan, 0.5)
        self.assertGreaterEqual(event.pitch, 0.96)
        bus = AudioBus()
        bus.set_duck("music", 0.4)
        bus.update(1.0)
        self.assertAlmostEqual(bus.gain("music", 1.0), 0.4)


if __name__ == "__main__":
    unittest.main()
