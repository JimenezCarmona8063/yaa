from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import pygame

from .settings import MAP_COLUMNS, MAP_ROWS, TILE_SIZE


@dataclass
class Location:
    name: str
    rect: pygame.Rect
    color: Tuple[int, int, int]
    description: str


class CampusMap:
    def __init__(self) -> None:
        self.locations: Dict[str, Location] = {}
        self._build_layout()

    def _build_layout(self) -> None:
        palette = [
            (86, 101, 115),
            (118, 215, 196),
            (174, 214, 241),
            (241, 196, 15),
            (230, 126, 34),
            (155, 89, 182),
            (46, 134, 193),
            (244, 208, 63),
            (93, 173, 226),
            (84, 153, 199),
            (22, 160, 133),
            (236, 112, 99),
            (241, 148, 138),
            (39, 174, 96),
            (30, 132, 73),
        ]

        names = [
            "Entrada", "Fundadores", "Starbucks", "Caffenio", "Cafetería",
            "Oxxo", "TI", "Posgrados", "Gym", "Canchas", "Música",
            "Biblioteca", "Smart Center", "Ingenierías", "Civil", "Capilla",
        ]

        index = 0
        for row in range(MAP_ROWS):
            for col in range(MAP_COLUMNS):
                if index >= len(names):
                    break
                x = col * TILE_SIZE + 32
                y = row * TILE_SIZE + 32
                rect = pygame.Rect(x, y, TILE_SIZE - 8, TILE_SIZE - 8)
                color = palette[index % len(palette)]
                description = f"Zona de {names[index]}"
                self.locations[names[index]] = Location(names[index], rect, color, description)
                index += 1

    def draw(self, surface: pygame.Surface) -> None:
        for location in self.locations.values():
            pygame.draw.rect(surface, location.color, location.rect)
            pygame.draw.rect(surface, (33, 47, 60), location.rect, 2)

    def random_location(self) -> Location:
        import random

        return random.choice(list(self.locations.values()))

    def get_location(self, name: str) -> Location:
        return self.locations[name]

    def list_locations(self) -> List[str]:
        return list(self.locations.keys())
