"""Tests del cálculo de tamaño de ventana adaptado a la pantalla (sección 41)."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.window_sizing import compute_window_size, compute_centered_position

MIN_W, MIN_H, IDEAL_W, IDEAL_H = 1024, 640, 1280, 800


def test_never_exceeds_screen_size():
    for w, h in [(1024, 600), (1280, 720), (1366, 768), (1920, 1080), (3840, 2160), (800, 600)]:
        size = compute_window_size(w, h, MIN_W, MIN_H, IDEAL_W, IDEAL_H)
        assert size.width <= w
        assert size.height <= h


def test_uses_ideal_size_on_large_screens():
    size = compute_window_size(1920, 1080, MIN_W, MIN_H, IDEAL_W, IDEAL_H)
    assert size.width == IDEAL_W
    assert size.height == IDEAL_H


def test_caps_at_ideal_size_even_on_huge_screens():
    size = compute_window_size(3840, 2160, MIN_W, MIN_H, IDEAL_W, IDEAL_H)
    assert size.width == IDEAL_W
    assert size.height == IDEAL_H


def test_shrinks_below_minimum_on_tiny_screens_instead_of_overflowing():
    """Si la pantalla es más chica que el mínimo 'deseado', no debe forzar
    una ventana más grande que la pantalla real."""
    size = compute_window_size(800, 600, MIN_W, MIN_H, IDEAL_W, IDEAL_H)
    assert size.width == 800
    assert size.height == 600


def test_centered_position_is_within_screen_bounds():
    screen_w, screen_h = 1920, 1080
    size = compute_window_size(screen_w, screen_h, MIN_W, MIN_H, IDEAL_W, IDEAL_H)
    x, y = compute_centered_position(screen_w, screen_h, size.width, size.height)
    assert 0 <= x <= screen_w - size.width
    assert 0 <= y <= screen_h - size.height
