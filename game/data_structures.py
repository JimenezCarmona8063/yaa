from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable, Iterator, Optional


class Node:
    __slots__ = ("value", "next")

    def __init__(self, value: Any, next: Optional["Node"] = None) -> None:
        self.value = value
        self.next = next

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"Node({self.value!r})"


class LinkedList:
    def __init__(self, values: Optional[Iterable[Any]] = None) -> None:
        self.head: Optional[Node] = None
        self.tail: Optional[Node] = None
        self._length = 0
        if values:
            for value in values:
                self.append(value)

    def append(self, value: Any) -> None:
        new_node = Node(value)
        if not self.head:
            self.head = self.tail = new_node
        else:
            assert self.tail is not None
            self.tail.next = new_node
            self.tail = new_node
        self._length += 1

    def popleft(self) -> Any:
        if not self.head:
            raise IndexError("Pop from empty linked list")
        node = self.head
        self.head = node.next
        if self.head is None:
            self.tail = None
        self._length -= 1
        return node.value

    def __len__(self) -> int:
        return self._length

    def __iter__(self) -> Iterator[Any]:
        current = self.head
        while current:
            yield current.value
            current = current.next


class CustomQueue:
    def __init__(self) -> None:
        self._list = LinkedList()

    def enqueue(self, value: Any) -> None:
        self._list.append(value)

    def dequeue(self) -> Any:
        return self._list.popleft()

    def is_empty(self) -> bool:
        return len(self._list) == 0

    def __len__(self) -> int:
        return len(self._list)

    def __iter__(self) -> Iterator[Any]:
        return iter(self._list)


class CustomDeque:
    def __init__(self) -> None:
        self._list = LinkedList()

    def push_back(self, value: Any) -> None:
        self._list.append(value)

    def push_front(self, value: Any) -> None:
        new_node = Node(value, self._list.head)
        self._list.head = new_node
        if self._list.tail is None:
            self._list.tail = new_node
        self._list._length += 1

    def pop_front(self) -> Any:
        return self._list.popleft()

    def pop_back(self) -> Any:
        if self._list.tail is None:
            raise IndexError("Pop from empty deque")
        if self._list.head is self._list.tail:
            value = self._list.tail.value
            self._list.head = self._list.tail = None
            self._list._length = 0
            return value
        current = self._list.head
        assert current is not None
        while current.next is not self._list.tail:
            current = current.next
            assert current is not None
        assert self._list.tail is not None
        value = self._list.tail.value
        current.next = None
        self._list.tail = current
        self._list._length -= 1
        return value

    def __len__(self) -> int:
        return len(self._list)

    def __iter__(self) -> Iterator[Any]:
        return iter(self._list)


@dataclass(order=True)
class PrioritizedItem:
    priority: float
    count: int
    value: Any


class PriorityQueue:
    def __init__(self) -> None:
        self._heap: list[PrioritizedItem] = []
        self._counter = 0

    def push(self, priority: float, value: Any) -> None:
        from bisect import insort

        item = PrioritizedItem(priority, self._counter, value)
        self._counter += 1
        insort(self._heap, item)

    def pop(self) -> Any:
        if not self._heap:
            raise IndexError("Pop from empty priority queue")
        return self._heap.pop(0).value

    def __len__(self) -> int:
        return len(self._heap)

    def peek(self) -> Any:
        if not self._heap:
            raise IndexError("Peek from empty priority queue")
        return self._heap[0].value

    def clear(self) -> None:
        self._heap.clear()
        self._counter = 0

    def items(self) -> list[Any]:
        return [item.value for item in self._heap]
