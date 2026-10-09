"""Dialogue graph validation and explicit ending rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterable

from .state import StoryState


@dataclass(frozen=True)
class DialogueChoice:
    choice_id: str
    text: str
    next_id: str | None = None
    set_flags: frozenset[str] = frozenset()
    requires_flags: frozenset[str] = frozenset()


@dataclass(frozen=True)
class DialogueNode:
    node_id: str
    speaker: str
    text: str
    choices: tuple[DialogueChoice, ...] = ()
    once: bool = False


@dataclass
class DialogueGraph:
    nodes: dict[str, DialogueNode] = field(default_factory=dict)

    def validate(self) -> list[str]:
        errors: list[str] = []
        for node in self.nodes.values():
            if not node.node_id:
                errors.append("dialogue node has empty id")
            seen_choices: set[str] = set()
            for choice in node.choices:
                if choice.choice_id in seen_choices:
                    errors.append(f"duplicate choice {choice.choice_id} in {node.node_id}")
                seen_choices.add(choice.choice_id)
                if choice.next_id is not None and choice.next_id not in self.nodes:
                    errors.append(f"missing target {choice.next_id} from {node.node_id}")
        return errors

    def available(self, node_id: str, state: StoryState) -> tuple[DialogueChoice, ...]:
        node = self.nodes[node_id]
        if node.once and node_id in state.seen_dialogue:
            return ()
        return tuple(
            choice
            for choice in node.choices
            if choice.requires_flags.issubset(state.flags)
        )

    def visit(self, node_id: str, state: StoryState) -> DialogueNode:
        return self.nodes[node_id]

    def choose(self, node_id: str, choice_id: str, state: StoryState) -> str | None:
        choices = {choice.choice_id: choice for choice in self.available(node_id, state)}
        choice = choices[choice_id]
        state.flags.update(choice.set_flags)
        state.seen_dialogue.add(node_id)
        return choice.next_id


@dataclass(frozen=True)
class EndingRule:
    ending_id: str
    required_flags: frozenset[str] = frozenset()
    required_quests: frozenset[str] = frozenset()
    required_choice: str | None = None

    def matches(self, state: StoryState) -> bool:
        return (
            self.required_flags.issubset(state.flags)
            and all(state.has_completed(quest) for quest in self.required_quests)
            and (self.required_choice is None or state.final_choice == self.required_choice)
        )


def resolve_ending(state: StoryState, rules: Iterable[EndingRule], fallback: str = "home") -> str:
    for rule in rules:
        if rule.matches(state):
            return rule.ending_id
    return fallback
