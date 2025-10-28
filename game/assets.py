from __future__ import annotations

import random
from typing import Dict, List

import pygame

from .settings import TILE_SIZE


PALETTE = {
    "rector": [(199, 44, 65), (227, 120, 75), (217, 91, 67), (255, 205, 178)],
    "maestro": [(47, 72, 88), (33, 55, 86), (133, 193, 233), (46, 134, 193)],
    "empleado": [(88, 214, 141), (30, 132, 73), (27, 163, 156), (163, 228, 215)],
    "alumno": [(247, 220, 111), (244, 208, 63), (211, 84, 0), (242, 120, 75)],
    "alert": [(231, 76, 60), (192, 57, 43), (235, 152, 78), (236, 112, 99)],
}


def create_pixel_frame(color: tuple[int, int, int], accent: tuple[int, int, int]) -> pygame.Surface:
    surface = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
    surface.fill((0, 0, 0, 0))
    rect = pygame.Rect(8, 8, TILE_SIZE - 16, TILE_SIZE - 16)
    pygame.draw.rect(surface, color, rect)
    pygame.draw.rect(surface, accent, rect, 4)
    for _ in range(12):
        px = random.randint(rect.left + 2, rect.right - 4)
        py = random.randint(rect.top + 2, rect.bottom - 4)
        surface.set_at((px, py), accent)
    return surface


def build_animation_set(role: str, frame_count: int = 6) -> Dict[str, List[pygame.Surface]]:
    random.seed(42)
    colors = PALETTE.get(role, PALETTE["alumno"])
    base_frames = [
        create_pixel_frame(colors[i % len(colors)], colors[(i + 1) % len(colors)])
        for i in range(frame_count)
    ]

    animations: Dict[str, List[pygame.Surface]] = {
        "idle": base_frames,
        "walk": base_frames[::-1],
        "work": base_frames,
        "alert": [
            create_pixel_frame(PALETTE["alert"][i % len(PALETTE["alert"])], colors[i % len(colors)])
            for i in range(frame_count)
        ],
    }

    return animations
