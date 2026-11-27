"""Método gráfico para problemas de dos variables (región factible, vértices y recta de Z)."""
from dataclasses import dataclass, field
from fractions import Fraction

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Polygon  # noqa: E402

from .geometry import feasible_vertices_2d, is_unbounded_region_2d  # noqa: E402
from .model import SIGN_LABEL  # noqa: E402
from .numbers import fmt, lin_expr  # noqa: E402

# Paletas para fondo claro (interfaz en modo claro y PDF) y para fondo oscuro (modo oscuro de la interfaz).
LIGHT = {
    "bg": "white", "fg": "#222", "axis": "#444", "grid": "#b0b0b0",
    "region": "#9ecae1", "region_line": "#3182bd", "vertex": "#111", "label_bg": "white", "label_edge": "#999",
    "z": "#e6550d", "opt": "#f2b705", "empty": "#b30000", "unbounded": "#08519c",
    "lines": ["#1f77b4", "#d62728", "#2ca02c", "#9467bd", "#8c564b", "#e377c2", "#17becf", "#bcbd22"],
}
DARK = {
    "bg": "#0e1117", "fg": "#e6e6e6", "axis": "#9aa0a6", "grid": "#5f6368",
    "region": "#4a90c2", "region_line": "#7fb8e6", "vertex": "#f0f0f0", "label_bg": "#262730", "label_edge": "#5f6368",
    "z": "#ff8c42", "opt": "#ffd54f", "empty": "#ff6b6b", "unbounded": "#8ab4f8",
    "lines": ["#5aa9e6", "#ff6b6b", "#6bd66b", "#c39bff", "#e0a37a", "#ff8ad8", "#4fd6e6", "#e6e65a"],
}
COLORS = LIGHT["lines"]


@dataclass
class GraphInfo:
    applicable: bool
    vertices: list = field(default_factory=list)     # (x1, x2, Z) exactos
    bounded: bool = True
    empty: bool = False
    optimal_vertices: list = field(default_factory=list)
    messages: list = field(default_factory=list)
    figure: object = None


def _clip(poly, a1, a2, b, sign):
    """Recorta un polígono (lista de (x, y) float) con el semiplano sign·(a1x + a2y − b) ≤ 0."""
    def inside(pt):
        return sign * (a1 * pt[0] + a2 * pt[1] - b) <= 1e-12

    out = []
    for i in range(len(poly)):
        cur, nxt = poly[i], poly[(i + 1) % len(poly)]
        ci, ni = inside(cur), inside(nxt)
        if ci:
            out.append(cur)
        if ci != ni:
            f1 = sign * (a1 * cur[0] + a2 * cur[1] - b)
            f2 = sign * (a1 * nxt[0] + a2 * nxt[1] - b)
            t = f1 / (f1 - f2)
            out.append((cur[0] + t * (nxt[0] - cur[0]), cur[1] + t * (nxt[1] - cur[1])))
    return out


def _area(poly):
    return abs(sum(poly[i][0] * poly[(i + 1) % len(poly)][1] - poly[(i + 1) % len(poly)][0] * poly[i][1]
                   for i in range(len(poly)))) / 2 if len(poly) >= 3 else 0.0


def _pretty(v):
    v = Fraction(v)
    if v.denominator == 1:
        return str(v.numerator)
    if v.denominator <= 12:
        return fmt(v)
    return f"{float(v):.3f}".rstrip("0").rstrip(".")


def graph_2d(problem, solution=None, dark=False):
    """Construye la gráfica. Si n ≠ 2 devuelve GraphInfo(applicable=False) con el aviso.

    dark=True dibuja con la paleta para fondo oscuro (modo oscuro de la interfaz).
    """
    if problem.n != 2:
        return GraphInfo(False, messages=[
            f"El método gráfico no aplica: el problema tiene {problem.n} variables y solo se puede "
            "graficar con exactamente 2 variables."])

    info = GraphInfo(True)
    verts = feasible_vertices_2d(problem)
    pairs = [(row[0], row[1]) for row in problem.A]
    c1, c2 = problem.c
    info.vertices = [(x1, x2, c1 * x1 + c2 * x2) for x1, x2 in verts]
    info.empty = not verts
    info.bounded = (not info.empty) and (not is_unbounded_region_2d(problem))

    status = solution.status if solution is not None else None
    if info.empty:
        info.messages.append("La región factible es VACÍA: no existe ningún punto que cumpla todas las restricciones.")
    elif not info.bounded:
        info.messages.append("La región factible es NO ACOTADA (se extiende indefinidamente).")
    if status == "unbounded":
        info.messages.append("La función objetivo es no acotada en esta región: no hay vértice óptimo.")
    if info.vertices and status in (None, "optimal"):
        best = (max if problem.sense == "max" else min)(v[2] for v in info.vertices)
        info.optimal_vertices = [v for v in info.vertices if v[2] == best]

    # ----- ventana de dibujo
    ints = []
    for (a1, a2), b in zip(pairs, problem.b):
        if a1 != 0 and b / a1 > 0:
            ints.append(float(b / a1))
        if a2 != 0 and b / a2 > 0:
            ints.append(float(b / a2))
    vmax = max([max(float(v[0]), float(v[1])) for v in info.vertices], default=0.0)
    if info.empty:
        lim = max(ints, default=10.0) * 1.2
    elif info.bounded:
        lim = max(vmax, 1e-9) * 1.25
    else:
        lim = max([vmax] + ints, default=10.0) * 1.35
    lim = lim if lim > 0 else 10.0
    X = Y = lim

    C = DARK if dark else LIGHT
    fig, ax = plt.subplots(figsize=(8.2, 6.4), dpi=110)
    fig.patch.set_facecolor(C["bg"])
    ax.set_facecolor(C["bg"])
    for sp in ax.spines.values():
        sp.set_color(C["axis"])
    ax.tick_params(colors=C["fg"])
    ax.set_xlim(-0.06 * X, X)
    ax.set_ylim(-0.06 * Y, Y)
    ax.axhline(0, color=C["axis"], lw=1.2)
    ax.axvline(0, color=C["axis"], lw=1.2)
    ax.grid(alpha=0.25, color=C["grid"])

    # ----- región factible sombreada
    poly = [(0.0, 0.0), (X, 0.0), (X, Y), (0.0, Y)]
    for (a1, a2), s, b in zip(pairs, problem.signs, problem.b):
        fa1, fa2, fb = float(a1), float(a2), float(b)
        if s == "<=":
            poly = _clip(poly, fa1, fa2, fb, 1)
        elif s == ">=":
            poly = _clip(poly, fa1, fa2, fb, -1)
        else:
            poly = _clip(_clip(poly, fa1, fa2, fb, 1), fa1, fa2, fb, -1)
        if not poly:
            break
    has_equal = any(s == "=" for s in problem.signs)
    if poly and _area(poly) > 1e-9 * X * Y and not has_equal and not info.empty:
        ax.add_patch(Polygon(poly, closed=True, facecolor=C["region"], edgecolor="none", alpha=0.55, zorder=1,
                             label="Región factible"))
    elif info.vertices:
        pts = sorted(info.vertices, key=lambda v: (v[0], v[1]))
        ax.plot([float(v[0]) for v in pts], [float(v[1]) for v in pts], color=C["region_line"], lw=5, alpha=0.6,
                solid_capstyle="round", zorder=1, label="Región factible (segmento/punto)")

    # ----- restricciones rotuladas
    xs = [-0.06 * X, X]
    for i, ((a1, a2), s, b) in enumerate(zip(pairs, problem.signs, problem.b)):
        col = C["lines"][i % len(C["lines"])]
        lab = f"R{i + 1}: {lin_expr([a1, a2], ['x1', 'x2'])} {SIGN_LABEL[s]} {fmt(b)}"
        fa1, fa2, fb = float(a1), float(a2), float(b)
        if fa2 != 0:
            ys = [(fb - fa1 * x) / fa2 for x in xs]
            ax.plot(xs, ys, color=col, lw=1.8, label=lab, zorder=2)
        elif fa1 != 0:
            ax.plot([fb / fa1] * 2, [-0.06 * Y, Y], color=col, lw=1.8, label=lab, zorder=2)

    # ----- vértices con su Z
    opt_set = {(v[0], v[1]) for v in info.optimal_vertices}
    for k, (x1, x2, z) in enumerate(info.vertices):
        is_opt = (x1, x2) in opt_set
        ax.scatter([float(x1)], [float(x2)], s=95 if is_opt else 45, color=C["opt"] if is_opt else C["vertex"],
                   edgecolor=C["vertex"], marker="*" if is_opt else "o", zorder=5)
        dx = 0.02 * X if float(x1) < 0.75 * X else -0.02 * X
        ax.annotate(f"({_pretty(x1)}, {_pretty(x2)})\nZ = {_pretty(z)}", (float(x1), float(x2)),
                    xytext=(float(x1) + dx, float(x2) + 0.035 * Y), fontsize=8.5, zorder=6,
                    ha="left" if dx > 0 else "right", color=C["fg"],
                    bbox=dict(boxstyle="round,pad=0.2", fc=C["label_bg"], ec=C["label_edge"], alpha=0.85))

    # ----- recta de la función objetivo (isoutilidad) en el óptimo
    if info.optimal_vertices and status != "unbounded" and (c1 != 0 or c2 != 0):
        ox1, ox2, oz = info.optimal_vertices[0]
        fc1, fc2, foz = float(c1), float(c2), float(oz)
        if fc2 != 0:
            ys = [(foz - fc1 * x) / fc2 for x in xs]
            ax.plot(xs, ys, "--", color=C["z"], lw=2.2, zorder=4, label=f"Z = {_pretty(oz)} (óptimo)")
        else:
            ax.plot([foz / fc1] * 2, [-0.06 * Y, Y], "--", color=C["z"], lw=2.2, zorder=4,
                    label=f"Z = {_pretty(oz)} (óptimo)")
        if len(info.optimal_vertices) > 1:
            pa, pb = info.optimal_vertices[0], info.optimal_vertices[-1]
            ax.plot([float(pa[0]), float(pb[0])], [float(pa[1]), float(pb[1])], color=C["opt"], lw=6, alpha=0.8,
                    zorder=3, label="Segmento de óptimos múltiples")
        # dirección de mejora
        sgn = 1 if problem.sense == "max" else -1
        norm = (fc1 ** 2 + fc2 ** 2) ** 0.5
        L = 0.12 * X
        ax.annotate("", xy=(float(ox1) + sgn * L * fc1 / norm, float(ox2) + sgn * L * fc2 / norm),
                    xytext=(float(ox1), float(ox2)),
                    arrowprops=dict(arrowstyle="->", color=C["z"], lw=2), zorder=6)

    if info.empty:
        ax.text(0.5, 0.5, "REGIÓN FACTIBLE VACÍA", transform=ax.transAxes, ha="center", va="center", fontsize=18,
                color=C["empty"], alpha=0.9, bbox=dict(boxstyle="round", fc=C["bg"], ec=C["empty"]))
    elif not info.bounded:
        ax.text(0.98, 0.02, "Región no acotada →", transform=ax.transAxes, ha="right", va="bottom", fontsize=10,
                color=C["unbounded"])

    ax.set_xlabel("x1", color=C["fg"])
    ax.set_ylabel("x2", color=C["fg"])
    sense = "Max" if problem.sense == "max" else "Min"
    ax.set_title(f"Método gráfico — {sense} Z = {lin_expr(problem.c, ['x1', 'x2'])}", color=C["fg"])
    leg = ax.legend(loc="upper right", fontsize=8, framealpha=0.9, facecolor=C["label_bg"], edgecolor=C["label_edge"])
    for t in leg.get_texts():
        t.set_color(C["fg"])
    fig.tight_layout()
    info.figure = fig
    return info
