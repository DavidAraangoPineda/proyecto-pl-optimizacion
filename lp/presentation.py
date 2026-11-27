"""Exporta la corrida del motor propio a datos para la presentación cinematográfica (presentacion/).

Todo lo que la presentación muestra (tableros, razones, vértices, recorrido, sensibilidad) sale de
este módulo, es decir, del método propio. La presentación solo lo anima.

Uso:
    python -m lp.presentation            # regenera presentacion/js/datos.js con los ejemplos
    presentation_html(problema)          # HTML autónomo (un solo archivo) para un problema
"""
import json
import math
import re
from fractions import Fraction
from itertools import combinations
from pathlib import Path

from .geometry import feasible_vertices_2d, is_unbounded_region_2d
from .model import EXAMPLES, SIGN_LABEL, Problem, constraints_text, objective_text
from .numbers import fmt, fmt_bound, lin_expr
from .render import revised_blocks, step_text, tableau_table
from .solver import solve
from .standard import standard_form_lines

ROOT = Path(__file__).resolve().parent.parent
PRES = ROOT / "presentacion"


def _f(x):
    return float(x)


def _md(s):
    """**negrita** → <b>negrita</b> (los subtítulos de la presentación usan HTML)."""
    return re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", s)


def _plain(s):
    return re.sub(r"\*\*(.+?)\*\*", r"\1", s).replace("⚠️ ", "")


def _z_orig(p, z):
    """Valor de Z en el sentido original si no tiene parte M; si no, texto de Z'."""
    if z.b == 0:
        v = z.a if p.sense == "max" else -z.a
        return {"txt": fmt(v), "num": _f(v), "conM": False}
    return {"txt": z.fmt(), "num": None, "conM": True}


# ---------------------------------------------------------------- geometría

def _graph2(p, sol):
    verts = feasible_vertices_2d(p)
    c1, c2 = p.c
    vs = [(x, y, c1 * x + c2 * y) for x, y in verts]
    empty = not verts
    bounded = (not empty) and not is_unbounded_region_2d(p)
    opt = []
    if vs and sol.status == "optimal":
        best = (max if p.sense == "max" else min)(v[2] for v in vs)
        opt = [v for v in vs if v[2] == best]
    ints = []
    for (a1, a2), b in zip(((r[0], r[1]) for r in p.A), p.b):
        if a1 != 0 and b / a1 > 0:
            ints.append(_f(b / a1))
        if a2 != 0 and b / a2 > 0:
            ints.append(_f(b / a2))
    vmax = max([max(_f(v[0]), _f(v[1])) for v in vs], default=0.0)
    if empty:
        lim = max(ints, default=10.0) * 1.2
    elif bounded:
        lim = max(vmax, 1e-9) * 1.3
    else:
        lim = max([vmax] + ints, default=10.0) * 1.4
    lim = lim if lim > 0 else 10.0
    # restricciones redundantes: ningún vértice factible las toca (y no es de igualdad)
    rectas = []
    for i, ((a1, a2), s, b) in enumerate(zip(((r[0], r[1]) for r in p.A), p.signs, p.b)):
        toca = any(a1 * x + a2 * y == b for x, y, _ in vs)
        rectas.append({"a1": _f(a1), "a2": _f(a2), "b": _f(b), "signo": s,
                       "txt": f"R{i + 1}: {lin_expr([a1, a2], ['x1', 'x2'])} {SIGN_LABEL[s]} {fmt(b)}",
                       "redundante": bool(vs) and not toca})
    return {
        "lim": lim, "acotada": bounded, "vacia": empty, "rectas": rectas,
        "vertices": [{"x": _f(x), "y": _f(y), "z": _f(z), "xs": fmt(x), "ys": fmt(y), "zs": fmt(z),
                      "opt": any(v[0] == x and v[1] == y for v in opt)} for x, y, z in vs],
        "c": [_f(c1), _f(c2)],
    }


def _graph3(p, sol):
    """Poliedro factible en 3D: vértices, aristas y caras (recortado con una caja si es no acotado)."""
    planes = [(list(p.A[i]), p.signs[i], p.b[i]) for i in range(p.m)]
    for j in range(3):
        e = [Fraction(0)] * 3
        e[j] = Fraction(-1)
        planes.append((e, "<=", Fraction(0)))       # -x_j <= 0

    def feasible(x, pl):
        for a, s, b in pl:
            v = sum(ai * xi for ai, xi in zip(a, x))
            if (s == "<=" and v > b) or (s == ">=" and v < b) or (s == "=" and v != b):
                return False
        return True

    def enum(pl):
        pts = {}
        for i, j, k in combinations(range(len(pl)), 3):
            M = [pl[i][0], pl[j][0], pl[k][0]]
            rhs = [pl[i][2], pl[j][2], pl[k][2]]
            det = _det3(M)
            if det == 0:
                continue
            x = []
            for col in range(3):
                Mc = [row[:] for row in M]
                for r in range(3):
                    Mc[r][col] = rhs[r]
                x.append(_det3(Mc) / det)
            if feasible(x, pl):
                pts[tuple(x)] = True
        return list(pts)

    verts = enum(planes)
    clipped = False
    if not verts:
        return {"vacia": True}
    L = max(max(_f(v) for v in pt) for pt in verts)
    L = (L if L > 0 else 10) * 1.0
    # ¿es no acotado? se prueba si al agregar una caja más grande aparecen vértices nuevos
    big = planes + [([Fraction(int(r == j)) for r in range(3)], "<=", Fraction(int(math.ceil(L * 2 + 1))))
                    for j in range(3)]
    vb = enum(big)
    if len(vb) != len(verts) or any(v not in verts for v in vb):
        clipped = True
        Lc = Fraction(int(math.ceil(L * 1.6 + 1)))
        planes = planes + [([Fraction(int(r == j)) for r in range(3)], "<=", Lc) for j in range(3)]
        verts = enum(planes)

    def active(pt, pl):
        a, s, b = pl
        return sum(ai * xi for ai, xi in zip(a, pt)) == b

    idx = {v: k for k, v in enumerate(verts)}
    edges = []
    for u, v in combinations(verts, 2):
        common = [k for k, pl in enumerate(planes) if active(u, pl) and active(v, pl)]
        if len(common) >= 2:
            edges.append([idx[u], idx[v]])
    faces = []
    for k, pl in enumerate(planes):
        on = [v for v in verts if active(v, pl)]
        if len(on) < 3:
            continue
        cx = [sum(_f(v[t]) for v in on) / len(on) for t in range(3)]
        n = [_f(a) for a in pl[0]]
        nn = math.sqrt(sum(t * t for t in n)) or 1
        n = [t / nn for t in n]
        ref = [1, 0, 0] if abs(n[0]) < 0.9 else [0, 1, 0]
        u = _cross(n, ref)
        w = _cross(n, u)
        on.sort(key=lambda v: math.atan2(sum((_f(v[t]) - cx[t]) * w[t] for t in range(3)),
                                         sum((_f(v[t]) - cx[t]) * u[t] for t in range(3))))
        tipo = "eje" if k >= p.m and k < p.m + 3 else ("caja" if k >= p.m + 3 else "r")
        faces.append({"v": [idx[v] for v in on], "r": k if k < p.m else -1, "tipo": tipo})
    vs = []
    for v in verts:
        z = sum(ci * xi for ci, xi in zip(p.c, v))
        vs.append({"p": [_f(t) for t in v], "s": [fmt(t) for t in v], "z": fmt(z)})
    lim = max(max(_f(t) for t in v) for v in verts) or 10
    return {"vacia": False, "vertices": vs, "aristas": edges, "caras": faces, "lim": lim, "acotada": not clipped}


def _det3(M):
    return (M[0][0] * (M[1][1] * M[2][2] - M[1][2] * M[2][1])
            - M[0][1] * (M[1][0] * M[2][2] - M[1][2] * M[2][0])
            + M[0][2] * (M[1][0] * M[2][1] - M[1][1] * M[2][0]))


def _cross(a, b):
    return [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]]


# ---------------------------------------------------------------- sensibilidad animada

def _rhs_animation(p, sol):
    """Mueve el LD de una restricción con precio sombra ≠ 0 y re-resuelve con el método propio."""
    if p.n != 2 or sol.status != "optimal":
        return None
    sn = sol.sens
    cands = [i for i in range(p.m) if sn.shadow[i] != 0]
    if not cands:
        return None
    i = max(cands, key=lambda k: abs(sn.shadow[k]))
    lo, hi = sn.rhs_ranges[i]
    b0 = p.b[i]
    span = max(abs(b0) * Fraction(1, 2), Fraction(1))
    a = lo if lo is not None else b0 - span
    z = hi if hi is not None else b0 + span
    width = z - a if z > a else span
    start, end = a - width * Fraction(1, 4), z + width * Fraction(1, 4)
    frames = []
    n1 = n2 = 24      # el valor actual b0 queda exactamente en un cuadro
    valores = ([start + (b0 - start) * Fraction(k, n1) for k in range(n1)]
               + [b0 + (end - b0) * Fraction(k, n2) for k in range(n2 + 1)])
    for bk in valores:
        b2 = list(p.b)
        b2[i] = bk
        q = Problem(p.sense, p.c, p.A, p.signs, b2)
        s = solve(q, "bigm")
        inside = (lo is None or bk >= lo) and (hi is None or bk <= hi)
        frames.append({
            "b": _f(bk), "bs": fmt(bk) if Fraction(bk).denominator <= 4 else f"{float(bk):.2f}".rstrip("0").rstrip("."),
            "estado": s.status, "dentro": inside,
            "x": [_f(v) for v in s.x] if s.x else None,
            "z": _f(s.z) if s.z is not None else None,
            "base": [s.sf.names[j] for j in s.final_basis] if s.final_basis else None,
        })
    return {"restr": i, "b0": _f(b0), "b0s": fmt(b0), "precio": fmt(sn.shadow[i]), "preciof": _f(sn.shadow[i]),
            "lo": fmt_bound(lo), "hi": fmt_bound(hi), "lof": None if lo is None else _f(lo),
            "hif": None if hi is None else _f(hi), "frames": frames}


# ---------------------------------------------------------------- simplex revisado

def _revised(p, bigm_sol):
    """Corrida del simplex revisado (B⁻¹, multiplicadores y costos reducidos) y comparación con la Gran M."""
    sol = solve(p, "revised")
    sf = sol.sf
    names = sf.names
    steps = []
    for st in sol.run.steps:
        basis = st["basis"]
        x = [Fraction(0)] * p.n
        arts = False
        for i, j in enumerate(basis):
            if j < p.n:
                x[j] = st["xB"][i]
            if sf.kinds[j] == "art" and st["xB"][i] > 0:
                arts = True
        e, r = st["entering"], st["leaving_row"]
        steps.append({
            "k": st["k"], "base": [names[j] for j in basis],
            "bloques": [{"titulo": t, "header": h, "rows": rows, "meta": meta}
                        for t, h, rows, meta in revised_blocks(sf, st)],
            "y": [v.fmt() for v in st["y"]],
            "entra": None if e is None else names[e], "dj": None if e is None else st["dj"][e].fmt(),
            "sale": None if r is None else names[basis[r]],
            "pivote": None if st["pivot"] is None else fmt(st["pivot"]),
            "theta": None if r is None else fmt(st["ratios"][r]),
            "z": st["z"].fmt(), "zOrig": _z_orig(p, st["z"]),
            "x": [_f(v) for v in x], "xs": [fmt(v) for v in x], "factible": not arts,
        })
    a, b = bigm_sol, sol
    iguales = (a.status == b.status and a.z == b.z and a.x == b.x
               and [s["basis"] for s in a.run.steps] == [s["basis"] for s in b.run.steps])
    return {"pasos": steps, "estado": sol.status, "iguales": iguales,
            "x": [fmt(v) for v in sol.x] if sol.x else None, "z": fmt(sol.z) if sol.z is not None else None}


# ---------------------------------------------------------------- escena completa

def scene(p, method="bigm"):
    sol = solve(p, method)
    sf = sol.sf
    names = sf.names
    steps = []
    for st in sol.run.steps:
        header, rows, meta = tableau_table(sf, st)
        basis = st["basis"]
        rhs = st["rhs"]
        x = [Fraction(0)] * p.n
        arts = {}
        for i, j in enumerate(basis):
            if j < p.n:
                x[j] = rhs[i]
            if sf.kinds[j] == "art":
                arts[names[j]] = _f(rhs[i])
        e = st["entering"]
        r = st["leaving_row"]
        steps.append({
            "k": st["k"], "base": [names[j] for j in basis], "header": header, "rows": rows, "meta": meta,
            "entra": None if e is None else names[e], "entraIdx": e,
            "sale": None if r is None else names[basis[r]], "filaSale": r,
            "pivote": None if st["pivot"] is None else fmt(st["pivot"]),
            "dj": None if e is None else st["dj"][e].fmt(),
            "djM": None if e is None else st["dj"][e].b != 0,
            "razones": None if st["ratios"] is None else [
                {"var": names[basis[i]], "txt": "—" if rt is None else fmt(rt), "val": None if rt is None else _f(rt),
                 "num": fmt(rhs[i]), "den": fmt(st["T"][i][e])}
                for i, rt in enumerate(st["ratios"])],
            "empate": [names[basis[i]] for i in st["tied"]] if len(st["tied"]) > 1 else [],
            "z": st["z"].fmt(), "zOrig": _z_orig(p, st["z"]),
            "x": [_f(v) for v in x], "xs": [fmt(v) for v in x],
            "factible": not any(v > 0 for v in arts.values()), "arts": arts,
            "textos": [_md(t) for t in step_text(sf, st, False, p.sense)],
        })
    rows_std = []
    for i in range(p.m):
        added = [{"nombre": names[j], "tipo": sf.kinds[j], "coef": fmt(sf.A[i][j])}
                 for j in range(p.n, sf.N) if sf.A[i][j] != 0]
        rows_std.append({
            "orig": constraints_text(p)[i].split(": ", 1)[1], "signo": SIGN_LABEL[p.signs[i]],
            "flip": sf.flipped[i],
            "normal": f"{lin_expr(sf.A[i][:p.n], p.var_names)} {SIGN_LABEL[_norm_sign(p.signs[i], sf.flipped[i])]} {fmt(sf.b[i])}",
            "agregadas": added,
            "ecuacion": standard_form_lines(p, sf)[1 + i].split(":  ", 1)[1],
        })
    d = {
        "nombre": p.name or "Problema", "sentido": p.sense, "n": p.n, "m": p.m, "vars": p.var_names,
        "objetivo": objective_text(p), "restricciones": constraints_text(p),
        "metodo": "Gran M (tablero)" if method == "bigm" else "Simplex revisado",
        "estandar": {"lineas": standard_form_lines(p, sf), "notas": sf.notes, "nombres": names,
                     "tipos": sf.kinds, "filas": rows_std, "base0": [names[j] for j in sf.basis0],
                     "tieneArt": sf.has_artificial},
        "pasos": steps, "estado": sol.status,
        "mensajes": [_plain(m) for m in sol.messages] + list(sol.run.notes),
        "x": [fmt(v) for v in sol.x] if sol.x else None, "z": fmt(sol.z) if sol.z is not None else None,
        "holguras": [{"tipo": t, "valor": fmt(v)} for t, v in sol.slacks] if sol.slacks else None,
        "alternos": [[fmt(v) for v in xs] for xs in sol.alt_vertices], "altVars": sol.alt_vars,
        "degeneradas": sol.degenerate_vars, "empates": sol.tie_iterations,
        "noAcotadaVar": names[sol.run.unbounded_col] if sol.run.unbounded_col is not None else None,
        "revisado": _revised(p, sol),
    }
    if sol.run.unbounded_col is not None and p.n == 2:
        # dirección en la que se escapa la solución (para dibujar la flecha al infinito)
        last = sol.run.steps[-1]
        e = sol.run.unbounded_col
        dirx = [Fraction(0)] * p.n
        if e < p.n:
            dirx[e] = Fraction(1)
        for i, j in enumerate(last["basis"]):
            if j < p.n:
                dirx[j] = -last["T"][i][e]
        d["rayo"] = [_f(v) for v in dirx]
    if sol.status == "optimal":
        sn = sol.sens
        d["sensibilidad"] = {
            "restr": [{"nombre": f"R{i + 1}", "ld": fmt(p.b[i]), "precio": fmt(sn.shadow[i]),
                       "lo": fmt_bound(sn.rhs_ranges[i][0]), "hi": fmt_bound(sn.rhs_ranges[i][1]),
                       "activa": sol.slacks[i][1] == 0} for i in range(p.m)],
            "vars": [{"nombre": p.var_names[j], "valor": fmt(sol.x[j]), "basica": sn.basic[j],
                      "coef": fmt(p.c[j]), "reducido": fmt(sn.reduced[j]),
                      "lo": fmt_bound(sn.cost_ranges[j][0]), "hi": fmt_bound(sn.cost_ranges[j][1])}
                     for j in range(p.n)],
            "animacion": _rhs_animation(p, sol),
        }
    if p.n == 2:
        d["grafico"] = _graph2(p, sol)
    elif p.n == 3:
        d["poliedro"] = _graph3(p, sol)
    return d


def _norm_sign(s, flipped):
    return {"<=": ">=", ">=": "<=", "=": "="}[s] if flipped else s


def _example(k):
    return EXAMPLES[next(x for x in EXAMPLES if x.startswith(f"{k}."))]


def all_data(main=None):
    """Datos completos: escena principal + ejemplos + casos especiales para el capítulo 6."""
    ejemplos = {k: scene(p) for k, p in EXAMPLES.items()}
    keys = list(EXAMPLES)
    return {
        "principal": scene(main) if main is not None else ejemplos[keys[0]],
        "ejemplos": ejemplos,
        "casos": {"infactible": ejemplos[keys[3]], "noAcotado": ejemplos[keys[4]],
                  "multiples": ejemplos[keys[5]], "degenerado": ejemplos[keys[6]],
                  "artificiales": ejemplos[keys[1]]},
    }


def datos_js(main=None):
    return "window.DATOS_PL = " + json.dumps(all_data(main), ensure_ascii=False) + ";\n"


def presentation_html(problem):
    """Un solo archivo HTML con la presentación y los datos del problema (funciona sin internet)."""
    html = (PRES / "index.html").read_text(encoding="utf-8")
    css = (PRES / "css" / "estilos.css").read_text(encoding="utf-8")
    html = html.replace('<link rel="stylesheet" href="css/estilos.css">', f"<style>\n{css}\n</style>")
    for name in ("audio.js", "dibujo.js", "app.js"):
        js = (PRES / "js" / name).read_text(encoding="utf-8")
        html = html.replace(f'<script src="js/{name}"></script>', f"<script>\n{js}\n</script>")
    data = datos_js(problem).replace("</", "<\\/")
    html = html.replace('<script src="js/datos.js"></script>', f"<script>\n{data}</script>")
    return html


if __name__ == "__main__":
    (PRES / "js" / "datos.js").write_text(datos_js(), encoding="utf-8")
    print("presentacion/js/datos.js regenerado")
