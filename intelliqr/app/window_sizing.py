
from __future__ import annotations
from dataclasses import dataclass


@dataclass
class WindowSize:
    width: int
    height: int


def compute_window_size(
    screen_width: int,
    screen_height: int,
    min_width: int,
    min_height: int,
    ideal_width: int,
    ideal_height: int,
    margin_ratio: float = 0.92,
) -> WindowSize:
    """
    Calcula el tamaño con el que debe abrir la ventana:
    - Nunca ocupa más del `margin_ratio` de la pantalla disponible (deja
      margen para la barra de tareas y no tapa toda la pantalla).
    - Intenta usar el tamaño "ideal" si la pantalla es lo bastante grande.
    - Si la pantalla es más chica que el mínimo, se ajusta al tamaño real
      de la pantalla en vez de forzar un tamaño que no cabe (monitores o
      portátiles pequeños, en pulgadas, con resoluciones bajas).
    """
    max_w = int(screen_width * margin_ratio)
    max_h = int(screen_height * margin_ratio)

    width = min(ideal_width, max_w)
    height = min(ideal_height, max_h)

    # No forzar un tamaño mayor al que realmente cabe en la pantalla,
    # aunque eso signifique quedar por debajo del mínimo "deseado".
    width = max(width, min(min_width, screen_width))
    height = max(height, min(min_height, screen_height))

    return WindowSize(width=width, height=height)


def compute_centered_position(screen_width: int, screen_height: int, window_width: int, window_height: int) -> tuple[int, int]:
    """Posición (x, y) para centrar la ventana en la pantalla disponible."""
    x = max((screen_width - window_width) // 2, 0)
    y = max((screen_height - window_height) // 2, 0)
    return x, y
