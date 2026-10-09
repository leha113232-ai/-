"""Deterministic animation and melee state machines."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ActionPhase(str, Enum):
    IDLE = "idle"
    WINDUP = "windup"
    ACTIVE = "active"
    RECOVERY = "recovery"


@dataclass
class GroundedEntity:
    x: float
    ground_y: float
    visual_y: float = 0.0
    facing: int = 1
    airborne: bool = False

    @property
    def draw_y(self) -> float:
        return self.ground_y + self.visual_y

    def snap_to_ground(self) -> None:
        self.visual_y = 0.0
        self.airborne = False


@dataclass(frozen=True)
class AttackTiming:
    windup: float = 0.12
    active: float = 0.10
    recovery: float = 0.22

    @property
    def total(self) -> float:
        return self.windup + self.active + self.recovery


@dataclass
class AttackState:
    timing: AttackTiming = AttackTiming()
    phase: ActionPhase = ActionPhase.IDLE
    elapsed: float = 0.0
    hit_emitted: bool = False

    def start(self, timing: AttackTiming | None = None) -> None:
        self.timing = timing or self.timing
        self.phase = ActionPhase.WINDUP
        self.elapsed = 0.0
        self.hit_emitted = False

    def update(self, dt: float) -> ActionPhase:
        if self.phase is ActionPhase.IDLE:
            return self.phase
        self.elapsed += max(0.0, dt)
        if self.elapsed < self.timing.windup:
            self.phase = ActionPhase.WINDUP
        elif self.elapsed < self.timing.windup + self.timing.active:
            self.phase = ActionPhase.ACTIVE
        elif self.elapsed < self.timing.total:
            self.phase = ActionPhase.RECOVERY
        else:
            self.phase = ActionPhase.IDLE
            self.elapsed = 0.0
            self.hit_emitted = False
        return self.phase

    def consume_hit(self) -> bool:
        if self.phase is ActionPhase.ACTIVE and not self.hit_emitted:
            self.hit_emitted = True
            return True
        return False

    def cancel(self) -> None:
        self.phase = ActionPhase.IDLE
        self.elapsed = 0.0
        self.hit_emitted = False


def update_entity(entity: GroundedEntity, attack: AttackState, dt: float) -> ActionPhase:
    """Advance gameplay and guarantee no stale airborne visual offset."""

    phase = attack.update(dt)
    if phase is ActionPhase.IDLE:
        entity.snap_to_ground()
    return phase


def frame_index(frame_count: int, elapsed: float, frame_time: float = 0.10) -> int:
    if frame_count <= 0:
        raise ValueError("frame_count must be positive")
    if frame_time <= 0:
        raise ValueError("frame_time must be positive")
    return int(max(0.0, elapsed) / frame_time) % frame_count


def nearest_scale_size(width: int, height: int, scale: int) -> tuple[int, int]:
    if scale < 1:
        raise ValueError("scale must be positive")
    return width * scale, height * scale
