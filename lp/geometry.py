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


def _is_unbounded_region(p):
    """La región (no vacía) es no acotada si existe una dirección d ≥ 0, d ≠ 0 con A·d (≤,≥,=) 0."""
    cands = [(Fraction(1), Fraction(0)), (Fraction(0), Fraction(1))]
    for a1, a2 in p.A_2d:
        for sg in (1, -1):
            d = (-a2 * sg, a1 * sg)
            if d != (0, 0):
                cands.append(d)
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
            return True
    return False



class _View:
    """Vista del problema con los coeficientes como pares (a1, a2)."""

    def __init__(self, problem):
        self.A_2d = [(row[0], row[1]) for row in problem.A]
        self.signs = problem.signs
        self.b = problem.b
