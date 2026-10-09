"""Audio event mixing primitives independent from SDL2 backend."""

from __future__ import annotations

from dataclasses import dataclass
import random


@dataclass(frozen=True)
class AudioEvent:
    name: str
    volume: float = 1.0
    pan: float = 0.0
    pitch: float = 1.0
    bus: str = "sfx"


def clamp(value: float, low: float, high: float) -> float:
    return max(low, min(high, value))


def spatial_event(
    name: str,
    source_x: float,
    listener_x: float,
    max_distance: float,
    rng: random.Random | None = None,
) -> AudioEvent:
    if max_distance <= 0:
        raise ValueError("max_distance must be positive")
    distance = abs(source_x - listener_x)
    volume = clamp(1.0 - distance / max_distance, 0.0, 1.0)
    pan = clamp((source_x - listener_x) / max_distance, -1.0, 1.0)
    randomizer = rng or random
    pitch = randomizer.uniform(0.96, 1.04)
    return AudioEvent(name=name, volume=volume, pan=pan, pitch=pitch)


class AudioBus:
    """Small deterministic bus mixer for ducking and scene transitions."""

    def __init__(self) -> None:
        self.levels = {"master": 1.0, "music": 1.0, "ambience": 1.0, "sfx": 1.0, "voice": 1.0}
        self._duck_targets: dict[str, float] = {}

    def set_duck(self, bus: str, level: float) -> None:
        self._duck_targets[bus] = clamp(level, 0.0, 1.0)

    def clear_duck(self, bus: str) -> None:
        self._duck_targets.pop(bus, None)

    def update(self, dt: float, smoothing: float = 8.0) -> None:
        blend = clamp(max(0.0, dt) * smoothing, 0.0, 1.0)
        for bus, current in self.levels.items():
            target = self._duck_targets.get(bus, 1.0)
            self.levels[bus] = current + (target - current) * blend

    def gain(self, bus: str, event_volume: float) -> float:
        return clamp(self.levels.get("master", 1.0) * self.levels.get(bus, 1.0) * event_volume, 0.0, 1.0)
