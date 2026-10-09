from __future__ import annotations

import json
from pathlib import Path
import unittest

from courier_game.dialogue import EndingRule, resolve_ending
from courier_game.state import StoryState


class StoryDataTests(unittest.TestCase):
    def test_story_data_has_unique_endings_and_valid_quest_references(self) -> None:
        root = Path(__file__).resolve().parents[1]
        data = json.loads((root / "assets" / "story.json").read_text(encoding="utf-8"))
        quest_ids = set(data["quests"])
        endings = data["endings"]
        ending_ids = [ending["id"] for ending in endings]
        self.assertEqual(len(ending_ids), len(set(ending_ids)))
        for ending in endings:
            self.assertTrue(set(ending.get("quests", [])).issubset(quest_ids))

    def test_lex_route_is_independent_of_legacy_karma(self) -> None:
        state = StoryState(final_choice="stay")
        state.complete("lex_truth")
        state.set_flag("lex_trust")
        rules = [EndingRule("dream_together", frozenset({"lex_trust"}), frozenset({"lex_truth"}), "stay")]
        self.assertEqual(resolve_ending(state, rules), "dream_together")


if __name__ == "__main__":
    unittest.main()
