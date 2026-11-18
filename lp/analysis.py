"""Interpretación del resultado: solución, casos especiales y análisis de sensibilidad."""
from dataclasses import dataclass, field
from fractions import Fraction

from .common import ratio_test
from .linalg import inverse, matvec, column
from .numbers import MNum, fmt


@dataclass
class Sensitivity:
    shadow: list            # precio sombra de cada restricción (cambio de Z por unidad de LD)
    rhs_ranges: list        # (lo, hi) absolutos del LD donde el precio sombra es válido
    reduced: list           # costo reducido de cada variable original (cambio de Z por unidad forzada)
    cost_ranges: list       # (lo, hi) absolutos de cada coeficiente objetivo
    basic: list             # bool: la variable original es básica
    notes: list = field(default_factory=list)


@dataclass
class Solution:
    status: str
    problem: object
    sf: object
    run: object
    x: list = None
    z: Fraction = None
    slacks: list = None          # (tipo, valor) por restricción
    degenerate_vars: list = field(default_factory=list)
    alt_vertices: list = field(default_factory=list)   # otros vértices óptimos (listas de x)
    alt_ray: bool = False
    alt_vars: list = field(default_factory=list)
    sens: Sensitivity = None
    messages: list = field(default_factory=list)
    final_basis: list = None
    tie_iterations: list = field(default_factory=list)

    @property
    def is_optimal(self):
        return self.status == "optimal"

    @property
    def alternative_optima(self):
        return bool(self.alt_vertices) or self.alt_ray

    @property
    def degenerate(self):
        return bool(self.degenerate_vars)


def _x_from_basis(sf, basis, xB):
    x = [Fraction(0)] * sf.n
    for j, v in zip(basis, xB):
        if j < sf.n:
            x[j] = v
    return x


def _feasibility_check(sf, run):
    """Si la Gran M termina «no acotada» con artificiales positivas, el original puede ser infactible.

    Se resuelve la fase 1 (minimizar la suma de artificiales) con el mismo método propio.
    Devuelve la corrida de fase 1 si el problema es infactible, o None si es factible.
    """
    from dataclasses import replace
    from .bigm import solve_bigm

    c1 = [MNum(-1) if k == "art" else MNum(0) for k in sf.kinds]
    r1 = solve_bigm(replace(sf, c=c1))
    # solve_bigm ya marca «infeasible» si termina con una artificial positiva
    return r1 if r1.status == "infeasible" else None


def interpret(problem, sf, run):
    if run.status == "unbounded" and any(
        sf.kinds[j] == "art" and run.xB[i] > 0 for i, j in enumerate(run.basis)
    ):
        r1 = _feasibility_check(sf, run)
        if r1 is not None:
            run.status = "infeasible"
            run.basis, run.xB = r1.basis, r1.xB
            run.notes.append(
                "La Gran M detectó una dirección no acotada con artificiales positivas; una verificación de "
                "factibilidad (minimizar la suma de artificiales) mostró que el problema es infactible."
            )
    sol = Solution(run.status, problem, sf, run)
    sol.tie_iterations = [s["k"] for s in run.steps if len(s.get("tied", [])) > 1]
    names = sf.names

    if run.status == "iteration_limit":
        sol.messages.append("Se alcanzó el límite de iteraciones (posible ciclaje). Revise el modelo.")
        return sol

    if run.status == "infeasible":
        arts = [(names[j], run.xB[i]) for i, j in enumerate(run.basis) if sf.kinds[j] == "art" and run.xB[i] > 0]
        det = ", ".join(f"{n} = {fmt(v)}" for n, v in arts)
        sol.messages.append(
            "El problema NO tiene solución factible. En el óptimo del problema penalizado queda al menos una "
            f"variable artificial positiva ({det}): no es posible satisfacer todas las restricciones a la vez."
        )
        return sol

    if run.status == "unbounded":
        j = run.unbounded_col
        verbo = "aumentar" if problem.sense == "max" else "disminuir"
        sol.messages.append(
            f"La solución es NO ACOTADA: al entrar {names[j]} todos los elementos de su columna son ≤ 0, "
            f"así que {names[j]} puede crecer indefinidamente sin violar ninguna restricción y Z se puede "
            f"{verbo} sin límite."
        )
        return sol

    # --- óptimo
    basis, xB = run.basis, run.xB
    x = _x_from_basis(sf, basis, xB)
    sol.x = x
    sol.z = sum((cj * xj for cj, xj in zip(problem.c, x)), Fraction(0))
    sol.final_basis = basis
    sl = []
    for i in range(problem.m):
        lhs = sum((a * v for a, v in zip(problem.A[i], x)), Fraction(0))
        s = problem.signs[i]
        if s == "<=":
            sl.append(("holgura", problem.b[i] - lhs))
        elif s == ">=":
            sl.append(("exceso", lhs - problem.b[i]))
        else:
            sl.append(("igualdad", Fraction(0)))
    sol.slacks = sl
    sol.degenerate_vars = [names[j] for i, j in enumerate(basis) if xB[i] == 0]
    if sol.degenerate_vars:
        sol.messages.append(
            "Solución DEGENERADA: la(s) variable(s) básica(s) " + ", ".join(sol.degenerate_vars) +
            " vale(n) 0 en el óptimo (hay más restricciones activas que variables positivas)."
        )
    _alternative_optima(sol)
    if sol.alternative_optima:
        sol.messages.append(_alt_message(sol))
    sol.sens = sensitivity(sol)
    return sol


def _final_dj(sf, basis, Binv):
    """Costos reducidos con costos Gran M para la base final."""
    m = sf.m
    cB = [sf.c[j] for j in basis]
    y = [sum((cB[r] * Binv[r][i] for r in range(m)), MNum()) for i in range(m)]
    d = []
    for j in range(sf.N):
        d.append(MNum() if j in basis else sf.c[j] - sum((y[i] * sf.A[i][j] for i in range(m)), MNum()))
    return d


def _alternative_optima(sol):
    sf, basis = sol.sf, sol.final_basis
    Binv = inverse([[sf.A[i][j] for j in basis] for i in range(sf.m)])
    d = _final_dj(sf, basis, Binv)
    xB = matvec(Binv, sf.b)
    for j in range(sf.N):
        if j in basis or sf.kinds[j] == "art" or not d[j].is_zero():
            continue
        sol.alt_vars.append(sf.names[j])
        direction = matvec(Binv, column(sf.A, j))
        ratios, r, _ = ratio_test(basis, xB, direction)
        if r is None:
            sol.alt_ray = True
            continue
        theta = ratios[r]
        newB = [v - theta * dv for v, dv in zip(xB, direction)]
        newB[r] = theta
        nb = basis[:]
        nb[r] = j
        xn = _x_from_basis(sf, nb, newB)
        if xn != sol.x and xn not in sol.alt_vertices:
            sol.alt_vertices.append(xn)


def _alt_message(sol):
    base = ("Existen SOLUCIONES ÓPTIMAS MÚLTIPLES: " + ", ".join(sol.alt_vars) +
            " es no básica con costo reducido 0, así que puede entrar sin cambiar Z. ")
    pts = [sol.x] + sol.alt_vertices
    fmtp = lambda v: "(" + ", ".join(fmt(t) for t in v) + ")"
    if sol.alt_vertices:
        base += ("Vértices óptimos encontrados: " + " y ".join(fmtp(v) for v in pts) +
                 f"; todo punto del segmento que los une da Z = {fmt(sol.z)}.")
    if sol.alt_ray:
        base += " Además existe una dirección no acotada de soluciones óptimas (arista infinita)."
    return base


# ---------------------------------------------------------------- sensibilidad

def sensitivity(sol):
    p, sf, basis = sol.problem, sol.sf, sol.final_basis
    m, N, n = sf.m, sf.N, sf.n
    B = [[sf.A[i][j] for j in basis] for i in range(m)]
    Binv = inverse(B)
    xB = matvec(Binv, sf.b)
    sign = 1 if p.sense == "max" else -1
    # costos reales en forma de maximización (artificiales con costo 0)
    cr = [(sf.c[j].a if sf.kinds[j] != "art" else Fraction(0)) for j in range(N)]
    notes = []
    if any(sf.kinds[j] == "art" for j in basis):
        notes.append("La base final contiene una variable artificial en 0 (degeneración): el análisis puede no ser único.")
    cB = [cr[j] for j in basis]
    y = [sum((cB[r] * Binv[r][i] for r in range(m)), Fraction(0)) for i in range(m)]
    alpha = [[sum((Binv[r][t] * sf.A[t][j] for t in range(m)), Fraction(0)) for j in range(N)] for r in range(m)]
    zj = [sum((cB[r] * alpha[r][j] for r in range(m)), Fraction(0)) for j in range(N)]
    dj = [cr[j] - zj[j] for j in range(N)]           # <= 0 en el óptimo (maximización)

    # precios sombra: dZ/db_i en el sentido original; rangos de LD respecto al LD original
    shadow, rhs_ranges = [], []
    for i in range(m):
        s_i = -1 if sf.flipped[i] else 1
        shadow.append(sign * s_i * y[i])
        lo, hi = None, None
        for r in range(m):
            a = Binv[r][i]
            if a > 0:
                v = -xB[r] / a
                lo = v if lo is None else max(lo, v)
            elif a < 0:
                v = -xB[r] / a
                hi = v if hi is None else min(hi, v)
        if s_i == -1:    # δ en la fila normalizada → δ en el LD original
            lo, hi = (None if hi is None else -hi), (None if lo is None else -lo)
        b0 = p.b[i]
        rhs_ranges.append((None if lo is None else b0 + lo, None if hi is None else b0 + hi))

    basic = [j in basis for j in range(n)]
    reduced, cost_ranges = [], []
    for k in range(n):
        ck = p.c[k]
        if k in basis:
            r = basis.index(k)
            lo, hi = None, None
            for j in range(N):
                if j in basis or sf.kinds[j] == "art":
                    continue
                a = alpha[r][j]
                if a > 0:
                    v = dj[j] / a
                    lo = v if lo is None else max(lo, v)
                elif a < 0:
                    v = dj[j] / a
                    hi = v if hi is None else min(hi, v)
            cmax = sign * ck                           # costo en forma de maximización
            clo = None if lo is None else cmax + lo
            chi = None if hi is None else cmax + hi
            if p.sense == "min":
                clo, chi = (None if chi is None else -chi), (None if clo is None else -clo)
            reduced.append(Fraction(0))
            cost_ranges.append((clo, chi))
        else:
            reduced.append(sign * dj[k])
            if p.sense == "max":
                cost_ranges.append((None, zj[k]))
            else:
                cost_ranges.append((-zj[k], None))
    return Sensitivity(shadow, rhs_ranges, reduced, cost_ranges, basic, notes)
