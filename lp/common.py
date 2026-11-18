"""Reglas de pivoteo comunes a los dos métodos (para que sus iteraciones sean comparables)."""
from dataclasses import dataclass, field

BLAND_AFTER = 200   # tras estas iteraciones se usa la regla de Bland (evita ciclos)
MAX_ITER = 2000


@dataclass
class Run:
    method: str            # "bigm" | "revised"
    status: str            # "optimal" | "infeasible" | "unbounded" | "iteration_limit"
    steps: list            # una entrada por iteración (diccionarios)
    basis: list            # columnas básicas finales
    xB: list               # valores de las variables básicas finales
    unbounded_col: int = None
    notes: list = field(default_factory=list)


def choose_entering(sf, basis, d, iteration):
    """Mayor costo reducido positivo (Dantzig); empates → menor índice. Bland tras muchas iteraciones.

    Las artificiales que ya salieron de la base no vuelven a entrar.
    """
    cands = [j for j in range(sf.N) if j not in basis and sf.kinds[j] != "art" and d[j].positive()]
    if not cands:
        return None
    if iteration >= BLAND_AFTER:
        return min(cands)
    return max(cands, key=lambda j: (d[j].key(), -j))


def ratio_test(basis, rhs, col):
    """Prueba de la razón mínima. Devuelve (razones, fila_saliente, filas_empatadas).

    razones[i] = rhs[i]/col[i] si col[i] > 0, o None si no aplica.
    Empates → sale la variable de menor índice (regla de Bland para la saliente).
    """
    ratios = [(rhs[i] / col[i]) if col[i] > 0 else None for i in range(len(rhs))]
    valid = [r for r in ratios if r is not None]
    if not valid:
        return ratios, None, []
    best = min(valid)
    tied = [i for i, r in enumerate(ratios) if r is not None and r == best]
    leave = min(tied, key=lambda i: basis[i])
    return ratios, leave, tied
