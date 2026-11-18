"""Pruebas del motor con los 7 problemas del enunciado.

scipy se usa ÚNICAMENTE aquí, para verificar los resultados del método propio.
"""
import random
import sys
from fractions import Fraction as F
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from lp.model import EXAMPLES, Problem, parse_problem, ValidationError  # noqa: E402
from lp.solver import solve  # noqa: E402

METHODS = ["bigm", "revised"]
EX = list(EXAMPLES.values())


@pytest.mark.parametrize("method", METHODS)
def test_ejemplo1(method):
    s = solve(EX[0], method)
    assert s.status == "optimal" and s.x == [42, 16] and s.z == 3380
    assert s.slacks[2] == ("holgura", 24)          # x2 <= 40 es redundante


@pytest.mark.parametrize("method", METHODS)
def test_ejemplo2(method):
    s = solve(EX[1], method)
    assert s.status == "optimal"
    assert s.x == [F(2, 5), F(9, 5)] and s.z == F(17, 5)


@pytest.mark.parametrize("method", METHODS)
def test_ejemplo3(method):
    s = solve(EX[2], method)
    assert s.x == [0, 100, 230] and s.z == 1350


@pytest.mark.parametrize("method", METHODS)
def test_ejemplo4_infactible(method):
    assert solve(EX[3], method).status == "infeasible"


@pytest.mark.parametrize("method", METHODS)
def test_ejemplo5_no_acotado(method):
    assert solve(EX[4], method).status == "unbounded"


@pytest.mark.parametrize("method", METHODS)
def test_ejemplo6_multiples(method):
    s = solve(EX[5], method)
    assert s.status == "optimal" and s.z == 10 and s.alternative_optima
    pts = [tuple(s.x)] + [tuple(v) for v in s.alt_vertices]
    assert (F(0), F(5, 2)) in pts and (F(3), F(1)) in pts


@pytest.mark.parametrize("method", METHODS)
def test_ejemplo7_degenerado(method):
    s = solve(EX[6], method)
    assert s.x == [0, 2] and s.z == 18 and s.degenerate


def test_ambos_metodos_mismas_iteraciones():
    for p in EX:
        a, b = solve(p, "bigm"), solve(p, "revised")
        assert [t["entering"] for t in a.run.steps] == [t["entering"] for t in b.run.steps]
        assert [t["leaving_row"] for t in a.run.steps] == [t["leaving_row"] for t in b.run.steps]


# ---------------------------------------------------------------- verificación contra scipy

def _scipy(p):
    import numpy as np
    from scipy.optimize import linprog

    c = [float(v) for v in p.c]
    if p.sense == "max":
        c = [-v for v in c]
    A_ub, b_ub, A_eq, b_eq = [], [], [], []
    for row, sg, b in zip(p.A, p.signs, p.b):
        r = [float(v) for v in row]
        if sg == "<=":
            A_ub.append(r), b_ub.append(float(b))
        elif sg == ">=":
            A_ub.append([-v for v in r]), b_ub.append(-float(b))
        else:
            A_eq.append(r), b_eq.append(float(b))
    return linprog(c, A_ub=A_ub or None, b_ub=b_ub or None, A_eq=A_eq or None, b_eq=b_eq or None,
                   bounds=[(0, None)] * len(c), method="highs")


def _random_problem(rng):
    n, m = rng.randint(2, 4), rng.randint(2, 4)
    c = [str(rng.randint(-3, 9)) for _ in range(n)]
    A = [[str(rng.randint(-2, 6)) for _ in range(n)] for _ in range(m)]
    signs = [rng.choice(["≤", "≤", "≥", "="]) for _ in range(m)]
    b = [str(rng.randint(-5, 30)) for _ in range(m)]
    return parse_problem(rng.choice(["max", "min"]), c, A, signs, b)


@pytest.mark.parametrize("method", METHODS)
def test_aleatorios_contra_scipy(method):
    rng = random.Random(2026)
    checked = 0
    for _ in range(400):
        p = _random_problem(rng)
        ref = _scipy(p)
        s = solve(p, method)
        if ref.status == 0:
            assert s.status == "optimal", (p, s.status)
            z_ref = -ref.fun if p.sense == "max" else ref.fun
            assert abs(float(s.z) - z_ref) < 1e-6, (p, float(s.z), z_ref)
            # la solución propia debe ser factible
            for row, sg, b in zip(p.A, p.signs, p.b):
                lhs = sum(a * x for a, x in zip(row, s.x))
                assert (sg == "<=" and lhs <= b) or (sg == ">=" and lhs >= b) or (sg == "=" and lhs == b)
            assert all(v >= 0 for v in s.x)
            checked += 1
        elif ref.status == 2:
            assert s.status == "infeasible", (p, s.status)
        elif ref.status == 3:
            assert s.status == "unbounded", (p, s.status)
    assert checked > 50


def test_sensibilidad_contra_resolver():
    """Precio sombra y rango de LD verificados re-resolviendo el problema con el LD perturbado."""
    rng = random.Random(7)
    checked = 0
    for _ in range(300):
        p = _random_problem(rng)
        s = solve(p, "bigm")
        if s.status != "optimal" or s.degenerate or s.alternative_optima:
            continue
        for i in range(p.m):
            lo, hi = s.sens.rhs_ranges[i]
            for target in (lo, hi):
                if target is None:
                    continue
                b2 = list(p.b)
                b2[i] = target
                q = Problem(p.sense, p.c, p.A, p.signs, b2)
                t = solve(q, "bigm")
                if t.status == "optimal":
                    # dentro del rango cerrado Z cambia linealmente con el precio sombra
                    assert t.z - s.z == s.sens.shadow[i] * (target - p.b[i]), (p, i)
                    checked += 1
        # rango de costos: dentro del rango la solución óptima no cambia
        for k in range(p.n):
            lo, hi = s.sens.cost_ranges[k]
            for target in (lo, hi):
                if target is None:
                    continue
                c2 = list(p.c)
                c2[k] = target
                t = solve(Problem(p.sense, c2, p.A, p.signs, p.b), "bigm")
                assert t.status == "optimal"
                assert sum(a * b for a, b in zip(c2, s.x)) == t.z, (p, k)
    assert checked > 30


# ---------------------------------------------------------------- validación

def test_validacion():
    with pytest.raises(ValidationError) as e:
        parse_problem("max", ["1", ""], [["1", "abc"]], ["≤"], ["5"])
    assert len(e.value.messages) == 2
    with pytest.raises(ValidationError):
        parse_problem("max", ["1", "2"], [["1"]], ["≤"], ["5"])     # dimensiones
    with pytest.raises(ValidationError):
        parse_problem("max", ["1"], [["1"]], ["<>"], ["5"])        # signo
    p = parse_problem("min", ["1,5", "1/2"], [["1", "1"]], ["≥"], ["-2"])
    assert p.c == [F(3, 2), F(1, 2)] and p.b == [-2]
