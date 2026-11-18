"""Modelo del problema, validación de la entrada, guardado/carga en JSON y ejemplos."""
import json
from dataclasses import dataclass, field
from fractions import Fraction

SIGNS = ("<=", ">=", "=")
SIGN_LABEL = {"<=": "≤", ">=": "≥", "=": "="}
SIGN_FROM_LABEL = {"≤": "<=", "≥": ">=", "=": "=", "<=": "<=", ">=": ">=", "==": "="}


class ValidationError(Exception):
    """Entrada inválida. `messages` lleva una lista de mensajes legibles."""

    def __init__(self, messages):
        self.messages = list(messages)
        super().__init__("\n".join(self.messages))


@dataclass
class Problem:
    sense: str                     # "max" | "min"
    c: list                        # coeficientes de la función objetivo (Fraction)
    A: list                        # matriz m x n (Fraction)
    signs: list                    # "<=", ">=", "="
    b: list                        # lados derechos (Fraction)
    name: str = ""
    var_names: list = field(default_factory=list)

    def __post_init__(self):
        if not self.var_names:
            self.var_names = [f"x{j + 1}" for j in range(len(self.c))]

    @property
    def n(self):
        return len(self.c)

    @property
    def m(self):
        return len(self.A)


def parse_number(text):
    """Convierte '3', '-2.5', '1,5' o '7/3' a Fraction. Lanza ValueError si no es numérico."""
    if isinstance(text, (int, Fraction)):
        return Fraction(text)
    if isinstance(text, float):
        if text != text or text in (float("inf"), float("-inf")):
            raise ValueError("no finito")
        return Fraction(str(text))
    s = str(text).strip().replace(",", ".").replace("−", "-").replace(" ", "")
    if s == "":
        raise ValueError("vacío")
    return Fraction(s)  # admite enteros, decimales, fracciones y notación científica


def _is_blank(v):
    return v is None or (isinstance(v, float) and v != v) or str(v).strip() in ("", "None", "nan")


def parse_problem(sense, c_cells, A_cells, sign_cells, b_cells, name=""):
    """Valida la entrada cruda (textos de la interfaz) y construye un Problem.

    Acumula TODOS los errores (campos vacíos, valores no numéricos, signos o
    dimensiones inconsistentes) y los lanza juntos en una ValidationError.
    """
    errors = []
    if str(sense).lower() not in ("max", "min"):
        errors.append("El tipo de problema debe ser Maximizar o Minimizar.")
    n = len(c_cells)
    m = len(A_cells)
    if n < 1:
        errors.append("Debe haber al menos una variable.")
    if m < 1:
        errors.append("Debe haber al menos una restricción.")
    if not (len(sign_cells) == m == len(b_cells)):
        errors.append("Dimensiones inconsistentes: el número de signos y lados derechos debe coincidir con las restricciones.")
    for i, row in enumerate(A_cells):
        if len(row) != n:
            errors.append(f"Dimensiones inconsistentes: la restricción R{i + 1} tiene {len(row)} coeficientes y hay {n} variables.")
    if errors:
        raise ValidationError(errors)

    def num(cell, where):
        if _is_blank(cell):
            errors.append(f"Campo vacío en {where}.")
            return Fraction(0)
        try:
            return parse_number(cell)
        except (ValueError, ZeroDivisionError):
            errors.append(f"Valor no numérico en {where}: «{cell}».")
            return Fraction(0)

    c = [num(v, f"el coeficiente de x{j + 1} en la función objetivo") for j, v in enumerate(c_cells)]
    A = [[num(v, f"R{i + 1}, coeficiente de x{j + 1}") for j, v in enumerate(row)] for i, row in enumerate(A_cells)]
    b = [num(v, f"el lado derecho de R{i + 1}") for i, v in enumerate(b_cells)]
    signs = []
    for i, s in enumerate(sign_cells):
        key = SIGN_FROM_LABEL.get(str(s).strip())
        if key is None:
            errors.append(f"Signo inválido en R{i + 1}: «{s}». Use ≤, ≥ o =.")
            key = "<="
        signs.append(key)
    if errors:
        raise ValidationError(errors)
    return Problem(str(sense).lower(), c, A, signs, b, name=name)


def objective_text(p, decimals=False):
    from .render import lin_expr
    return f"{'Max' if p.sense == 'max' else 'Min'} Z = {lin_expr(p.c, p.var_names, decimals)}"


def constraints_text(p, decimals=False):
    from .render import lin_expr
    from .numbers import fmt
    return [f"R{i + 1}: {lin_expr(p.A[i], p.var_names, decimals)} {SIGN_LABEL[p.signs[i]]} {fmt(p.b[i], decimals)}" for i in range(p.m)]


# ---------------------------------------------------------------- JSON

def problem_to_dict(p):
    return {
        "name": p.name,
        "sense": p.sense,
        "c": [str(v) for v in p.c],
        "constraints": [
            {"a": [str(v) for v in p.A[i]], "sign": p.signs[i], "b": str(p.b[i])} for i in range(p.m)
        ],
    }


def problem_to_json(p):
    return json.dumps(problem_to_dict(p), indent=2, ensure_ascii=False)


def raw_from_json(text):
    """Lee un JSON y devuelve (sense, c, A, signs, b, name) como textos, sin validar números."""
    try:
        d = json.loads(text)
        cons = d["constraints"]
        return (
            d["sense"], [str(v) for v in d["c"]],
            [[str(v) for v in k["a"]] for k in cons],
            [SIGN_LABEL.get(k["sign"], k["sign"]) for k in cons],
            [str(k["b"]) for k in cons],
            d.get("name", ""),
        )
    except (KeyError, TypeError, ValueError) as e:
        raise ValidationError([f"El archivo no tiene el formato esperado de un problema ({e!s})."])


def problem_from_json(text):
    sense, c, A, signs, b, name = raw_from_json(text)
    return parse_problem(sense, c, A, signs, b, name)


# ---------------------------------------------------------------- ejemplos del enunciado

def _ex(name, sense, c, A, signs, b):
    return parse_problem(sense, c, A, signs, b, name)


EXAMPLES = {
    "1. Max, restricción redundante (gráfico)": _ex("Ejemplo 1", "max", ["50", "80"],
        [["2", "1"], ["1", "3"], ["0", "1"]], ["<=", "<=", "<="], ["100", "90", "40"]),
    "2. Min con =, ≥ y LD negativo": _ex("Ejemplo 2", "min", ["4", "1"],
        [["3", "1"], ["4", "3"], ["-1", "-2"]], ["=", ">=", ">="], ["3", "6", "-4"]),
    "3. Tres variables": _ex("Ejemplo 3", "max", ["3", "2", "5"],
        [["1", "2", "1"], ["3", "0", "2"], ["1", "4", "0"]], ["<=", "<=", "<="], ["430", "460", "420"]),
    "4. Infactible": _ex("Ejemplo 4", "max", ["1", "1"],
        [["1", "1"], ["1", "1"]], ["<=", ">="], ["2", "5"]),
    "5. No acotado": _ex("Ejemplo 5", "max", ["1", "1"],
        [["1", "-1"], ["-1", "1"]], ["<=", "<="], ["1", "2"]),
    "6. Óptimos múltiples": _ex("Ejemplo 6", "max", ["2", "4"],
        [["1", "2"], ["1", "1"]], ["<=", "<="], ["5", "4"]),
    "7. Degenerado": _ex("Ejemplo 7", "max", ["3", "9"],
        [["1", "4"], ["1", "2"]], ["<=", "<="], ["8", "4"]),
}
