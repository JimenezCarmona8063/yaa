from __future__ import annotations

"""Simulador TACHI con lógica y visualización interactiva en pygame.

Este script contiene toda la lógica necesaria para representar el proyecto
TACHI sin depender de módulos adicionales. Puede abrirse y modificarse
como un solo archivo y, aun así, reutilizarse como módulo importable. Incluye:

* Un mapa estilo pixel art que puede renderizarse en ASCII o en una ventana
  de pygame.
* Clases para personajes (rector, maestros, alumnos y empleados) con paneles
  de control que muestran el estado de sus actividades.
* Estructuras de datos basadas en colas (FIFO) y colas de prioridad que
  permiten planificar y atender tareas de acuerdo con su urgencia.
* Una interfaz :class:`PygameSimulator` que permite elegir personajes, atender
  actividades y mostrar la información al colocar el cursor sobre cada avatar.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
import math
import random
from typing import Dict, Iterable, Iterator, List, Optional, Sequence, Tuple


# ---------------------------------------------------------------------------
#  Estructuras de datos personalizadas
# ---------------------------------------------------------------------------


class LinkedListNode:
    __slots__ = ("value", "next")

    def __init__(self, value: str) -> None:
        self.value = value
        self.next: Optional[LinkedListNode] = None


class LinkedList:
    """Lista enlazada simple utilizada para la bitácora del simulador."""

    def __init__(self, max_length: int = 12) -> None:
        self.head: Optional[LinkedListNode] = None
        self.tail: Optional[LinkedListNode] = None
        self._size = 0
        self._max = max_length

    def appendleft(self, value: str) -> None:
        node = LinkedListNode(value)
        node.next = self.head
        self.head = node
        if self.tail is None:
            self.tail = node
        self._size += 1
        while self._size > self._max and self.tail:
            self._remove_last()

    def _remove_last(self) -> None:
        if self.head is None:
            return
        if self.head == self.tail:
            self.head = self.tail = None
            self._size = 0
            return
        prev = self.head
        while prev.next and prev.next != self.tail:
            prev = prev.next
        prev.next = None
        self.tail = prev
        self._size -= 1

    def __iter__(self) -> Iterator[str]:
        current = self.head
        while current:
            yield current.value
            current = current.next


class Queue:
    """Cola FIFO implementada manualmente."""

    def __init__(self) -> None:
        self._items: List[object] = []
        self._start = 0

    def push(self, item: object) -> None:
        self._items.append(item)

    def pop(self) -> Optional[object]:
        if self._start >= len(self._items):
            return None
        item = self._items[self._start]
        self._start += 1
        if self._start > 32 and self._start * 2 >= len(self._items):
            self._items = self._items[self._start :]
            self._start = 0
        return item

    def __len__(self) -> int:
        return len(self._items) - self._start

    def __iter__(self) -> Iterator[object]:
        return iter(self._items[self._start :])


class Deque:
    """Deque circular para rotar disponibilidades."""

    def __init__(self) -> None:
        self._items: List[object] = []

    def push_back(self, item: object) -> None:
        self._items.append(item)

    def pop_front(self) -> Optional[object]:
        if not self._items:
            return None
        return self._items.pop(0)

    def rotate(self) -> None:
        if self._items:
            self._items.append(self._items.pop(0))

    def __iter__(self) -> Iterator[object]:
        return iter(self._items)


class MinHeap:
    """Implementación básica de un heap binario mínimo."""

    def __init__(self) -> None:
        self._data: List[object] = []

    def push(self, item: object) -> None:
        self._data.append(item)
        self._sift_up(len(self._data) - 1)

    def pop(self) -> Optional[object]:
        if not self._data:
            return None
        if len(self._data) == 1:
            return self._data.pop()
        top = self._data[0]
        self._data[0] = self._data.pop()
        self._sift_down(0)
        return top

    def __len__(self) -> int:
        return len(self._data)

    def _sift_up(self, idx: int) -> None:
        while idx > 0:
            parent = (idx - 1) // 2
            if self._data[idx] < self._data[parent]:
                self._data[idx], self._data[parent] = self._data[parent], self._data[idx]
                idx = parent
            else:
                break

    def _sift_down(self, idx: int) -> None:
        size = len(self._data)
        while True:
            left = 2 * idx + 1
            right = 2 * idx + 2
            smallest = idx
            if left < size and self._data[left] < self._data[smallest]:
                smallest = left
            if right < size and self._data[right] < self._data[smallest]:
                smallest = right
            if smallest == idx:
                break
            self._data[idx], self._data[smallest] = self._data[smallest], self._data[idx]
            idx = smallest

    def __iter__(self) -> Iterator[object]:
        return iter(sorted(self._data))


# ---------------------------------------------------------------------------
#  Mapa tipo "pixel art"
# ---------------------------------------------------------------------------


_MAP_TILES: Tuple[Tuple[str, ...], ...] = (
    ("STA", "CAF", "FUN", "ENT", "OXX", "BIB", "GYM"),
    ("TI ", "SC ", "ING", "POS", "MUS", "CAN", "CIV"),
    ("CAF", "OXO", "CAF", "LIB", "DIR", "ADM", "PRO"),
    ("RES", "ASO", "COM", "DEP", "MUS", "LAB", "UP "),
)


_TILE_DESCRIPTIONS: Dict[str, str] = {
    "STA": "Starbucks",
    "CAF": "Cafetería",
    "FUN": "Fundadores",
    "ENT": "Entrada",
    "OXX": "Oxxo",
    "BIB": "Biblioteca",
    "GYM": "Gimnasio",
    "TI": "TI",
    "SC": "Smart Center",
    "ING": "Ingenierías",
    "POS": "Posgrados",
    "MUS": "Música",
    "CAN": "Canchas",
    "CIV": "Civil",
    "OXO": "Oxxo (anexo)",
    "LIB": "Librería",
    "DIR": "Dirección",
    "ADM": "Administración",
    "PRO": "Proveedores",
    "RES": "Residencias",
    "ASO": "Asesorías",
    "COM": "Comedor",
    "DEP": "Deportes",
    "LAB": "Laboratorios",
    "UP": "Rectoría UP",
}


def _normalized_tile_name(tile: str) -> str:
    return tile.strip().upper()


def campus_tiles() -> Tuple[Tuple[str, ...], ...]:
    return _MAP_TILES


def render_pixel_map() -> str:
    ancho = len(_MAP_TILES[0])
    borde = "#" * (ancho * 4 + 1)
    filas = [borde]
    for fila in _MAP_TILES:
        contenido = "#".join(tile for tile in fila)
        filas.append(f"#{contenido}#")
    filas.append(borde)
    return "\n".join(filas)


def tile_locations() -> Dict[str, Tuple[int, int]]:
    ubicaciones: Dict[str, Tuple[int, int]] = {}
    for y, fila in enumerate(_MAP_TILES):
        for x, tile in enumerate(fila):
            nombre = _normalized_tile_name(tile)
            if nombre and nombre not in ubicaciones:
                ubicaciones[nombre] = (x, y)
    return ubicaciones


# ---------------------------------------------------------------------------
#  Actividades y planificador
# ---------------------------------------------------------------------------


class ActivityCategory(Enum):
    ACADEMICA = auto()
    SOCIAL = auto()
    SALUD = auto()
    OPERATIVA = auto()
    DEFENSA = auto()


@dataclass(order=True)
class Activity:
    priority: float
    nombre: str = field(compare=False)
    ubicacion: str = field(compare=False)
    duracion: float = field(compare=False)
    categoria: ActivityCategory = field(compare=False)
    required_role: Optional[str] = field(compare=False, default=None)


class ActionBuffer(Queue):
    """Cola de acciones solicitadas por el usuario."""


class AvailabilityDeque(Deque):
    """Gestiona la rotación de personajes disponibles."""


class PriorityActivityQueue(MinHeap):
    def push_activity(self, activity: Activity) -> None:
        self.push(activity)

    def pop_activity(self) -> Optional[Activity]:
        top = self.pop()
        return top if isinstance(top, Activity) else None


# ---------------------------------------------------------------------------
#  Personajes y herencia
# ---------------------------------------------------------------------------


DEFAULT_NEEDS: Tuple[str, ...] = (
    "ha_comido",
    "ha_hecho_ejercicio",
    "ya_dio_clase",
    "ya_fue_a_clases",
    "ya_se_baño",
    "tuvo_examenes",
    "tiene_examenes",
    "hablo_con_amigos",
    "fue_a_asesorias",
    "ya_se_va_a_casa",
    "ya_estudio",
)


@dataclass
class CampusCharacter:
    nombre: str
    rol: str
    ubicacion: str
    velocidad: float = 110.0
    needs: Dict[str, bool] = field(default_factory=lambda: {n: False for n in DEFAULT_NEEDS})
    prioridades: PriorityActivityQueue = field(default_factory=PriorityActivityQueue)
    rutina: Queue = field(default_factory=Queue)
    estado: str = "disponible"
    _path: List[Tuple[int, int]] = field(default_factory=list)
    _position: Tuple[float, float] = field(default_factory=lambda: (0.0, 0.0))
    _animation_timer: float = 0.0
    _animation_index: int = 0
    _current_activity: Optional[Activity] = None
    _progress: float = 0.0

    def __post_init__(self) -> None:
        self._position = (0.0, 0.0)

    # --- Gestión de actividades -------------------------------------------------
    def schedule_activity(self, activity: Activity) -> None:
        if activity.priority <= 1.0:
            self.prioridades.push_activity(activity)
        else:
            self.rutina.push(activity)

    def next_activity(self) -> Optional[Activity]:
        actividad = self.prioridades.pop_activity()
        if actividad is None:
            siguiente = self.rutina.pop()
            if isinstance(siguiente, Activity):
                actividad = siguiente
        if isinstance(actividad, Activity):
            return actividad
        return None

    # --- Movimiento -------------------------------------------------------------
    def set_position(self, pos: Tuple[float, float]) -> None:
        self._position = pos

    def position(self) -> Tuple[float, float]:
        return self._position

    def assign_path(self, path: Sequence[Tuple[int, int]]) -> None:
        self._path = list(path)
        if len(self._path) > 1:
            # el primer nodo es la casilla actual; se elimina para evitar rebotes
            self._path.pop(0)
        if self._path:
            self.estado = "en_ruta"
        else:
            self.estado = "ocupado"

    # --- Actualización ----------------------------------------------------------
    def update(self, dt: float, grid: "CampusGrid") -> None:
        self._animation_timer += dt
        if self._animation_timer >= 0.12:  # al menos ~8 fps
            self._animation_index = (self._animation_index + 1) % 6
            self._animation_timer = 0.0

        if self.estado == "en_ruta":
            self._advance_path(dt, grid)
        elif self.estado == "ocupado" and self._current_activity:
            self._progress += dt
            if self._progress >= self._current_activity.duracion:
                self._finish_activity()

    def _advance_path(self, dt: float, grid: "CampusGrid") -> None:
        if not self._path:
            self.estado = "ocupado"
            return
        target_tile = self._path[0]
        target_pos = grid.tile_center(*target_tile)
        x, y = self._position
        tx, ty = target_pos
        dx = tx - x
        dy = ty - y
        distance = math.hypot(dx, dy)
        if distance < 1.0:
            self._position = target_pos
            self._path.pop(0)
            if not self._path:
                self.estado = "ocupado"
        else:
            direction = (dx / distance, dy / distance)
            step = self.velocidad * dt
            self._position = (x + direction[0] * step, y + direction[1] * step)

    def start_activity(self, activity: Activity) -> None:
        self._current_activity = activity
        self._progress = 0.0
        self.ubicacion = activity.ubicacion
        if not self._path:
            self.estado = "ocupado"

    def _finish_activity(self) -> None:
        if self._current_activity:
            nombre = self._current_activity.nombre
            if nombre == "Ir a comer":
                self.needs["ha_comido"] = True
            elif nombre == "Entrenamiento":
                self.needs["ha_hecho_ejercicio"] = True
            elif "clase" in nombre.lower():
                self.needs["ya_dio_clase"] = True
            self._current_activity = None
        self.estado = "disponible"

    # --- Visualización ----------------------------------------------------------
    def sprite_color(self) -> Tuple[int, int, int]:
        return 255, 255, 255

    def control_panel(self) -> Dict[str, object]:
        return {
            "nombre": self.nombre,
            "rol": self.rol,
            "ubicacion": _TILE_DESCRIPTIONS.get(self.ubicacion, self.ubicacion),
            "estado": self.estado,
            "actividad": self._current_activity.nombre if self._current_activity else None,
            "necesidades": self.needs.copy(),
            "prioritarias": [a.nombre for a in self.prioridades],
            "rutinarias": [a.nombre for a in self.rutina],
        }


class Rector(CampusCharacter):
    def sprite_color(self) -> Tuple[int, int, int]:
        return 255, 234, 167


class Maestro(CampusCharacter):
    def sprite_color(self) -> Tuple[int, int, int]:
        return 9, 132, 227


class Alumno(CampusCharacter):
    def sprite_color(self) -> Tuple[int, int, int]:
        return 232, 67, 147


class Empleado(CampusCharacter):
    def sprite_color(self) -> Tuple[int, int, int]:
        return 0, 184, 148


CharacterType = CampusCharacter


def create_character(nombre: str, tipo: str, ubicacion: str) -> CampusCharacter:
    mapping = {
        "rector": Rector,
        "maestro": Maestro,
        "alumno": Alumno,
        "empleado": Empleado,
    }
    cls = mapping.get(tipo.lower(), CampusCharacter)
    personaje = cls(nombre=nombre, rol=tipo.lower(), ubicacion=_normalized_tile_name(ubicacion))
    return personaje


def default_characters(grid: "CampusGrid") -> List[CampusCharacter]:
    personajes = [
        create_character("Antonio", "rector", "ADM"),
        create_character("D\u00e1valos", "maestro", "ING"),
        create_character("Martha", "alumno", "BIB"),
        create_character("Fabiola", "empleado", "CAF"),
    ]
    for personaje in personajes:
        personaje.set_position(grid.tile_center(*grid.tile_of(personaje.ubicacion)))
    return personajes


# ---------------------------------------------------------------------------
#  Mapa navegable para pygame
# ---------------------------------------------------------------------------


class CampusGrid:
    TILE_SIZE = 96
    PADDING = 12

    TILE_COLORS: Dict[str, Tuple[int, int, int]] = {
        "STA": (108, 92, 231),
        "CAF": (214, 162, 232),
        "FUN": (255, 159, 243),
        "ENT": (129, 236, 236),
        "OXX": (250, 177, 160),
        "BIB": (116, 185, 255),
        "GYM": (85, 239, 196),
        "TI": (255, 118, 117),
        "SC": (253, 121, 168),
        "ING": (223, 230, 233),
        "POS": (178, 190, 195),
        "MUS": (253, 203, 110),
        "CAN": (0, 184, 148),
        "CIV": (108, 92, 231),
        "OXO": (250, 177, 160),
        "LIB": (116, 185, 255),
        "DIR": (9, 132, 227),
        "ADM": (0, 184, 148),
        "PRO": (0, 206, 201),
        "RES": (232, 67, 147),
        "ASO": (225, 112, 85),
        "COM": (214, 162, 232),
        "DEP": (85, 239, 196),
        "LAB": (45, 52, 54),
        "UP": (253, 203, 110),
    }

    def __init__(self) -> None:
        self._tiles = campus_tiles()
        self._lookup = tile_locations()

    # --- geometría -------------------------------------------------------------
    def map_size(self) -> Tuple[int, int]:
        width = len(self._tiles[0]) * self.TILE_SIZE + self.PADDING * 2
        height = len(self._tiles) * self.TILE_SIZE + self.PADDING * 2
        return width, height

    def tile_rect(self, x: int, y: int) -> Tuple[int, int, int, int]:
        return (
            self.PADDING + x * self.TILE_SIZE,
            self.PADDING + y * self.TILE_SIZE,
            self.TILE_SIZE,
            self.TILE_SIZE,
        )

    def tile_center(self, x: int, y: int) -> Tuple[float, float]:
        rect = self.tile_rect(x, y)
        return rect[0] + rect[2] / 2, rect[1] + rect[3] / 2

    def tile_of(self, tile_name: str) -> Tuple[int, int]:
        tile = self._lookup.get(_normalized_tile_name(tile_name))
        if not tile:
            raise KeyError(f"Zona desconocida: {tile_name}")
        return tile

    # --- pathfinding -----------------------------------------------------------
    def neighbors(self, x: int, y: int) -> Iterable[Tuple[int, int]]:
        width = len(self._tiles[0])
        height = len(self._tiles)
        for nx, ny in ((x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)):
            if 0 <= nx < width and 0 <= ny < height:
                yield nx, ny

    def find_path(self, start: Tuple[int, int], goal: Tuple[int, int]) -> List[Tuple[int, int]]:
        if start == goal:
            return [goal]
        frontier: Queue = Queue()
        frontier.push(start)
        came_from: Dict[Tuple[int, int], Optional[Tuple[int, int]]] = {start: None}
        while len(frontier) > 0:
            current = frontier.pop()
            if not isinstance(current, tuple):
                continue
            if current == goal:
                break
            for neighbor in self.neighbors(*current):
                if neighbor not in came_from:
                    came_from[neighbor] = current
                    frontier.push(neighbor)
        path: List[Tuple[int, int]] = []
        node: Optional[Tuple[int, int]] = goal
        while node:
            path.append(node)
            node = came_from.get(node)
        path.reverse()
        return path

    # --- dibujo ----------------------------------------------------------------
    def draw(self, surface, font) -> None:
        import pygame

        for y, row in enumerate(self._tiles):
            for x, tile in enumerate(row):
                rect = pygame.Rect(*self.tile_rect(x, y))
                name = _normalized_tile_name(tile)
                color = self.TILE_COLORS.get(name, (99, 110, 114))
                pygame.draw.rect(surface, color, rect)
                pygame.draw.rect(surface, (36, 40, 60), rect, 2)
                if font:
                    label = font.render(_TILE_DESCRIPTIONS.get(name, name), True, (14, 16, 26))
                    label_rect = label.get_rect(center=rect.center)
                    surface.blit(label, label_rect)


# ---------------------------------------------------------------------------
#  Planificador de acciones
# ---------------------------------------------------------------------------


class TaskPlanner:
    """Planificador basado en heap que asigna actividades a los personajes."""

    def __init__(self, personajes: Sequence[CampusCharacter], grid: CampusGrid) -> None:
        self.buffer = ActionBuffer()
        self.heap = PriorityActivityQueue()
        self.available = AvailabilityDeque()
        for personaje in personajes:
            self.available.push_back(personaje)
        self.grid = grid
        self.random_timer = 0.0

    def enqueue(self, activity: Activity) -> None:
        self.buffer.push(activity)

    def trigger_random_events(self, dt: float) -> Optional[str]:
        self.random_timer += dt
        if self.random_timer < 12.0:
            return None
        self.random_timer = 0.0
        choices = [
            Activity(0.4, "Alerta de defensa", "ENT", 3.0, ActivityCategory.DEFENSA),
            Activity(0.8, "Festival musical", "MUS", 4.0, ActivityCategory.SOCIAL),
            Activity(0.6, "Entrega de proveedores", "PRO", 3.5, ActivityCategory.OPERATIVA, "empleado"),
        ]
        evento = random.choice(choices)
        self.heap.push_activity(evento)
        return f"Evento inesperado: {evento.nombre} en {_TILE_DESCRIPTIONS.get(evento.ubicacion, evento.ubicacion)}"

    def distribute(self) -> List[str]:
        mensajes: List[str] = []
        while len(self.buffer) > 0:
            item = self.buffer.pop()
            if isinstance(item, Activity):
                self.heap.push_activity(item)
        for personaje in list(self.available):
            if personaje.estado != "disponible":
                continue
            actividad = self.heap.pop_activity() or personaje.next_activity()
            if not actividad:
                continue
            if actividad.required_role and actividad.required_role != personaje.rol:
                self.heap.push_activity(actividad)
                continue
            self._assign_activity(personaje, actividad)
            mensajes.append(f"{personaje.nombre} atender\u00e1 {actividad.nombre}")
            self.available.rotate()
        return mensajes

    def _assign_activity(self, personaje: CampusCharacter, actividad: Activity) -> None:
        destino = self.grid.tile_of(actividad.ubicacion)
        inicio = self.grid.tile_of(personaje.ubicacion)
        path = self.grid.find_path(inicio, destino)
        personaje.assign_path(path)
        personaje.start_activity(actividad)


# ---------------------------------------------------------------------------
#  Interfaz pygame
# ---------------------------------------------------------------------------


class PygameSimulator:
    BACKGROUND_COLOR = (14, 16, 26)
    PANEL_BACKGROUND = (22, 24, 38)
    PANEL_TEXT = (240, 240, 240)
    PANEL_SUBTEXT = (190, 200, 210)
    SELECTION_COLOR = (255, 235, 97)
    PANEL_WIDTH = 360

    def __init__(self, *, characters: Optional[List[CampusCharacter]] = None, grid: Optional[CampusGrid] = None) -> None:
        self.grid = grid or CampusGrid()
        self.characters = characters or default_characters(self.grid)
        self.font_small = None
        self.font_regular = None
        self.log = LinkedList()
        self.planner = TaskPlanner(self.characters, self.grid)
        self.hover: Optional[CampusCharacter] = None
        self.selected: CampusCharacter = self.characters[0]
        self._prepare_initial_tasks()

    def _prepare_initial_tasks(self) -> None:
        for personaje in self.characters:
            if personaje.rol == "rector":
                personaje.schedule_activity(Activity(0.5, "Supervisar facultades", "DIR", 4.0, ActivityCategory.OPERATIVA))
            elif personaje.rol == "maestro":
                personaje.schedule_activity(Activity(0.6, "Dar clase de estructuras", "ING", 3.5, ActivityCategory.ACADEMICA, "maestro"))
                personaje.schedule_activity(Activity(1.1, "Asesor\u00eda estudiantil", "SC", 2.5, ActivityCategory.ACADEMICA))
            elif personaje.rol == "alumno":
                personaje.schedule_activity(Activity(0.7, "Asistir a clase", "ING", 3.0, ActivityCategory.ACADEMICA))
                personaje.schedule_activity(Activity(1.4, "Practicar deporte", "CAN", 2.0, ActivityCategory.SALUD))
            elif personaje.rol == "empleado":
                personaje.schedule_activity(Activity(0.5, "Abrir el Oxxo", "OXX", 2.5, ActivityCategory.OPERATIVA, "empleado"))
                personaje.schedule_activity(Activity(0.9, "Recibir proveedores", "PRO", 3.0, ActivityCategory.OPERATIVA, "empleado"))

    # --- ciclo principal -------------------------------------------------------
    def run(self) -> None:
        import pygame

        pygame.init()
        pygame.font.init()

        map_width, map_height = self.grid.map_size()
        window = pygame.display.set_mode((map_width + self.PANEL_WIDTH, map_height))
        pygame.display.set_caption("Simulador TACHI - Campus UP")

        clock = pygame.time.Clock()
        self.font_small = pygame.font.SysFont("arial", 18)
        self.font_regular = pygame.font.SysFont("arial", 20)

        running = True
        while running:
            dt = clock.tick(60) / 1000.0
            self.hover = None

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        running = False
                    else:
                        self._handle_key(event.key)

            self._update(dt)

            window.fill(self.BACKGROUND_COLOR)
            self.grid.draw(window, self.font_small)
            self._draw_characters(window)
            self._draw_panel(window, map_width)
            pygame.display.flip()

        pygame.quit()

    def _handle_key(self, key: int) -> None:
        import pygame

        shortcuts = {
            pygame.K_1: self.characters[0],
            pygame.K_2: self.characters[1],
            pygame.K_3: self.characters[2],
            pygame.K_4: self.characters[3],
        }
        if key in shortcuts:
            self.selected = shortcuts[key]
            return

        presets = {
            pygame.K_q: Activity(0.7, "Construir aula", "FUN", 3.5, ActivityCategory.OPERATIVA),
            pygame.K_w: Activity(0.9, "Ir a comer", "CAF", 2.0, ActivityCategory.SALUD),
            pygame.K_e: Activity(1.2, "Estudiar en biblioteca", "BIB", 3.0, ActivityCategory.ACADEMICA, "alumno"),
            pygame.K_r: Activity(1.0, "Entrenamiento", "GYM", 2.5, ActivityCategory.SALUD),
            pygame.K_t: Activity(0.6, "Visita del rector", "UP", 3.0, ActivityCategory.OPERATIVA, "rector"),
            pygame.K_y: Activity(1.3, "Reparar laboratorio", "LAB", 4.0, ActivityCategory.OPERATIVA, "empleado"),
        }
        activity = presets.get(key)
        if activity:
            self.planner.enqueue(activity)
            self.log.appendleft(f"Actividad solicitada: {activity.nombre}")

    def _update(self, dt: float) -> None:
        import pygame

        event_msg = self.planner.trigger_random_events(dt)
        if event_msg:
            self.log.appendleft(event_msg)
        for mensaje in self.planner.distribute():
            self.log.appendleft(mensaje)

        for personaje in self.characters:
            personaje.update(dt, self.grid)

        mouse_pos = pygame.mouse.get_pos()
        for personaje in self.characters:
            px, py = personaje.position()
            radius = self.grid.TILE_SIZE // 3
            if (mouse_pos[0] - px) ** 2 + (mouse_pos[1] - py) ** 2 <= radius ** 2:
                self.hover = personaje
        if self.hover:
            self.selected = self.hover

    def _draw_characters(self, surface) -> None:
        import pygame

        for personaje in self.characters:
            px, py = personaje.position()
            color = personaje.sprite_color()
            radius = self.grid.TILE_SIZE // 3
            pygame.draw.circle(surface, color, (int(px), int(py)), radius)
            outline = 4 if personaje is self.selected else 2
            pygame.draw.circle(surface, self.SELECTION_COLOR, (int(px), int(py)), radius + outline, 2)
            # animación simple de 6 frames basada en índice
            if self.font_small:
                estado = personaje.estado
                if estado == "en_ruta":
                    dots = "".join(("·" if i <= personaje._animation_index else " " ) for i in range(6))
                    label = self.font_small.render(dots, True, (36, 40, 60))
                    surface.blit(label, (int(px) - radius, int(py) - radius - 18))

    def _draw_panel(self, surface, map_width: int) -> None:
        import pygame

        rect = pygame.Rect(map_width, 0, self.PANEL_WIDTH, surface.get_height())
        pygame.draw.rect(surface, self.PANEL_BACKGROUND, rect)
        pygame.draw.rect(surface, (36, 40, 60), rect, 2)

        personaje = self.selected
        if self.font_regular:
            title = f"{personaje.nombre} ({personaje.rol})"
            surface.blit(self.font_regular.render(title, True, self.PANEL_TEXT), (rect.x + 16, rect.y + 16))

        y = rect.y + 56
        if self.font_small:
            ubic = _TILE_DESCRIPTIONS.get(personaje.ubicacion, personaje.ubicacion)
            surface.blit(self.font_small.render(f"Ubicación: {ubic}", True, self.PANEL_SUBTEXT), (rect.x + 16, y))
            y += 26
            surface.blit(self.font_small.render(f"Estado: {personaje.estado}", True, self.PANEL_SUBTEXT), (rect.x + 16, y))
            y += 26
            actividad = personaje._current_activity.nombre if personaje._current_activity else "Ninguna"
            surface.blit(self.font_small.render(f"Actividad: {actividad}", True, self.PANEL_SUBTEXT), (rect.x + 16, y))
            y += 32
            surface.blit(self.font_small.render("Necesidades:", True, self.PANEL_TEXT), (rect.x + 16, y))
            y += 24
            for nombre, cumplida in personaje.needs.items():
                estado = "✓" if cumplida else "✗"
                texto = f"{estado} {nombre.replace('_', ' ')}"
                surface.blit(self.font_small.render(texto, True, self.PANEL_SUBTEXT), (rect.x + 20, y))
                y += 20
                if y > rect.bottom - 180:
                    break

            y += 8
            surface.blit(self.font_small.render("Actividades en espera:", True, self.PANEL_TEXT), (rect.x + 16, y))
            y += 24
            for actividad in personaje.prioridades:
                surface.blit(self.font_small.render(f"• {actividad.nombre}", True, self.PANEL_SUBTEXT), (rect.x + 20, y))
                y += 20
            for actividad in personaje.rutina:
                if isinstance(actividad, Activity):
                    surface.blit(self.font_small.render(f"• {actividad.nombre}", True, self.PANEL_SUBTEXT), (rect.x + 20, y))
                    y += 20

            y = rect.bottom - 200
            surface.blit(self.font_small.render("Bitácora:", True, self.PANEL_TEXT), (rect.x + 16, y))
            y += 24
            for entrada in self.log:
                surface.blit(self.font_small.render(entrada, True, self.PANEL_SUBTEXT), (rect.x + 16, y))
                y += 20
                if y > rect.bottom - 32:
                    break

            instrucciones = [
                "1-4: seleccionar personaje",
                "Q-Y: agregar actividades",
                "Cursor: panel contextual",
                "ESC: salir",
            ]
            y = rect.bottom - 120
            for texto in instrucciones:
                surface.blit(self.font_small.render(texto, True, self.PANEL_SUBTEXT), (rect.x + 16, y))
                y += 22


# ---------------------------------------------------------------------------
#  API pública
# ---------------------------------------------------------------------------


__all__ = [
    "Activity",
    "ActivityCategory",
    "ActionBuffer",
    "AvailabilityDeque",
    "CampusCharacter",
    "CampusGrid",
    "LinkedList",
    "default_characters",
    "PygameSimulator",
    "Queue",
    "TaskPlanner",
    "render_pixel_map",
    "tile_locations",
    "campus_tiles",
]


def _demo() -> None:
    print("=== Mapa del campus estilo pixel art ===")
    print(render_pixel_map())
    print()
    grid = CampusGrid()
    personajes = default_characters(grid)
    planner = TaskPlanner(personajes, grid)
    for personaje in personajes:
        actividad = personaje.next_activity()
        if actividad:
            planner.enqueue(actividad)
    for mensaje in planner.distribute():
        print(mensaje)
    print("Para la versión interactiva usa: from tachi_simulador import PygameSimulator")


if __name__ == "__main__":  # pragma: no cover - bloque interactivo
    _demo()
