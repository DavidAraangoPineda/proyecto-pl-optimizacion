"""Exportación de la solución paso a paso a PDF (reportlab; fuente DejaVu incluida con matplotlib)."""
import io
import os

import matplotlib
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Image, PageBreak, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from .graphical import graph_2d
from .model import SIGN_LABEL, constraints_text, objective_text
from .numbers import fmt, fmt_bound
from .render import revised_blocks, step_text, tableau_table
from .standard import standard_form_lines

_FONT = "DejaVu"
_FONT_B = "DejaVu-Bold"


def _register_fonts():
    if _FONT in pdfmetrics.getRegisteredFontNames():
        return
    d = os.path.join(matplotlib.get_data_path(), "fonts", "ttf")
    pdfmetrics.registerFont(TTFont(_FONT, os.path.join(d, "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont(_FONT_B, os.path.join(d, "DejaVuSans-Bold.ttf")))


def _esc(s):
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("**", "")


def _table(header, rows, font=7, meta=None, col_widths=None):
    data = [header] + rows
    t = Table(data, colWidths=col_widths, repeatRows=1)
    style = [
        ("FONTNAME", (0, 0), (-1, -1), _FONT), ("FONTSIZE", (0, 0), (-1, -1), font),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#dbe6f1")),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#999999")),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 2), ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]
    if meta:
        if meta.get("enter_col") is not None:
            style.append(("BACKGROUND", (meta["enter_col"], 0), (meta["enter_col"], -1), colors.HexColor("#d9f2d9")))
        if meta.get("leave_row") is not None:
            style.append(("BACKGROUND", (0, meta["leave_row"] + 1), (-1, meta["leave_row"] + 1), colors.HexColor("#fde0dc")))
        if meta.get("enter_row") is not None:
            style.append(("BACKGROUND", (0, meta["enter_row"] + 1), (-1, meta["enter_row"] + 1), colors.HexColor("#d9f2d9")))
        if meta.get("enter_col") is not None and meta.get("leave_row") is not None:
            style.append(("BACKGROUND", (meta["enter_col"], meta["leave_row"] + 1),
                          (meta["enter_col"], meta["leave_row"] + 1), colors.HexColor("#ffe08a")))
    t.setStyle(TableStyle(style))
    return t


def build_pdf(sol, decimals=False, other=None):
    """Genera el PDF (bytes) con problema, forma estándar, iteraciones, solución, gráfico y sensibilidad."""
    _register_fonts()
    p, sf = sol.problem, sol.sf
    ss = getSampleStyleSheet()
    H1 = ParagraphStyle("h1", parent=ss["Title"], fontName=_FONT_B, fontSize=16)
    H2 = ParagraphStyle("h2", parent=ss["Heading2"], fontName=_FONT_B, fontSize=12, spaceBefore=10)
    H3 = ParagraphStyle("h3", parent=ss["Heading3"], fontName=_FONT_B, fontSize=10, spaceBefore=6)
    B = ParagraphStyle("b", parent=ss["BodyText"], fontName=_FONT, fontSize=9, leading=12)
    S = ParagraphStyle("s", parent=B, fontSize=8, leading=10)

    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=landscape(A4), leftMargin=1.3 * cm, rightMargin=1.3 * cm,
                            topMargin=1.2 * cm, bottomMargin=1.2 * cm, title="Solución de programación lineal")
    el = []
    method = "Gran M (tablero)" if sol.run.method == "bigm" else "Simplex revisado"
    el += [Paragraph("Solución de programación lineal", H1),
           Paragraph(f"Método: {method}", B), Spacer(1, 4)]

    el.append(Paragraph("1. Problema", H2))
    el.append(Paragraph(_esc(objective_text(p, decimals)), B))
    el.append(Paragraph("sujeto a:", B))
    for line in constraints_text(p, decimals):
        el.append(Paragraph("&nbsp;&nbsp;" + _esc(line), B))
    el.append(Paragraph("&nbsp;&nbsp;" + _esc(", ".join(p.var_names) + " ≥ 0"), B))

    el.append(Paragraph("2. Forma estándar (holguras, excesos y artificiales)", H2))
    for n in sf.notes:
        el.append(Paragraph("• " + _esc(n), B))
    for line in standard_form_lines(p, sf, decimals):
        el.append(Paragraph(_esc(line), B))

    el.append(Paragraph("3. Iteraciones", H2))
    for st in sol.run.steps:
        last = st is sol.run.steps[-1]
        el.append(Paragraph(f"Iteración {st['k']}" + (" (final)" if last else ""), H3))
        if st["kind"] == "tableau":
            header, rows, meta = tableau_table(sf, st, decimals)
            el.append(_table(header, rows, meta=meta))
        else:
            for title, header, rows, meta in revised_blocks(sf, st, decimals):
                el.append(Paragraph(_esc(title), S))
                el.append(_table(header, rows, meta=meta))
                el.append(Spacer(1, 3))
        for line in step_text(sf, st, decimals, p.sense):
            el.append(Paragraph(_esc(line), S))

    el.append(Paragraph("4. Resultado", H2))
    for msg in sol.messages:
        el.append(Paragraph(_esc(msg), B))
    if sol.status == "optimal":
        el.append(Paragraph(f"Z = {fmt(sol.z, decimals)}", B))
        rows = [[p.var_names[j], fmt(sol.x[j], decimals)] for j in range(p.n)]
        el.append(_table(["Variable", "Valor"], rows, font=8, col_widths=[4 * cm, 4 * cm]))
        el.append(Spacer(1, 4))
        rows = [[f"R{i + 1}", SIGN_LABEL[p.signs[i]], fmt(p.b[i], decimals), t, fmt(v, decimals)]
                for i, (t, v) in enumerate(sol.slacks)]
        el.append(_table(["Restricción", "Signo", "LD", "Tipo", "Holgura / exceso"], rows, font=8))

        sn = sol.sens
        el.append(Paragraph("5. Análisis de sensibilidad", H2))
        rows = [[f"R{i + 1}", fmt(p.b[i], decimals), fmt(sn.shadow[i], decimals),
                 f"[{fmt_bound(sn.rhs_ranges[i][0], decimals)} ; {fmt_bound(sn.rhs_ranges[i][1], decimals)}]"]
                for i in range(p.m)]
        el.append(_table(["Restricción", "LD", "Precio sombra", "Rango del LD"], rows, font=8))
        el.append(Spacer(1, 4))
        rows = [[p.var_names[j], fmt(p.c[j], decimals), fmt(sn.reduced[j], decimals),
                 f"[{fmt_bound(sn.cost_ranges[j][0], decimals)} ; {fmt_bound(sn.cost_ranges[j][1], decimals)}]"]
                for j in range(p.n)]
        el.append(_table(["Variable", "Coef. en Z", "Costo reducido", "Rango del coeficiente"], rows, font=8))
        for n in sn.notes:
            el.append(Paragraph(_esc(n), S))

    if p.n == 2:
        info = graph_2d(p, sol)
        if info.figure is not None:
            el.append(PageBreak())
            el.append(Paragraph("6. Método gráfico", H2))
            img = io.BytesIO()
            info.figure.savefig(img, format="png", dpi=130)
            import matplotlib.pyplot as plt
            plt.close(info.figure)
            img.seek(0)
            el.append(Image(img, width=17 * cm, height=13.2 * cm))
            for msg in info.messages:
                el.append(Paragraph(_esc(msg), S))
    else:
        el.append(Paragraph("6. Método gráfico", H2))
        el.append(Paragraph("No aplica: el problema tiene más de dos variables.", B))

    doc.build(el)
    return buf.getvalue()
