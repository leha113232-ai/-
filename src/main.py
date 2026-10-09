from __future__ import annotations

import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parent
if not (ROOT / "assets").exists():
    ROOT = ROOT.parent
SRC = ROOT / "src"
if not SRC.exists():
    SRC = Path(__file__).resolve().parent

from courier_game.animation import ActionPhase, AttackState, AttackTiming, GroundedEntity, frame_index, update_entity
from courier_game.audio import AudioBus
from courier_game.dialogue import DialogueChoice, DialogueGraph, DialogueNode, EndingRule, resolve_ending
from courier_game.state import StoryState


WIDTH, HEIGHT = 480, 800


class CourierDemo:
    """A small playable vertical slice using the recovered assets and safe core."""

    def __init__(self) -> None:
        self.story = StoryState()
        self.audio = AudioBus()
        self.entity = GroundedEntity(120, 570)
        self.attack = AttackState()
        self.graph = DialogueGraph({
            "lex_intro": DialogueNode(
                "lex_intro", "Лёха", "Ты расскажешь правду?",
                (
                    DialogueChoice("tell", "Рассказать", "lex_after", frozenset({"lex_trust"})),
                    DialogueChoice("stay", "Остаться рядом", "lex_after", frozenset({"lex_trust"})),
                ),
            ),
            "lex_after": DialogueNode("lex_after", "Лёха", "Тогда пойдём вместе."),
        })
        self.dialogue_node = "lex_intro"
        self.mode = "world"
        self.t = 0.0
        self.message = "Нажми ПРОБЕЛ: атака • E: диалог • F: финиш"
        self.font = None
        self.small_font = None
        self.art = {}

    def load(self, pygame) -> None:
        self.font = pygame.font.Font(None, 30)
        self.small_font = pygame.font.Font(None, 21)
        courier = ROOT / "assets" / "art" / "courier"
        for frame in sorted(courier.glob("r0_*.png")):
            try:
                self.art[frame.name] = pygame.image.load(str(frame)).convert_alpha()
            except pygame.error:
                pass

    def text(self, pygame, surface, value, x, y, color=(240, 240, 235), small=False):
        font = self.small_font if small else self.font
        surface.blit(font.render(value, True, color), (x, y))

    def handle(self, pygame, event) -> None:
        if event.type != pygame.KEYDOWN:
            return
        if event.key == pygame.K_SPACE:
            self.attack.start(AttackTiming(0.12, 0.10, 0.24))
            self.message = "Замах → удар → восстановление"
        elif event.key == pygame.K_e:
            if self.graph.available(self.dialogue_node, self.story):
                self.mode = "dialogue"
                self.message = "Выбери 1 или 2"
            else:
                self.message = "Диалог уже завершён"
        elif event.key in (pygame.K_1, pygame.K_2) and self.mode == "dialogue":
            choice_id = "tell" if event.key == pygame.K_1 else "stay"
            if choice_id in {choice.choice_id for choice in self.graph.available(self.dialogue_node, self.story)}:
                self.dialogue_node = self.graph.choose(self.dialogue_node, choice_id, self.story) or self.dialogue_node
                self.mode = "dialogue" if self.graph.available(self.dialogue_node, self.story) else "world"
                self.message = "Лёха услышал правду" if choice_id == "tell" else "Вы остались рядом"
        elif event.key == pygame.K_f:
            self.story.complete("lex_truth")
            self.story.final_choice = "stay"
            self.message = f"Концовка: {resolve_ending(self.story, (EndingRule('dream_together', frozenset({'lex_trust'}), frozenset({'lex_truth'}), 'stay'),))}"
        elif event.key == pygame.K_ESCAPE:
            self.mode = "world"
            self.message = "Нажми ПРОБЕЛ: атака • E: диалог • F: финиш"

    def update(self, dt: float) -> None:
        self.t += dt
        update_entity(self.entity, self.attack, dt)
        self.audio.update(dt)

    def draw(self, pygame, surface) -> None:
        surface.fill((20, 24, 43))
        pygame.draw.rect(surface, (35, 47, 67), (0, 440, WIDTH, 200))
        pygame.draw.rect(surface, (77, 96, 83), (0, 640, WIDTH, 160))
        pygame.draw.line(surface, (166, 148, 105), (0, 640), (WIDTH, 640), 3)
        pygame.draw.circle(surface, (222, 190, 102), (370, 130), 48)
        pygame.draw.rect(surface, (52, 55, 77), (350, 175, 40, 300))
        pygame.draw.rect(surface, (15, 18, 28), (12, 15, WIDTH - 24, 72))
        self.text(pygame, surface, "COURIER • REBUILD", 26, 28)
        self.text(pygame, surface, self.message, 20, 105, small=True)

        shadow = pygame.Rect(int(self.entity.x - 18), int(self.entity.ground_y + 12), 36, 8)
        pygame.draw.ellipse(surface, (23, 28, 30), shadow)
        if self.art:
            key = sorted(self.art)[frame_index(len(self.art), self.t, 0.12)]
            sprite = self.art[key]
            sprite = pygame.transform.scale(sprite, (sprite.get_width() * 3, sprite.get_height() * 3))
            rect = sprite.get_rect(midbottom=(int(self.entity.x), int(self.entity.draw_y)))
            surface.blit(sprite, rect)
        else:
            pygame.draw.rect(surface, (193, 82, 74), (self.entity.x - 14, self.entity.draw_y - 55, 28, 55))

        phase = self.attack.phase.value
        self.text(pygame, surface, f"attack: {phase}", 20, 705, (255, 220, 120), small=True)
        self.text(pygame, surface, f"flags: {', '.join(sorted(self.story.flags)) or 'none'}", 20, 730, small=True)
        if self.mode == "dialogue":
            pygame.draw.rect(surface, (12, 14, 25), (20, 500, WIDTH - 40, 125))
            pygame.draw.rect(surface, (184, 155, 85), (20, 500, WIDTH - 40, 125), 2)
            node = self.graph.nodes[self.dialogue_node]
            self.text(pygame, surface, f"{node.node_id}: {node.text}", 35, 520, small=True)
            self.text(pygame, surface, "1. Рассказать правду   2. Остаться рядом", 35, 555, small=True)


def main() -> None:
    try:
        import pygame
    except ImportError:
        print("Install pygame to run the desktop vertical slice")
        return
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    pygame.display.set_caption("Courier: Put k Mechte — Rebuild")
    clock = pygame.time.Clock()
    game = CourierDemo()
    game.load(pygame)
    running = True
    while running:
        dt = min(clock.tick(60) / 1000.0, 0.1)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            game.handle(pygame, event)
        game.update(dt)
        game.draw(pygame, screen)
        pygame.display.flip()
    pygame.quit()


if __name__ == "__main__":
    main()
