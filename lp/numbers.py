"""Aritmética exacta: fracciones y números de la forma a + b·M (Gran M simbólica)."""
from fractions import Fraction


def fmt(x, decimals=False, places=4):
    """Formatea un número como fracción exacta (por defecto) o decimal legible."""
    x = Fraction(x)
    if decimals:
        s = f"{float(x):.{places}f}".rstrip("0").rstrip(".")
        return "0" if s in ("", "-0") else s
    if x.denominator == 1:
        return str(x.numerator)
    return f"{x.numerator}/{x.denominator}"


def fmt_bound(x, decimals=False):
    """Formatea un extremo de rango; None representa infinito."""
    return "∞" if x is None else fmt(x, decimals)


def lin_expr(coefs, names, decimals=False):
    """Expresión lineal «2x1 - x2 + 3x3», omitiendo coeficientes nulos."""
    out = ""
    for cf, nm in zip(coefs, names):
        cf = Fraction(cf)
        if cf == 0:
            continue
        neg = cf < 0
        mag = abs(cf)
        body = ("" if mag == 1 else fmt(mag, decimals)) + nm
        if not out:
            out = ("-" if neg else "") + body
        else:
            out += f" {'-' if neg else '+'} {body}"
    return out or "0"


class MNum:
    """Número a + b·M, con M un número positivo arbitrariamente grande.

    Se ordena lexicográficamente por (b, a): así se compara sin darle un valor
    numérico a M. Solo se usa para la fila de costos del método de la Gran M.
    """

    __slots__ = ("a", "b")

    def __init__(self, a=0, b=0):
        self.a = Fraction(a)
        self.b = Fraction(b)

    def key(self):
        return (self.b, self.a)

    def __add__(self, o):
        o = o if isinstance(o, MNum) else MNum(o)
        return MNum(self.a + o.a, self.b + o.b)

    __radd__ = __add__

    def __neg__(self):
        return MNum(-self.a, -self.b)

    def __sub__(self, o):
        o = o if isinstance(o, MNum) else MNum(o)
        return MNum(self.a - o.a, self.b - o.b)

    def __mul__(self, k):
        k = Fraction(k)
        return MNum(self.a * k, self.b * k)

    __rmul__ = __mul__

    def __eq__(self, o):
        o = o if isinstance(o, MNum) else MNum(o)
        return self.a == o.a and self.b == o.b

    def __hash__(self):
        return hash(self.key())

    def is_zero(self):
        return self.a == 0 and self.b == 0

    def positive(self):
        return self.key() > (0, 0)

    def negative(self):
        return self.key() < (0, 0)

    def fmt(self, decimals=False):
        a, b = self.a, self.b
        if b == 0:
            return fmt(a, decimals)
        if b == 1:
            mp = "M"
        elif b == -1:
            mp = "-M"
        elif b.denominator == 1 or decimals:
            mp = f"{fmt(b, decimals)}M"
        else:
            mp = f"({fmt(b)})M"
        if a == 0:
            return mp
        return f"{mp} {'+' if a > 0 else '-'} {fmt(abs(a), decimals)}"

    def __repr__(self):
        return f"MNum({self.a}, {self.b})"
