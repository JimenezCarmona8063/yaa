from __future__ import annotations

"""Punto de entrada simplificado para lanzar el simulador TACHI."""

from tachi_simulador import PygameSimulator


def main() -> None:
    simulador = PygameSimulator()
    simulador.run()


if __name__ == "__main__":
    main()
