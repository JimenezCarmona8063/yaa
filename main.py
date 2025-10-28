from __future__ import annotations

from typing import Callable, Dict

import pygame

from game.actions import Action, ActionType
from game.characters import Character, create_initial_characters
from game.map import CampusMap
from game.scheduler import GameState, TaskScheduler
from game.settings import BACKGROUND_COLOR, FPS, SCREEN_HEIGHT, SCREEN_WIDTH
from game.ui import draw_action_buffer, draw_instructions, draw_resource_panel


def build_action_presets(campus_map: CampusMap) -> Dict[int, Callable[[], Action]]:
    return {
        pygame.K_1: lambda: Action("Dar clase", ActionType.TEACH, "Ingenierías", 4.0, required_role="maestro", urgency=0.9),
        pygame.K_2: lambda: Action("Estudiar", ActionType.STUDY, "Biblioteca", 3.0, required_role="alumno", urgency=1.1),
        pygame.K_3: lambda: Action("Vender snacks", ActionType.SELL, "Oxxo", 2.5, required_role="empleado", urgency=1.3),
        pygame.K_4: lambda: Action("Recorrido rector", ActionType.VISIT, "Smart Center", 3.5, required_role="rector", urgency=0.8),
        pygame.K_5: lambda: Action("Recolectar madera", ActionType.GATHER_WOOD, "Canchas", 4.0, required_role="empleado", urgency=1.4),
        pygame.K_6: lambda: Action("Minar recursos", ActionType.MINE, "Civil", 4.5, required_role="empleado", urgency=1.2),
        pygame.K_7: lambda: Action("Entrenamiento", ActionType.EXERCISE, "Gym", 2.0, urgency=1.0),
        pygame.K_8: lambda: Action("Ir a comer", ActionType.EAT, "Cafetería", 1.5, urgency=1.5),
        pygame.K_9: lambda: Action("Construir aula", ActionType.BUILD, "Fundadores", 4.0, urgency=0.7),
        pygame.K_0: lambda: Action("Alerta de defensa", ActionType.DEFEND, "Entrada", 2.0, urgency=0.3),
    }


def main() -> None:
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Proyecto TACHI - Vida UP")
    clock = pygame.time.Clock()

    campus_map = CampusMap()
    characters = create_initial_characters(campus_map)
    scheduler = TaskScheduler(campus_map)
    scheduler.register_characters(characters)
    game_state = GameState()
    action_presets = build_action_presets(campus_map)

    running = True
    hover_target: Character | None = None

    while running:
        dt = clock.tick(FPS) / 1000
        hover_target = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key in action_presets:
                    scheduler.add_user_action(action_presets[event.key]())

        scheduler.trigger_random_events(dt, game_state)
        scheduler.assign_actions(characters, game_state)

        screen.fill(BACKGROUND_COLOR)
        campus_map.draw(screen)

        mouse_pos = pygame.Vector2(pygame.mouse.get_pos())
        for character in characters:
            character.update(dt)
            character.draw(screen)
            frame_rect = character.frame.get_rect(center=character.location.rect.center)
            if frame_rect.collidepoint(mouse_pos):
                hover_target = character

        if hover_target:
            hover_target.draw_hover_panel(screen, mouse_pos + pygame.Vector2(16, 16))

        draw_resource_panel(screen, game_state)
        draw_instructions(screen)
        draw_action_buffer(screen, scheduler.pending_action_names())

        pygame.display.flip()

    pygame.quit()


if __name__ == "__main__":
    main()
