from __future__ import annotations

from typing import List

import pygame

from .actions import ActionType
from .scheduler import GameState
from .settings import DEFAULT_FONT, LARGE_FONT, PANEL_COLOR, SMALL_FONT, TEXT_COLOR


def draw_resource_panel(surface: pygame.Surface, game_state: GameState) -> None:
    panel_rect = pygame.Rect(960, 16, 220, 180)
    pygame.draw.rect(surface, PANEL_COLOR, panel_rect)
    pygame.draw.rect(surface, (255, 255, 255), panel_rect, 2)
    surface.blit(LARGE_FONT.render("UP Stats", True, TEXT_COLOR), (panel_rect.x + 12, panel_rect.y + 12))
    info_lines = [
        f"Día: {game_state.day}",
        f"Hora: {int(game_state.hour):02d}:{int((game_state.hour % 1) * 60):02d}",
        f"Ánimo: {int(game_state.morale * 100)}%",
        f"Agua: {game_state.resources.water}",
        f"Madera: {game_state.resources.wood}",
        f"Comida: {game_state.resources.food}",
        f"Minerales: {game_state.resources.minerals}",
    ]
    for idx, line in enumerate(info_lines):
        surface.blit(DEFAULT_FONT.render(line, True, TEXT_COLOR), (panel_rect.x + 12, panel_rect.y + 48 + idx * 24))

    alert_y = panel_rect.bottom + 12
    for alert in reversed(game_state.alerts):
        text_surface = SMALL_FONT.render(alert, True, TEXT_COLOR)
        bg_rect = text_surface.get_rect(topleft=(panel_rect.x, alert_y))
        pygame.draw.rect(surface, PANEL_COLOR, bg_rect.inflate(12, 8))
        pygame.draw.rect(surface, (255, 255, 255), bg_rect.inflate(12, 8), 1)
        surface.blit(text_surface, (panel_rect.x + 6, alert_y + 4))
        alert_y += text_surface.get_height() + 12


def draw_action_buffer(surface: pygame.Surface, pending_actions: List[str]) -> None:
    panel_rect = pygame.Rect(16, 620, 800, 80)
    pygame.draw.rect(surface, PANEL_COLOR, panel_rect)
    pygame.draw.rect(surface, (255, 255, 255), panel_rect, 2)
    surface.blit(DEFAULT_FONT.render("Buffer de acciones", True, TEXT_COLOR), (panel_rect.x + 12, panel_rect.y + 12))
    combined = ", ".join(pending_actions) or "(Vacío)"
    surface.blit(SMALL_FONT.render(combined, True, TEXT_COLOR), (panel_rect.x + 12, panel_rect.y + 44))


def draw_instructions(surface: pygame.Surface) -> None:
    instructions = [
        "Controles:",
        "1: Clases (Profesor)",
        "2: Estudiar (Alumno)",
        "3: Vender (Empleado)",
        "4: Visita Rector",
        "5: Recolectar Madera",
        "6: Minar",
        "7: Ejercicio",
        "8: Comer",
        "9: Construir",
        "0: Defender",
    ]
    for idx, line in enumerate(instructions):
        surface.blit(SMALL_FONT.render(line, True, TEXT_COLOR), (860, 320 + idx * 18))
