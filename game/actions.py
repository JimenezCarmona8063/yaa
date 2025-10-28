from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class ActionType(Enum):
    TEACH = auto()
    STUDY = auto()
    SELL = auto()
    VISIT = auto()
    EXERCISE = auto()
    EAT = auto()
    REST = auto()
    DEFEND = auto()
    BUILD = auto()
    GATHER_WATER = auto()
    GATHER_WOOD = auto()
    MINE = auto()
    PERFORM = auto()


@dataclass
class Action:
    name: str
    action_type: ActionType
    location: str
    duration: float
    required_role: Optional[str] = None
    description: str = ""
    urgency: float = 1.0

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Action(name={self.name!r}, type={self.action_type!r}, location={self.location!r})"
