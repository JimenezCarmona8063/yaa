from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Tuple

import pygame

from .settings import (
    MAP_COLUMNS,
    MAP_MARGIN,
    MAP_ROWS,
    TILE_SIZE,
    WALKWAY_BORDER_COLOR,
    WALKWAY_COLOR,
    SMALL_FONT,
)


@dataclass
class Location:
    name: str
    rect: pygame.Rect
    color: Tuple[int, int, int]
    description: str


class CampusMap:
    def __init__(self) -> None:
        self.locations: Dict[str, Location] = {}
        self._indices: Dict[str, Tuple[int, int]] = {}
        self.walkways: List[pygame.Rect] = []
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

        self.origin = pygame.Vector2(MAP_MARGIN, MAP_MARGIN)
        index = 0
        for row in range(MAP_ROWS):
            for col in range(MAP_COLUMNS):
                if index >= len(names):
                    break
                x = self.origin.x + col * TILE_SIZE
                y = self.origin.y + row * TILE_SIZE
                rect = pygame.Rect(x, y, TILE_SIZE - 8, TILE_SIZE - 8)
                color = palette[index % len(palette)]
                description = f"Zona de {names[index]}"
                self.locations[names[index]] = Location(names[index], rect, color, description)
                self._indices[names[index]] = (row, col)
                index += 1

        self._build_walkways()

    def draw(self, surface: pygame.Surface) -> None:
        for walkway in self.walkways:
            pygame.draw.rect(surface, WALKWAY_COLOR, walkway, border_radius=6)
            pygame.draw.rect(surface, WALKWAY_BORDER_COLOR, walkway, 2, border_radius=6)
        for location in self.locations.values():
            pygame.draw.rect(surface, location.color, location.rect)
            pygame.draw.rect(surface, WALKWAY_BORDER_COLOR, location.rect, 2)
            text = SMALL_FONT.render(location.name, True, (17, 17, 27))
            surface.blit(text, (location.rect.x + 6, location.rect.y + 4))

    def random_location(self) -> Location:
        import random

        return random.choice(list(self.locations.values()))

    def path_between(self, start_position: pygame.Vector2, destination: Location) -> List[pygame.Vector2]:
        path: List[pygame.Vector2] = []
        destination_center = pygame.Vector2(destination.rect.center)
        if start_position.distance_to(destination_center) <= 2:
            return path

        horizontal_target = pygame.Vector2(destination_center.x, start_position.y)
        if horizontal_target.distance_to(start_position) > 1:
            path.append(horizontal_target)
        if not path or path[-1].distance_to(destination_center) > 1:
            path.append(destination_center)
        return path

    def get_location(self, name: str) -> Location:
        return self.locations[name]

    def list_locations(self) -> List[str]:
        return list(self.locations.keys())

    def _build_walkways(self) -> None:
        walkway_thickness = 18
        map_width = MAP_COLUMNS * TILE_SIZE
        map_height = MAP_ROWS * TILE_SIZE

        for row in range(MAP_ROWS):
            center_y = self.origin.y + row * TILE_SIZE + (TILE_SIZE - 8) / 2
            rect = pygame.Rect(
                int(self.origin.x - 12),
                int(center_y - walkway_thickness / 2),
                int(map_width + 24),
                int(walkway_thickness),
            )
            self.walkways.append(rect)

        for col in range(MAP_COLUMNS):
            center_x = self.origin.x + col * TILE_SIZE + (TILE_SIZE - 8) / 2
            rect = pygame.Rect(
                int(center_x - walkway_thickness / 2),
                int(self.origin.y - 12),
                int(walkway_thickness),
                int(map_height + 24),
            )
            self.walkways.append(rect)
