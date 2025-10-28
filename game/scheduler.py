from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import List, Optional

from .actions import Action, ActionType
from .data_structures import CustomDeque, CustomQueue, PriorityQueue
from .map import CampusMap


@dataclass
class ResourceState:
    water: int = 0
    wood: int = 0
    food: int = 0
    minerals: int = 0


@dataclass
class GameState:
    day: int = 1
    hour: float = 8.0
    resources: ResourceState = field(default_factory=ResourceState)
    morale: float = 0.75
    alerts: List[str] = field(default_factory=list)

    def advance_time(self, dt_hours: float) -> None:
        self.hour += dt_hours
        if self.hour >= 24:
            self.day += 1
            self.hour = self.hour % 24

    def add_alert(self, message: str) -> None:
        self.alerts.append(message)
        if len(self.alerts) > 6:
            self.alerts.pop(0)


class TaskScheduler:
    def __init__(self, campus_map: CampusMap) -> None:
        self.campus_map = campus_map
        self.buffer = CustomQueue()
        self.priority_queue = PriorityQueue()
        self.available_characters = CustomDeque()
        self._known_available: set[int] = set()
        self._time_since_event = 0.0

    def register_characters(self, characters: List["Character"]) -> None:
        for character in characters:
            self.available_characters.push_back(character)
            self._known_available.add(id(character))

    def update_availability(self, characters: List["Character"]) -> None:
        for character in characters:
            if character.available and id(character) not in self._known_available:
                self.available_characters.push_back(character)
                self._known_available.add(id(character))
            elif not character.available and id(character) in self._known_available:
                # remove from deque by rebuilding
                temp = CustomDeque()
                while len(self.available_characters):
                    c = self.available_characters.pop_front()
                    if id(c) == id(character):
                        self._known_available.remove(id(c))
                        break
                    temp.push_back(c)
                while len(temp):
                    self.available_characters.push_front(temp.pop_back())

    def add_user_action(self, action: Action) -> None:
        self.buffer.enqueue(action)

    def promote_buffered_actions(self) -> None:
        while not self.buffer.is_empty():
            action = self.buffer.dequeue()
            priority = max(0.1, 5.0 - action.urgency)
            self.priority_queue.push(priority, action)

    def pending_action_names(self) -> List[str]:
        names = [action.name for action in self.buffer]
        names.extend(action.name for action in self.priority_queue.items())
        return names[:12]

    def assign_actions(self, characters: List["Character"], game_state: GameState) -> None:
        self.update_availability(characters)
        self.promote_buffered_actions()

        while len(self.available_characters) and len(self.priority_queue):
            character = self.available_characters.pop_front()
            self._known_available.discard(id(character))
            chosen_action = self.select_action_for_character(character, game_state)
            if chosen_action:
                character.assign_action(chosen_action)
            else:
                self.available_characters.push_back(character)
                self._known_available.add(id(character))
                break

    def select_action_for_character(self, character: "Character", game_state: GameState) -> Optional[Action]:
        candidates: List[Action] = []
        temp: List[Action] = []
        while len(self.priority_queue):
            action = self.priority_queue.pop()
            if character.compatible_with(action):
                candidates.append(action)
                break
            temp.append(action)

        for action in temp:
            self.priority_queue.push(2.5, action)

        if not candidates:
            return None

        action = candidates[0]
        urgency_modifier = max(0.5, action.urgency)
        morale_modifier = (1.0 - game_state.morale) * 2
        game_state.advance_time(action.duration / 2)
        morale_delta = 0.02 * urgency_modifier - 0.01 * morale_modifier
        game_state.morale = max(0.2, min(1.0, game_state.morale + morale_delta))

        self.apply_resource_changes(action, game_state)
        return action

    def apply_resource_changes(self, action: Action, game_state: GameState) -> None:
        if action.action_type == ActionType.GATHER_WATER:
            game_state.resources.water += 2
        elif action.action_type == ActionType.GATHER_WOOD:
            game_state.resources.wood += 2
        elif action.action_type == ActionType.MINE:
            game_state.resources.minerals += 2
        elif action.action_type == ActionType.SELL:
            game_state.resources.food += 1
        elif action.action_type == ActionType.EAT:
            game_state.resources.food = max(0, game_state.resources.food - 1)

    def trigger_random_events(self, dt: float, game_state: GameState) -> None:
        self._time_since_event += dt
        if self._time_since_event < 10.0:
            return
        self._time_since_event = 0.0
        event_type = random.choice(["lluvia", "incidente", "festival"])
        if event_type == "lluvia":
            action = Action(
                "Recolectar agua",
                ActionType.GATHER_WATER,
                "Entrada",
                duration=4.0,
                description="Lluvia repentina aumenta oportunidad de recolectar agua",
                urgency=0.8,
            )
            self.buffer.enqueue(action)
            game_state.add_alert("Lluvia: recolectar agua")
        elif event_type == "incidente":
            action = Action(
                "Defender campus",
                ActionType.DEFEND,
                "Fundadores",
                duration=3.5,
                description="Alerta de seguridad en el campus",
                urgency=0.4,
            )
            self.priority_queue.push(0.2, action)
            game_state.add_alert("Incidente de seguridad: ¡A defender!")
        elif event_type == "festival":
            action = Action(
                "Festival musical",
                ActionType.PERFORM,
                "Música",
                duration=5.0,
                description="Evento cultural que anima a los alumnos",
                urgency=1.2,
            )
            self.buffer.enqueue(action)
            game_state.add_alert("Festival musical en Música")


from typing import TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - avoid circular import at runtime
    from .characters import Character
