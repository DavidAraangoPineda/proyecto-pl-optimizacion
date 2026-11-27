"""Pruebas del método gráfico y de la geometría 2D (lp/geometry.py, lp/graphical.py)."""
import sys
from fractions import Fraction
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lp.geometry import feasible_vertices_2d, is_unbounded_region_2d  # noqa: E402
from lp.graphical import graph_2d  # noqa: E402
from lp.model import EXAMPLES  # noqa: E402
from lp.solver import solve  # noqa: E402

EJ = list(EXAMPLES.values())


def test_vertices_del_ejemplo_1():
    verts = feasible_vertices_2d(EJ[0])
    assert (Fraction(42), Fraction(16)) in verts and (Fraction(0), Fraction(0)) in verts
    assert not is_unbounded_region_2d(EJ[0])


def test_region_vacia_y_no_acotada():
    assert feasible_vertices_2d(EJ[3]) == []          # ejemplo 4: infactible
    assert is_unbounded_region_2d(EJ[4])              # ejemplo 5: no acotado


@pytest.mark.parametrize("oscuro", [False, True])
def test_graph_2d_para_todos_los_ejemplos(oscuro):
    for p in EJ:
        info = graph_2d(p, solve(p), dark=oscuro)
        if p.n != 2:
            assert not info.applicable
        else:
            assert info.applicable and info.figure is not None
