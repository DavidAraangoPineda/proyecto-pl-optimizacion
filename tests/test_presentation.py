"""Pruebas del exportador de la presentación (lp/presentation.py)."""
import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lp.model import EXAMPLES, parse_problem  # noqa: E402
from lp.presentation import presentation_html, scene  # noqa: E402


def test_escenas_de_los_ejemplos():
    for p in EXAMPLES.values():
        d = scene(p)
        json.dumps(d)                      # debe ser serializable
        assert d["pasos"], p.name
        if p.n == 2:
            assert "grafico" in d
        if p.n == 3:
            assert "poliedro" in d and not d["poliedro"]["vacia"]


def test_recorrido_coincide_con_el_resultado():
    d = scene(list(EXAMPLES.values())[0])
    assert d["pasos"][-1]["xs"] == ["42", "16"] and d["z"] == "3380"
    anim = d["sensibilidad"]["animacion"]
    assert any(f["b"] == anim["b0"] for f in anim["frames"])   # el valor actual es un cuadro exacto


def test_escenas_aleatorias_no_fallan():
    rng = random.Random(11)
    for _ in range(120):
        n, m = rng.randint(1, 4), rng.randint(1, 4)
        p = parse_problem(rng.choice(["max", "min"]), [str(rng.randint(-3, 9)) for _ in range(n)],
                          [[str(rng.randint(-2, 6)) for _ in range(n)] for _ in range(m)],
                          [rng.choice(["≤", "≥", "="]) for _ in range(m)], [str(rng.randint(-5, 20)) for _ in range(m)])
        json.dumps(scene(p))


def test_html_autonomo():
    html = presentation_html(list(EXAMPLES.values())[1])
    assert "window.DATOS_PL" in html and "<script src=" not in html and 'href="css/' not in html


def test_incluye_simplex_revisado_y_comparacion():
    for p in EXAMPLES.values():
        r = scene(p)["revisado"]
        assert r["pasos"] and r["iguales"], p.name
        assert len(r["pasos"][0]["bloques"]) == 3            # B⁻¹, multiplicadores y costos reducidos
        assert r["estado"] == scene(p)["estado"]
