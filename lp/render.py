"""Utilidades de presentación (texto y tablas) compartidas por la interfaz y el PDF."""
from fractions import Fraction

from .numbers import fmt, fmt_bound, MNum


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


# ---------------------------------------------------------------- tableros y justificaciones

def _m(v, dec):
    return v.fmt(dec) if isinstance(v, MNum) else fmt(v, dec)


def tableau_table(sf, step, decimals=False):
    """Tablero de la Gran M: (encabezado, filas, meta) donde meta marca columna/fila/pivote."""
    names = sf.names
    header = ["Base", "cB"] + names + ["b", "Razón"]
    rows = [["cj", ""] + [_m(c, decimals) for c in sf.c] + ["", ""]]
    for i, j in enumerate(step["basis"]):
        ratio = ""
        if step["ratios"] is not None:
            r = step["ratios"][i]
            ratio = "—" if r is None else fmt(r, decimals)
        rows.append([names[j], _m(step["cB"][i], decimals)] + [fmt(v, decimals) for v in step["T"][i]]
                    + [fmt(step["rhs"][i], decimals), ratio])
    rows.append(["zj", ""] + [_m(v, decimals) for v in step["zj"]] + [_m(step["z"], decimals), ""])
    rows.append(["cj − zj", ""] + [_m(v, decimals) for v in step["dj"]] + ["", ""])
    meta = {"enter_col": None, "leave_row": None}
    if step["entering"] is not None:
        meta["enter_col"] = 2 + step["entering"]
    if step["leaving_row"] is not None:
        meta["leave_row"] = 1 + step["leaving_row"]
    return header, rows, meta


def revised_blocks(sf, step, decimals=False):
    """Bloques del simplex revisado: lista de (título, encabezado, filas, meta)."""
    names, m = sf.names, sf.m
    basis = step["basis"]
    meta0 = {"enter_col": None, "leave_row": None}
    blocks = []
    # B⁻¹, cB y xB
    header = ["Variable básica", "cB"] + [f"B⁻¹ (col {i + 1})" for i in range(m)] + ["xB = B⁻¹·b"]
    ratio_col = step["ratios"] is not None
    if ratio_col:
        header += ["α = B⁻¹·a_e", "Razón xB/α"]
    rows = []
    for i, j in enumerate(basis):
        row = [names[j], _m(step["cB"][i], decimals)] + [fmt(v, decimals) for v in step["Binv"][i]] + [fmt(step["xB"][i], decimals)]
        if ratio_col:
            r = step["ratios"][i]
            row += [fmt(step["direction"][i], decimals), "—" if r is None else fmt(r, decimals)]
        rows.append(row)
    meta = {"enter_col": None, "leave_row": step["leaving_row"]}
    blocks.append(("Base actual, B⁻¹, xB" + (" y dirección α de la variable que entra" if ratio_col else ""), header, rows, meta))
    # multiplicadores
    blocks.append(("Multiplicadores simplex  y = cB·B⁻¹",
                   [f"y{i + 1}" for i in range(m)], [[_m(v, decimals) for v in step["y"]]], meta0))
    # costos reducidos de las no básicas
    nb = [j for j in range(sf.N) if j not in basis and sf.kinds[j] != "art"]
    rows = []
    for j in nb:
        zj = step["dj"][j]
        rows.append([names[j], _m(sf.c[j], decimals), _m(sf.c[j] - zj, decimals), _m(zj, decimals)])
    meta = {"enter_col": None, "leave_row": None,
            "enter_row": nb.index(step["entering"]) if step["entering"] in nb else None}
    blocks.append(("Costos reducidos de las variables no básicas  cj − zj  (zj = y·aj)",
                   ["Variable", "cj", "zj", "cj − zj"], rows, meta))
    return blocks


def step_text(sf, step, decimals=False, sense="max"):
    """Justificación en español de cada decisión de la iteración."""
    names = sf.names
    dj, e = step["dj"], step["entering"]
    out = []
    basis = step["basis"]
    cands = [j for j in range(sf.N) if j not in basis and sf.kinds[j] != "art" and dj[j].positive()]
    if e is None:
        out.append("**Prueba de optimalidad:** ningún cj − zj de las variables no básicas es positivo, "
                   "por lo tanto ninguna variable puede mejorar Z. Se llegó al final.")
        return out
    lst = ", ".join(f"{names[j]} ({_m(dj[j], decimals)})" for j in cands)
    out.append(f"**Variable que entra: {names[e]}.** Candidatas con cj − zj > 0: {lst}. "
               f"Se elige la de mayor valor ({_m(dj[e], decimals)}), porque es la que más mejora Z por unidad"
               + (" (empates: menor índice)." if len(cands) > 1 else "."))
    ratios = step["ratios"]
    if step["leaving_row"] is None:
        out.append(f"**Razón mínima:** ningún elemento de la columna de {names[e]} es positivo, no existe razón. "
                   f"{names[e]} puede crecer sin límite → problema NO ACOTADO.")
        return out
    r = step["leaving_row"]
    col = step["T"] if "T" in step else None
    parts = []
    for i, rt in enumerate(ratios):
        parts.append(f"{names[basis[i]]}: —" if rt is None else f"{names[basis[i]]}: {fmt(rt, decimals)}")
    theta = ratios[r]
    out.append("**Prueba de la razón mínima** (solo filas con elemento > 0 en la columna que entra): "
               + "; ".join(parts) + f". El mínimo es θ = {fmt(theta, decimals)}.")
    out.append(f"**Variable que sale: {names[basis[r]]}** (fila {r + 1}), la que alcanza primero el mínimo.")
    if len(step["tied"]) > 1:
        tied = ", ".join(names[basis[i]] for i in step["tied"])
        out.append(f"⚠️ Empate en la razón mínima entre {tied}: se elige la de menor índice. "
                   "La siguiente solución será **degenerada** (alguna variable básica valdrá 0).")
    out.append(f"**Pivote:** elemento {fmt(step['pivot'], decimals)} en la fila de {names[basis[r]]} y la columna de {names[e]}. "
               "Se divide la fila pivote entre el pivote y se hace 0 el resto de la columna.")
    return out
