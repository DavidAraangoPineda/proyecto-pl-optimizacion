"""Geometría exacta de la región factible en dos variables (sin dibujo ni dependencias externas).

La usan el método gráfico (lp/graphical.py) y la presentación (lp/presentation.py).
"""
from fractions import Fraction


def feasible_vertices_2d(problem):
    """Vértices (x1, x2) exactos de la región factible, ordenados. Lista vacía si la región es vacía."""
    return _vertices(_View(problem))


def is_unbounded_region_2d(problem):
    """True si la región factible (no vacía) se extiende indefinidamente."""
    return _is_unbounded_region(_View(problem))


def _feasible(p, x1, x2):
    if x1 < 0 or x2 < 0:
        return False
    for (a1, a2), s, b in zip(p.A_2d, p.signs, p.b):
        v = a1 * x1 + a2 * x2
        if (s == "<=" and v > b) or (s == ">=" and v < b) or (s == "=" and v != b):
            return False
    return True


def _vertices(p):
    lines = [(a, b_) for a, b_ in zip(p.A_2d, p.b)] + [((Fraction(1), Fraction(0)), Fraction(0)),
                                                         ((Fraction(0), Fraction(1)), Fraction(0))]
    pts = set()
    for i in range(len(lines)):
        for j in range(i + 1, len(lines)):
            (a1, a2), b1 = lines[i]
            (c1, c2), b2 = lines[j]
            det = a1 * c2 - a2 * c1
            if det == 0:
                continue
            x1 = (b1 * c2 - a2 * b2) / det
            x2 = (a1 * b2 - b1 * c1) / det
            if _feasible(p, x1, x2):
                pts.add((x1, x2))
    return sorted(pts)


def improving_direction_2d(problem):
    """Dirección (d1, d2) por la que la región se extiende sin fin y Z mejora; None si no existe.

    Si existe, el problema es no acotado. Entre las direcciones candidatas se elige la que más mejora Z
    por unidad de longitud (sirve para dibujar la flecha «Z crece sin límite»).
    """
    p = _View(problem)
    sgn = 1 if problem.sense == "max" else -1
    best, best_score = None, 0.0
    for d1, d2 in _recession_directions(p):
        gain = sgn * (problem.c[0] * d1 + problem.c[1] * d2)
        if gain > 0:
            score = float(gain) / (float(d1) ** 2 + float(d2) ** 2) ** 0.5
            if score > best_score:
                best, best_score = (d1, d2), score
    return best


def _recession_directions(p):
    """Direcciones d ≥ 0, d ≠ 0 con A·d (≤, ≥, =) 0: hacia donde la región se extiende sin fin.

    Basta revisar los ejes y las direcciones paralelas a cada restricción: los bordes del cono de
    direcciones están siempre entre ellas.
    """
    cands = [(Fraction(1), Fraction(0)), (Fraction(0), Fraction(1))]
    for a1, a2 in p.A_2d:
        for sg in (1, -1):
            d = (-a2 * sg, a1 * sg)
            if d != (0, 0):
                cands.append(d)
    out = []
    for d1, d2 in cands:
        if d1 < 0 or d2 < 0 or (d1 == 0 and d2 == 0):
            continue
        ok = True
        for (a1, a2), s in zip(p.A_2d, p.signs):
            v = a1 * d1 + a2 * d2
            if (s == "<=" and v > 0) or (s == ">=" and v < 0) or (s == "=" and v != 0):
                ok = False
                break
        if ok:
            out.append((d1, d2))
    return out


def _is_unbounded_region(p):
    """La región (no vacía) es no acotada si existe alguna dirección de recesión."""
    return bool(_recession_directions(p))


class _View:
    """Vista del problema con los coeficientes como pares (a1, a2)."""

    def __init__(self, problem):
        self.A_2d = [(row[0], row[1]) for row in problem.A]
        self.signs = problem.signs
        self.b = problem.b
