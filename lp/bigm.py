"""Método de la Gran M sobre tablero (implementación propia, aritmética exacta)."""
from fractions import Fraction

from .common import Run, choose_entering, ratio_test, MAX_ITER
from .numbers import MNum


def solve_bigm(sf):
    m, N = sf.m, sf.N
    T = [row[:] for row in sf.A]
    rhs = list(sf.b)
    basis = list(sf.basis0)
    steps = []
    k = 0
    while True:
        cB = [sf.c[j] for j in basis]
        zj = [sum((cB[i] * T[i][j] for i in range(m)), MNum()) for j in range(N)]
        dj = [sf.c[j] - zj[j] for j in range(N)]
        z = sum((cB[i] * rhs[i] for i in range(m)), MNum())
        step = {
            "k": k, "basis": basis[:], "cB": cB, "T": [r[:] for r in T], "rhs": rhs[:],
            "zj": zj, "dj": dj, "z": z, "entering": None, "leaving_row": None,
            "pivot": None, "ratios": None, "tied": [], "kind": "tableau",
        }
        steps.append(step)
        if k >= MAX_ITER:
            return Run("bigm", "iteration_limit", steps, basis, rhs)
        e = choose_entering(sf, basis, dj, k)
        if e is None:
            status = "optimal"
            if any(sf.kinds[j] == "art" and rhs[i] > 0 for i, j in enumerate(basis)):
                status = "infeasible"
            return Run("bigm", status, steps, basis, rhs)
        step["entering"] = e
        col = [T[i][e] for i in range(m)]
        ratios, r, tied = ratio_test(basis, rhs, col)
        step["ratios"] = ratios
        step["tied"] = tied
        if r is None:
            return Run("bigm", "unbounded", steps, basis, rhs, unbounded_col=e)
        step["leaving_row"] = r
        p = T[r][e]
        step["pivot"] = p
        T[r] = [v / p for v in T[r]]
        rhs[r] = rhs[r] / p
        for i in range(m):
            if i != r and T[i][e] != 0:
                f = T[i][e]
                T[i] = [a - f * b for a, b in zip(T[i], T[r])]
                rhs[i] -= f * rhs[r]
        basis[r] = e
        k += 1
