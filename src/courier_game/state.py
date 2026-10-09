"""Core state and migration helpers for the rebuilt Courier game."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

SAVE_VERSION = 2


@dataclass
class StoryState:
    """Explicit story flags replace the opaque legacy karma score."""

    version: int = SAVE_VERSION
    quests: dict[str, str] = field(default_factory=dict)
    flags: set[str] = field(default_factory=set)
    relationships: dict[str, int] = field(default_factory=dict)
    final_choice: str | None = None
    seen_dialogue: set[str] = field(default_factory=set)

    def complete(self, quest_id: str) -> None:
        self.quests[quest_id] = "complete"

    def fail(self, quest_id: str) -> None:
        self.quests[quest_id] = "failed"

    def active(self, quest_id: str) -> None:
        self.quests[quest_id] = "active"

    def has_completed(self, quest_id: str) -> bool:
        return self.quests.get(quest_id) == "complete"

    def set_flag(self, flag: str, enabled: bool = True) -> None:
        if enabled:
            self.flags.add(flag)
        else:
            self.flags.discard(flag)


@dataclass
class TravelState:
    in_flight: bool = False
    destination: str | None = None
    elapsed: float = 0.0
    interrupted: bool = False

    def start(self, destination: str) -> None:
        self.in_flight = True
        self.destination = destination
        self.elapsed = 0.0
        self.interrupted = False

    def finish(self) -> str | None:
        destination = self.destination
        self.in_flight = False
        self.destination = None
        self.elapsed = 0.0
        self.interrupted = False
        return destination

    def cancel(self) -> None:
        self.in_flight = False
        self.interrupted = True
        self.elapsed = 0.0


def migrate_save(raw: dict[str, Any]) -> StoryState:
    """Migrate old saves without allowing legacy karma to drive new endings."""

    state = StoryState()
    for quest_id, status in raw.get("quests", {}).items():
        if status in {"active", "complete", "failed"}:
            state.quests[str(quest_id)] = status
    state.flags.update(str(flag) for flag in raw.get("flags", []) if isinstance(flag, str))
    state.relationships.update(
        {str(key): int(value) for key, value in raw.get("relationships", {}).items()}
    )
    state.final_choice = raw.get("final_choice")
    state.seen_dialogue.update(
        str(node_id) for node_id in raw.get("seen_dialogue", []) if isinstance(node_id, str)
    )

    # The old karma value is deliberately read nowhere. Legacy saves retain all
    # useful quest/choice data but can no longer silently alter an ending.
    state.set_flag("legacy_save_migrated", raw.get("version", 0) < SAVE_VERSION)
    return state


def serialize_save(state: StoryState) -> dict[str, Any]:
    return {
        "version": SAVE_VERSION,
        "quests": dict(state.quests),
        "flags": sorted(state.flags),
        "relationships": dict(state.relationships),
        "final_choice": state.final_choice,
        "seen_dialogue": sorted(state.seen_dialogue),
    }
