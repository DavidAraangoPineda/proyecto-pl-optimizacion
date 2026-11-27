"""Genera docs/Sprint1_Propuesta.pdf (informe de la propuesta del Sprint 1).

Uso:  python docs/generar_informe_sprint1.py
"""
import io
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch  # noqa: E402
from reportlab.lib import colors  # noqa: E402
from reportlab.lib.pagesizes import letter  # noqa: E402
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet  # noqa: E402
from reportlab.lib.units import cm  # noqa: E402
from reportlab.platypus import (Image, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,  # noqa: E402
                                Spacer, Table, TableStyle)

from lp.graphical import graph_2d  # noqa: E402
from lp.model import EXAMPLES  # noqa: E402
from lp.numbers import fmt  # noqa: E402
from lp.pdf_export import FONT, FONT_BOLD, register_fonts  # noqa: E402
from lp.solver import solve  # noqa: E402

AZUL = colors.HexColor("#1f4e79")
CLARO = colors.HexColor("#dbe6f1")


def boceto_png():
    """Boceto (wireframe) de la interfaz."""
    fig, ax = plt.subplots(figsize=(10, 6.2), dpi=150)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 62)
    ax.axis("off")

    def caja(x, y, w, h, txt="", fc="#ffffff", ec="#555", fs=8, bold=False, ha="center"):
        ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.25", fc=fc, ec=ec, lw=1))
        if txt:
            tx = x + w / 2 if ha == "center" else x + 1
            ax.text(tx, y + h / 2, txt, ha=ha, va="center", fontsize=fs, weight="bold" if bold else "normal")

    caja(0, 0, 100, 62, fc="#f7f9fc", ec="#333")
    # barra lateral
    caja(1, 1, 22, 60, fc="#eef2f7")
    ax.text(12, 58, "Opciones", ha="center", fontsize=10, weight="bold")
    items = ["Método:\n◉ Gran M   ○ Revisado", "Modo:\n◉ Paso a paso  ○ Directa",
             "Números:\n◉ Fracciones ○ Decimales", "Cargar ejemplo ▾", "Cargar JSON ⬆"]
    for k, t in enumerate(items):
        caja(2.5, 48 - k * 8.5, 19, 6.5, t, fs=7.5)
    # zona principal
    ax.text(25, 58, "Programación Lineal", fontsize=13, weight="bold")
    ax.text(25, 54.5, "1. Problema     ◉ Maximizar   ○ Minimizar", fontsize=9)
    ax.text(25, 51.3, "Coeficientes de Z", fontsize=8, color="#444")
    for j in range(3):
        caja(25 + j * 9, 47, 8, 3.2, f"x{j + 1}", fs=8)
    ax.text(25, 44, "Restricciones", fontsize=8, color="#444")
    for i in range(3):
        for j in range(3):
            caja(25 + j * 9, 39.5 - i * 4, 8, 3.2, "", fs=7)
        caja(52, 39.5 - i * 4, 6, 3.2, ["≤", "≥", "="][i] + " ▾", fs=8)
        caja(59.5, 39.5 - i * 4, 8, 3.2, "LD", fs=8)
    for k, t in enumerate(["+ Variable", "− Variable", "+ Restricción", "− Restricción"]):
        caja(25 + k * 12.5, 25.5, 11.5, 3.2, t, fs=7.5)
    caja(76, 25.5, 10, 3.2, "▶ Resolver", fc="#ff4b4b", ec="#c00", fs=8, bold=True)
    caja(87.5, 25.5, 11, 3.2, "Guardar JSON", fs=7.5)
    ax.text(25, 21.5, "2. Resultados", fontsize=9, weight="bold")
    tabs = ["Resultado", "Paso a paso", "Gráfico", "Sensibilidad", "Comparar", "Exportar PDF"]
    for k, t in enumerate(tabs):
        caja(25 + k * 12.3, 16.8, 11.5, 3.2, t, fc="#dbe6f1" if k == 1 else "#fff", fs=7.5)
    caja(25, 1.5, 73.5, 14, "", fc="#ffffff")
    ax.text(27, 13, "Tablero de la iteración: columna que entra (verde), fila que sale (rojo), pivote (amarillo)",
            fontsize=7.5, color="#333")
    for r in range(4):
        for c in range(9):
            col = "#fff"
            if c == 3:
                col = "#d9f2d9"
            if r == 1:
                col = "#fde0dc"
            if r == 1 and c == 3:
                col = "#ffd54f"
            ax.add_patch(plt.Rectangle((27 + c * 7.6, 9.5 - r * 2.0), 7.4, 1.8, fc=col, ec="#999", lw=0.5))
    ax.text(27, 2.5, "Justificación: entra x2 (mayor cj − zj), razón mínima = 30 → sale s2, pivote = 3",
            fontsize=7.5, style="italic", color="#333")
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    return buf


def grafico_ej1_png():
    p = list(EXAMPLES.values())[0]
    info = graph_2d(p, solve(p))
    buf = io.BytesIO()
    info.figure.savefig(buf, format="png", dpi=120, bbox_inches="tight")
    plt.close(info.figure)
    buf.seek(0)
    return buf


def tabla(data, widths, header=True):
    t = Table(data, colWidths=widths, repeatRows=1 if header else 0)
    st = [("FONTNAME", (0, 0), (-1, -1), FONT), ("FONTSIZE", (0, 0), (-1, -1), 9),
          ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#9aa9b8")),
          ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
          ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]
    if header:
        st += [("BACKGROUND", (0, 0), (-1, 0), CLARO), ("FONTNAME", (0, 0), (-1, 0), FONT_BOLD)]
    t.setStyle(TableStyle(st))
    return t


def main():
    register_fonts()
    ss = getSampleStyleSheet()
    T = ParagraphStyle("t", parent=ss["Title"], fontName=FONT_BOLD, fontSize=17, textColor=AZUL, leading=21)
    ST = ParagraphStyle("st", parent=ss["Normal"], fontName=FONT, fontSize=10, alignment=1, leading=14)
    H = ParagraphStyle("h", parent=ss["Heading2"], fontName=FONT_BOLD, fontSize=13, textColor=AZUL,
                       spaceBefore=12, spaceAfter=4)
    B = ParagraphStyle("b", parent=ss["BodyText"], fontName=FONT, fontSize=10, leading=14)
    L = ParagraphStyle("l", parent=B, leftIndent=12, bulletIndent=0)
    P = lambda s: Paragraph(s, B)  # noqa: E731
    cell = ParagraphStyle("c", parent=B, fontSize=9, leading=11.5)
    C = lambda s: Paragraph(s, cell)  # noqa: E731

    out = ROOT / "docs" / "Sprint1_Propuesta.pdf"
    doc = SimpleDocTemplate(str(out), pagesize=letter, leftMargin=2.2 * cm, rightMargin=2.2 * cm,
                            topMargin=1.8 * cm, bottomMargin=1.8 * cm,
                            title="Sprint 1 - Propuesta - Aplicación de Programación Lineal",
                            author="David Arango Pineda, Juan Ignacio Parra")
    el = [
        Paragraph("Universidad de Antioquia – Facultad de Ingeniería<br/>Departamento de Ingeniería de Sistemas · Optimización", ST),
        Spacer(1, 10),
        Paragraph("Sprint 1 – Propuesta<br/>Aplicación de Programación Lineal", T),
        Paragraph("18 de noviembre de 2026", ST),
        Spacer(1, 6),
        Paragraph("Repositorio: github.com/DavidAraangoPineda/proyecto-pl-optimizacion", ST),
        Spacer(1, 10),
    ]

    el.append(Paragraph("1. Qué se debe mostrar en este sprint", H))
    el.append(P("Según el cronograma del enunciado, la entrega de la <b>Semana 1 – Propuesta</b> comprende: "
                "<b>lenguaje, método elegido, integrantes y boceto de la interfaz</b>. Este informe cubre esos cuatro "
                "puntos y agrega el plan de los siguientes sprints y el estado actual del desarrollo."))
    el.append(Spacer(1, 4))
    el.append(tabla([
        ["Punto exigido", "Respuesta del equipo", "Sección"],
        ["Integrantes", C("David Arango Pineda · Juan Ignacio Parra"), "2"],
        ["Lenguaje", C("Python 3 con interfaz web en Streamlit"), "3"],
        ["Método elegido", C("Gran M (principal) + simplex revisado (bonificación)"), "4"],
        ["Boceto de la interfaz", C("Wireframe de la pantalla principal y sus pestañas"), "5"],
    ], [4 * cm, 9.6 * cm, 2 * cm]))

    el.append(Paragraph("2. Integrantes", H))
    el.append(tabla([
        ["Integrante", "Responsabilidad principal", "Respaldo"],
        ["David Arango Pineda", C("Motor: forma estándar, Gran M y simplex revisado; método gráfico; exportación a PDF"), "Juan Ignacio"],
        ["Juan Ignacio Parra", C("Interfaz y validación de la entrada; casos especiales; análisis de sensibilidad"), "David"],
    ], [4 * cm, 9 * cm, 2.6 * cm]))
    el.append(Spacer(1, 3))
    el.append(P("Cada integrante revisa también la parte del otro, porque en la sustentación el docente elige qué "
                "parte del código debe explicar cada uno."))

    el.append(Paragraph("3. Lenguaje y tecnologías", H))
    el.append(tabla([
        ["Componente", "Tecnología", "Por qué"],
        ["Lenguaje", "Python 3", C("Legible, conocido por ambos integrantes; buen soporte numérico y gráfico.")],
        ["Interfaz gráfica", "Streamlit (web)", C("Interfaz web con tablas editables, pestañas y descargas; se ejecuta con un solo comando.")],
        ["Aritmética", "fractions.Fraction", C("Fracciones exactas en todo el paso a paso: sin errores de redondeo (bonificación +0.1).")],
        ["Método gráfico", "matplotlib", C("Región factible sombreada, rectas rotuladas, vértices y recta de Z.")],
        ["PDF", "reportlab", C("Exportar la solución paso a paso a PDF (bonificación +0.1).")],
        ["Verificación", "pytest + scipy", C("scipy se usa <b>solo en las pruebas</b> para verificar; nunca para producir resultados.")],
    ], [3.3 * cm, 3.7 * cm, 8.6 * cm]))

    el.append(Paragraph("4. Método elegido", H))
    el.append(P("<b>Método principal: Gran M sobre tablero.</b> Se pasa el problema a forma estándar (holguras para ≤, "
                "exceso + artificial para ≥, artificial para =; las filas con lado derecho negativo se multiplican por −1). "
                "Las artificiales se penalizan con −M. M se maneja <b>simbólicamente</b> como números a + b·M, sin "
                "asignarle un valor numérico."))
    el.append(Spacer(1, 3))
    el.append(P("<b>Segundo método: simplex revisado</b> con B⁻¹ explícita, para comparar sus iteraciones con las de la "
                "Gran M (bonificación +0.2)."))
    el.append(Spacer(1, 3))
    el.append(P("<b>Reglas de decisión</b> (las mismas en ambos métodos):"))
    for t in ["Entra la variable con el mayor cj − zj positivo (empates: menor índice).",
              "Sale la variable con la menor razón b<sub>i</sub>/a<sub>ie</sub> (a<sub>ie</sub> &gt; 0); un empate indica degeneración.",
              "Óptimo cuando ningún cj − zj es positivo; infactible si queda una artificial positiva; "
              "no acotado si la columna que entra no tiene elementos positivos.",
              "Óptimos múltiples: una variable no básica con cj − zj = 0 en el óptimo."]:
        el.append(Paragraph(t, L, bulletText="•"))

    el.append(PageBreak())
    el.append(Paragraph("5. Boceto de la interfaz", H))
    el.append(P("Pantalla única: a la izquierda las opciones (método, modo directo o paso a paso, formato de números, "
                "cargar ejemplos o archivos); al centro la entrada del problema con botones para agregar o quitar "
                "variables y restricciones; abajo los resultados organizados en pestañas."))
    el.append(Spacer(1, 4))
    el.append(Image(boceto_png(), width=16.5 * cm, height=10.2 * cm))
    el.append(Spacer(1, 4))
    el.append(tabla([
        ["Pestaña", "Contenido"],
        ["Resultado", C("Valor de cada variable, Z, holgura o exceso de cada restricción y mensajes de casos especiales.")],
        ["Paso a paso", C("Forma estándar y cada iteración: entrante, razón mínima, saliente, pivote y tablero (o B⁻¹), con justificación.")],
        ["Gráfico", C("Solo con 2 variables: región factible, restricciones rotuladas, vértices con Z, recta de Z en el óptimo.")],
        ["Sensibilidad", C("Precios sombra, costos reducidos, rangos de coeficientes y de lados derechos, con interpretación.")],
        ["Comparar", C("Iteraciones de la Gran M y del simplex revisado lado a lado.")],
        ["Exportar", C("PDF de la solución paso a paso. Además: guardar y cargar problemas en JSON.")],
    ], [3.3 * cm, 12.3 * cm]))

    el.append(PageBreak())
    el.append(Paragraph("6. Plan de sprints", H))
    el.append(tabla([
        ["Sprint", "Fecha", "Entrega"],
        ["1 – Propuesta", "18 nov 2026", C("Lenguaje, método, integrantes, boceto de la interfaz (este informe).")],
        ["2 – Avance", "27 nov 2026", C("Entrada del problema y método resolviendo problemas como el 1 y el 3 del enunciado.")],
        ["3 – Final", "4 dic 2026", C("Paso a paso, gráfico, sensibilidad, casos especiales, manual de usuario, video y sustentación.")],
    ], [3.2 * cm, 2.8 * cm, 9.6 * cm]))

    el.append(Paragraph("7. Estado actual (adelanto)", H))
    el.append(P("El desarrollo va adelantado respecto al cronograma: ya existe un prototipo funcional en el repositorio. "
                "Resultados del motor propio con los problemas de ejemplo del enunciado:"))
    el.append(Spacer(1, 4))
    rows = [["#", "Caso", "Resultado obtenido", "Esperado"]]
    esperado = ["x₁=42, x₂=16, Z=3380", "x₁=2/5, x₂=9/5, Z=17/5", "x=(0,100,230), Z=1350",
                "Infactible", "No acotado", "Z=10 entre (0,5/2) y (3,1)", "x₁=0, x₂=2, Z=18, degenerado"]
    for k, (name, p) in enumerate(EXAMPLES.items()):
        s = solve(p)
        if s.status == "optimal":
            got = "x = (" + ", ".join(fmt(v) for v in s.x) + f"), Z = {fmt(s.z)}"
            if s.alternative_optima:
                got += " · óptimos múltiples"
            if s.degenerate:
                got += " · degenerado"
        else:
            got = {"infeasible": "Infactible", "unbounded": "No acotado"}[s.status]
        rows.append([str(k + 1), C(name.split(". ", 1)[1]), C(got), C(esperado[k])])
    el.append(tabla(rows, [0.8 * cm, 4.6 * cm, 5.6 * cm, 4.6 * cm]))
    el.append(Spacer(1, 4))
    el.append(P("Además, 400 problemas aleatorios se verificaron contra scipy con ambos métodos (19 pruebas automáticas "
                "aprobadas). Ejemplo del método gráfico generado por la aplicación (problema 1):"))
    el.append(Spacer(1, 4))
    el.append(Image(grafico_ej1_png(), width=9.4 * cm, height=7.3 * cm))

    el.append(PageBreak())
    el.append(Paragraph("8. Guion sugerido para la presentación (5 minutos)", H))
    guion = [
        ("0:00 – 0:30", "Presentar al equipo y el objetivo de la aplicación."),
        ("0:30 – 1:30", "Lenguaje y tecnologías (sección 3): por qué Python + Streamlit y por qué fracciones exactas."),
        ("1:30 – 2:30", "Método (sección 4): Gran M con M simbólica, reglas de entrada y salida, y el simplex revisado como segundo método."),
        ("2:30 – 3:30", "Boceto (sección 5): recorrer la pantalla y las pestañas."),
        ("3:30 – 4:30", "Adelanto opcional: abrir la aplicación (streamlit run app.py), cargar el ejemplo 1 y resolverlo en modo paso a paso."),
        ("4:30 – 5:00", "Plan de sprints y preguntas."),
    ]
    el.append(tabla([["Tiempo", "Qué mostrar"]] + [[a, C(b)] for a, b in guion], [3 * cm, 12.6 * cm]))

    el.append(Paragraph("9. Lista de verificación antes de presentar", H))
    for t in ["Repositorio accesible para el docente y con ambos integrantes como colaboradores.",
              "La aplicación abre en el equipo que se usará: pip install -r requirements.txt y streamlit run app.py.",
              "Ambos integrantes pueden explicar el método elegido y las reglas de entrada y salida.",
              "Tener a mano este PDF y el enunciado del proyecto."]:
        el.append(Paragraph(t, L, bulletText="☐"))

    doc.build(el)
    print(f"Generado: {out}")


if __name__ == "__main__":
    main()
