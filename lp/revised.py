"""Simplex revisado con B⁻¹ explícita y costos Gran M (implementación propia, aritmética exacta)."""
from .common import Run, choose_entering, ratio_test, MAX_ITER
from .linalg import identity, matvec, column
from .numbers import MNum


def solve_revised(sf):
    m, N = sf.m, sf.N
    basis = list(sf.basis0)
    Binv = identity(m)     # la base inicial (holguras/artificiales) es la identidad
    steps = []
    k = 0
    while True:
        xB = matvec(Binv, sf.b)
        cB = [sf.c[j] for j in basis]
        # multiplicadores y = cB · B⁻¹
        y = [sum((cB[r] * Binv[r][i] for r in range(m)), MNum()) for i in range(m)]
        d = [None] * N
        for j in range(N):
            if j in basis:
                d[j] = MNum()
            else:
                d[j] = sf.c[j] - sum((y[i] * sf.A[i][j] for i in range(m)), MNum())
        z = sum((cB[i] * xB[i] for i in range(m)), MNum())
        step = {
            "k": k, "basis": basis[:], "cB": cB, "Binv": [r[:] for r in Binv], "xB": xB[:],
            "y": y, "dj": d, "z": z, "entering": None, "leaving_row": None, "pivot": None,
            "direction": None, "ratios": None, "tied": [], "kind": "revised",
        }
        steps.append(step)
        if k >= MAX_ITER:
            return Run("revised", "iteration_limit", steps, basis, xB)
        e = choose_entering(sf, basis, d, k)
        if e is None:
            status = "optimal"
            if any(sf.kinds[j] == "art" and xB[i] > 0 for i, j in enumerate(basis)):
                status = "infeasible"
            return Run("revised", status, steps, basis, xB)
        step["entering"] = e
        direction = matvec(Binv, column(sf.A, e))      # α = B⁻¹ a_e
        step["direction"] = direction
        ratios, r, tied = ratio_test(basis, xB, direction)
        step["ratios"] = ratios
        step["tied"] = tied
        if r is None:
            return Run("revised", "unbounded", steps, basis, xB, unbounded_col=e)
        step["leaving_row"] = r
        p = direction[r]
        step["pivot"] = p
        # actualización de B⁻¹ (pivoteo sobre [B⁻¹ | α])
        Binv[r] = [v / p for v in Binv[r]]
        for i in range(m):
            if i != r and direction[i] != 0:
                f = direction[i]
                Binv[i] = [a - f * b for a, b in zip(Binv[i], Binv[r])]
        basis[r] = e
        k += 1
