"""Conversión a forma estándar: holguras, excesos y variables artificiales (Gran M)."""
from dataclasses import dataclass, field
from fractions import Fraction

from .numbers import MNum, fmt, lin_expr

_FLIP = {"<=": ">=", ">=": "<=", "=": "="}


@dataclass
class StandardForm:
    names: list            # nombre de cada columna: x1.., s1.., e1.., a1..
    kinds: list            # "x" | "slack" | "surplus" | "art"
    A: list                # m x N (Fraction), con lados derechos >= 0
    b: list                # lados derechos normalizados (>= 0)
    c: list                # costos en forma de maximización (MNum); artificiales = -M
    basis0: list           # columnas de la base inicial
    flipped: list          # fila multiplicada por -1 (LD negativo)
    row_id_col: list       # columna identidad inicial de cada fila (holgura o artificial)
    col_row: list          # fila a la que pertenece cada holgura/exceso/artificial (None para x)
    n: int                 # número de variables originales
    notes: list = field(default_factory=list)

    @property
    def m(self):
        return len(self.b)

    @property
    def N(self):
        return len(self.names)

    @property
    def has_artificial(self):
        return "art" in self.kinds


def build_standard_form(p):
    n, m = p.n, p.m
    signs = list(p.signs)
    rows = [list(r) for r in p.A]
    b = list(p.b)
    flipped = [False] * m
    notes = []
    for i in range(m):
        if b[i] < 0:
            rows[i] = [-v for v in rows[i]]
            b[i] = -b[i]
            old = signs[i]
            signs[i] = _FLIP[old]
            flipped[i] = True
            notes.append(
                f"R{i + 1} tenía lado derecho negativo: se multiplicó por −1 "
                f"(el signo {_sym(old)} pasa a {_sym(signs[i])})."
            )

    names = [f"x{j + 1}" for j in range(n)]
    kinds = ["x"] * n
    col_row = [None] * n
    cols = []  # columnas extra: (nombre, tipo, fila, coeficiente)
    for i in range(m):
        if signs[i] == "<=":
            cols.append((f"s{i + 1}", "slack", i, Fraction(1)))
        elif signs[i] == ">=":
            cols.append((f"e{i + 1}", "surplus", i, Fraction(-1)))
    for i in range(m):
        if signs[i] in (">=", "="):
            cols.append((f"a{i + 1}", "art", i, Fraction(1)))

    N = n + len(cols)
    A = [rows[i] + [Fraction(0)] * len(cols) for i in range(m)]
    c = [MNum(v if p.sense == "max" else -v) for v in p.c]
    basis0 = [None] * m
    row_id_col = [None] * m
    for k, (nm, kd, i, coef) in enumerate(cols):
        j = n + k
        names.append(nm)
        kinds.append(kd)
        col_row.append(i)
        A[i][j] = coef
        if kd == "art":
            c.append(MNum(0, -1))
            basis0[i] = j
            row_id_col[i] = j
        else:
            c.append(MNum(0))
            if kd == "slack":
                basis0[i] = j
                row_id_col[i] = j
    if p.sense == "min":
        notes.append("Problema de minimización: se maximiza Z' = −Z (al final Z = −Z').")
    return StandardForm(names, kinds, A, b, c, basis0, flipped, row_id_col, col_row, n, notes)


def _sym(s):
    return {"<=": "≤", ">=": "≥", "=": "="}[s]


def standard_form_lines(p, sf, decimals=False):
    """Texto de la forma estándar (objetivo y una ecuación por restricción)."""
    terms = []
    for j in range(sf.N):
        cj = sf.c[j]
        if cj.is_zero():
            continue
        terms.append((cj, sf.names[j]))
    obj = _mnum_expr(terms, decimals)
    head = "Max Z'" if p.sense == "min" else "Max Z"
    lines = [f"{head} = {obj}" + ("   (con Z' = −Z)" if p.sense == "min" else "")]
    for i in range(sf.m):
        lhs = lin_expr(sf.A[i], sf.names, decimals)
        lines.append(f"R{i + 1}:  {lhs} = {fmt(sf.b[i], decimals)}")
    lines.append("Todas las variables ≥ 0: " + ", ".join(sf.names))
    return lines


def _mnum_expr(terms, decimals):
    """Expresión de costos con M: «50x1 + 80x2 - Ma2»."""
    out = ""
    for cj, name in terms:
        neg = cj.key() < (0, 0)
        mag = -cj if neg else cj
        if mag.b == 0:
            coef = "" if mag.a == 1 else fmt(mag.a, decimals)
        elif mag.a == 0:
            coef = "M" if mag.b == 1 else f"{fmt(mag.b, decimals)}M"
        else:
            coef = f"({mag.fmt(decimals)})"
        piece = coef + name
        if not out:
            out = ("-" if neg else "") + piece
        else:
            out += f" {'-' if neg else '+'} {piece}"
    return out or "0"
