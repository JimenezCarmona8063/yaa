from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import pygame

from .actions import Action, ActionType
from .assets import build_animation_set
from .map import CampusMap, Location
from .settings import HOVER_COLOR, SMALL_FONT, TEXT_COLOR


@dataclass
class CharacterState:
    has_eaten: bool = False
    has_exercised: bool = False
    gave_class: bool = False
    attended_class: bool = False
    bathed: bool = True
    studied: bool = False
    socialized: bool = False
    went_home: bool = False
    defended: bool = False
    built: bool = False
    mood: float = 0.7
    energy: float = 0.8


@dataclass
class Character:
    name: str
    role: str
    campus_map: CampusMap
    location: Location
    animations: Dict[str, List[pygame.Surface]] = field(default_factory=dict)
    state: CharacterState = field(default_factory=CharacterState)
    current_action: Optional[Action] = None
    action_timer: float = 0.0
    frame_index: float = 0.0
    animation: str = "idle"
    speed: float = 120.0
    available: bool = True
    alert: bool = False
    position: pygame.Vector2 = field(init=False)
    destination_location: Optional[Location] = field(default=None, init=False)
    path: List[pygame.Vector2] = field(default_factory=list, init=False)
    action_started: bool = field(default=False, init=False)
    wandering: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        if not self.animations:
            self.animations = build_animation_set(self.role)
        self.position = pygame.Vector2(self.location.rect.center)

    @property
    def frame(self) -> pygame.Surface:
        frames = self.animations.get(self.animation, self.animations["idle"])
        index = int(self.frame_index) % len(frames)
        return frames[index]

    @property
    def sprite_rect(self) -> pygame.Rect:
        return self.frame.get_rect(center=self.position)

    def assign_action(self, action: Action) -> None:
        self.current_action = action
        self.action_timer = action.duration
        self.available = False
        self.animation = "walk"
        self.frame_index = 0.0
        self.action_started = False
        self.wandering = False
        try:
            target = self.campus_map.get_location(action.location)
        except KeyError:
            self.destination_location = None
            self.path = []
            self.action_started = True
            self.animation = "work"
            return

        self.destination_location = target
        self.path = self.campus_map.path_between(self.position, target)
        if not self.path:
            self.location = target
            self.position = pygame.Vector2(target.rect.center)
            self.destination_location = None
            self.action_started = True
            self.animation = "work"

    def update(self, dt: float) -> None:
        self.frame_index += dt * 6
        if self.current_action:
            if not self.action_started:
                if self._move_towards_destination(dt):
                    return
                self.action_started = True
                self.animation = "work"
                self.frame_index = 0.0
            self.animation = "work"
            self.action_timer -= dt
            if self.action_timer <= 0:
                self.complete_action(self.current_action)
                self.current_action = None
                self.available = True
                self.animation = "idle"
        else:
            if self.path:
                self._move_towards_destination(dt)
            else:
                self.animation = "idle"
                if random.random() < 0.005:
                    self.begin_wander()

    def begin_wander(self) -> None:
        destination = self.campus_map.random_location()
        if destination == self.location:
            return
        self.destination_location = destination
        self.path = self.campus_map.path_between(self.position, destination)
        self.wandering = True
        if not self.path:
            self.location = destination
            self.position = pygame.Vector2(destination.rect.center)
            self.destination_location = None
            self.wandering = False

    def _move_towards_destination(self, dt: float) -> bool:
        if not self.path:
            self._finalize_arrival()
            return False

        target = self.path[0]
        direction = target - self.position
        distance = direction.length()
        max_step = self.speed * dt

        if distance <= max(1.0, max_step):
            self.position = target
            self.path.pop(0)
            if not self.path:
                self._finalize_arrival()
                return False
            return True

        if distance != 0:
            direction = direction.normalize()
        self.position += direction * max_step
        self.animation = "walk"
        return True

    def _finalize_arrival(self) -> None:
        if not self.destination_location:
            return
        destination_center = pygame.Vector2(self.destination_location.rect.center)
        if self.position.distance_to(destination_center) > 2:
            return
        self.position = destination_center
        self.location = self.destination_location
        self.destination_location = None
        if self.wandering:
            self.wandering = False
            self.animation = "idle"

    def draw(self, surface: pygame.Surface) -> None:
        frame = self.frame
        rect = frame.get_rect(center=self.position)
        surface.blit(frame, rect)

    def draw_hover_panel(self, surface: pygame.Surface, position: pygame.Vector2) -> None:
        info_lines = self.get_info_lines()
        width = 220
        height = 20 + len(info_lines) * 18
        panel_rect = pygame.Rect(position.x, position.y, width, height)
        pygame.draw.rect(surface, HOVER_COLOR, panel_rect)
        pygame.draw.rect(surface, (255, 255, 255), panel_rect, 2)
        surface.blit(SMALL_FONT.render(self.name, True, TEXT_COLOR), (panel_rect.x + 8, panel_rect.y + 4))
        for idx, line in enumerate(info_lines, start=1):
            surface.blit(
                SMALL_FONT.render(line, True, TEXT_COLOR),
                (panel_rect.x + 8, panel_rect.y + 4 + idx * 16),
            )

    def get_info_lines(self) -> List[str]:
        destination_text = ""
        if self.current_action and not self.action_started:
            if self.destination_location:
                destination_text = f"Destino: {self.destination_location.name}"
        elif self.destination_location and self.wandering:
            destination_text = f"Rumbo a: {self.destination_location.name}"
        else:
            destination_text = f"Ubicación: {self.location.name}"

        return [
            f"Rol: {self.role}",
            f"Acción: {self.current_action.name if self.current_action else 'Disponible'}",
            destination_text,
            f"Comido: {'Sí' if self.state.has_eaten else 'No'}",
            f"Ejercicio: {'Sí' if self.state.has_exercised else 'No'}",
            f"Ánimo: {int(self.state.mood * 100)}%",
            f"Energía: {int(self.state.energy * 100)}%",
        ]

    def compatible_with(self, action: Action) -> bool:
        if action.required_role and action.required_role != self.role:
            return False
        return True

    def completion_effects(self, action: Action) -> None:
        if action.action_type == ActionType.EAT:
            self.state.has_eaten = True
            self.state.energy = min(1.0, self.state.energy + 0.2)
        elif action.action_type == ActionType.EXERCISE:
            self.state.has_exercised = True
            self.state.mood = min(1.0, self.state.mood + 0.15)
        elif action.action_type == ActionType.REST:
            self.state.energy = min(1.0, self.state.energy + 0.3)
        elif action.action_type == ActionType.DEFEND:
            self.state.defended = True
            self.alert = False
        elif action.action_type == ActionType.BUILD:
            self.state.built = True
        elif action.action_type == ActionType.TEACH:
            self.state.gave_class = True
        elif action.action_type == ActionType.STUDY:
            self.state.studied = True
            self.state.attended_class = True
        elif action.action_type == ActionType.SELL:
            self.state.socialized = True
        elif action.action_type == ActionType.VISIT:
            self.state.socialized = True

        self.state.energy = max(0.2, self.state.energy - 0.1)
        self.state.mood = max(0.1, self.state.mood - 0.05)

    def complete_action(self, action: Action) -> None:
        self.completion_effects(action)


class Rector(Character):
    def compatible_with(self, action: Action) -> bool:
        if not super().compatible_with(action):
            return False
        return action.action_type in {
            ActionType.VISIT,
            ActionType.DEFEND,
            ActionType.BUILD,
            ActionType.EAT,
        }

    def get_info_lines(self) -> List[str]:
        lines = super().get_info_lines()
        lines.append("Visitas completadas" if self.state.socialized else "Pendiente visitar")
        return lines

    def completion_effects(self, action: Action) -> None:
        super().completion_effects(action)
        if action.action_type == ActionType.VISIT:
            self.state.socialized = True


class Maestro(Character):
    materias: List[str] = field(default_factory=list)  # type: ignore[assignment]

    def compatible_with(self, action: Action) -> bool:
        if not super().compatible_with(action):
            return False
        return action.action_type in {
            ActionType.TEACH,
            ActionType.EAT,
            ActionType.REST,
            ActionType.EXERCISE,
            ActionType.DEFEND,
        }

    def completion_effects(self, action: Action) -> None:
        super().completion_effects(action)
        if action.action_type == ActionType.TEACH:
            self.state.gave_class = True


class Empleado(Character):
    def compatible_with(self, action: Action) -> bool:
        if not super().compatible_with(action):
            return False
        return action.action_type in {
            ActionType.SELL,
            ActionType.GATHER_WATER,
            ActionType.GATHER_WOOD,
            ActionType.MINE,
            ActionType.EAT,
            ActionType.DEFEND,
            ActionType.BUILD,
        }

    def completion_effects(self, action: Action) -> None:
        super().completion_effects(action)
        if action.action_type == ActionType.SELL:
            self.state.socialized = True


class Alumno(Character):
    def compatible_with(self, action: Action) -> bool:
        if not super().compatible_with(action):
            return False
        return action.action_type in {
            ActionType.STUDY,
            ActionType.EXERCISE,
            ActionType.REST,
            ActionType.EAT,
            ActionType.PERFORM,
            ActionType.DEFEND,
        }

    def completion_effects(self, action: Action) -> None:
        super().completion_effects(action)
        if action.action_type == ActionType.STUDY:
            self.state.attended_class = True


def create_initial_characters(campus_map: CampusMap) -> List[Character]:
    names = {
        "rector": ["Antonio"],
        "maestro": ["Dávalos", "Tachiquín", "Martha", "Isaac", "Fabiola"],
        "empleado": ["Contador", "Director", "Barista", "Oxxo"],
        "alumno": ["Alex", "Sofía", "Luis", "María"],
    }

    characters: List[Character] = []
    for role, role_names in names.items():
        for person in role_names:
            location = campus_map.random_location()
            if role == "rector":
                characters.append(Rector(person, role, campus_map, location))
            elif role == "maestro":
                characters.append(Maestro(person, role, campus_map, location))
            elif role == "empleado":
                characters.append(Empleado(person, role, campus_map, location))
            else:
                characters.append(Alumno(person, role, campus_map, location))
    return characters
