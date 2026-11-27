"""Aplicación de Programación Lineal — interfaz web (Streamlit).

Ejecutar:  streamlit run app.py
El motor (lp/) es propio: Gran M sobre tablero y simplex revisado, con fracciones exactas.
"""
import io

import pandas as pd
import streamlit as st

from interfaz import ayuda
from lp.graphical import graph_2d
from lp.model import (EXAMPLES, SIGN_LABEL, ValidationError, constraints_text, objective_text,
                      parse_problem, problem_to_json, raw_from_json)
from lp.numbers import fmt, fmt_bound
from lp.pdf_export import build_pdf
from lp.presentation import presentation_html
from lp.render import revised_blocks, step_text, tableau_table
from lp.solver import METHODS, solve
from lp.standard import standard_form_lines

st.set_page_config(page_title="Programación Lineal — Gran M y Simplex Revisado", page_icon="📐", layout="wide")

SIGN_OPTIONS = ["≤", "≥", "="]


# ====================================================================== estado

def _grids(n, m, c=None, A=None, signs=None, b=None):
    cols = [f"x{j + 1}" for j in range(n)]
    obj = pd.DataFrame([c or [""] * n], columns=cols, index=["Coef. de Z"])
    rows = []
    for i in range(m):
        rows.append((A[i] if A else [""] * n) + [signs[i] if signs else "≤"] + [b[i] if b else ""])
    con = pd.DataFrame(rows, columns=cols + ["Signo", "Lado derecho"], index=[f"R{i + 1}" for i in range(m)])
    return obj, con


def _load_raw(sense, c, A, signs, b, name=""):
    st.session_state.sense = sense
    st.session_state.obj, st.session_state.con = _grids(len(c), len(A), c, A, signs, b)
    st.session_state.pname = name
    st.session_state.ver += 1


def _init():
    if "ver" not in st.session_state:
        st.session_state.ver = 0
        st.session_state.result = None
        st.session_state.pdf = None
        st.session_state.uploaded_id = None
        p = list(EXAMPLES.values())[0]
        _load_raw(p.sense, [str(v) for v in p.c], [[str(v) for v in r] for r in p.A],
                  [SIGN_LABEL[s] for s in p.signs], [str(v) for v in p.b], p.name)


def _problem_from_grids(obj, con):
    n = obj.shape[1]
    return parse_problem(
        "max" if st.session_state.sense == "Maximizar" or st.session_state.sense == "max" else "min",
        list(obj.iloc[0]), [list(con.iloc[i, :n]) for i in range(len(con))],
        list(con["Signo"]), list(con["Lado derecho"]), st.session_state.get("pname", ""))


# ====================================================================== barra lateral

_init()
ss = st.session_state

with st.sidebar:
    st.header("⚙️ Opciones")
    method = st.radio("Método de solución", list(METHODS), format_func=lambda k: METHODS[k][0],
                      help="Ambos métodos son implementación propia del equipo.")
    with st.expander("ℹ️ ¿Qué diferencia hay entre los métodos?"):
        st.markdown(ayuda.METODOS)
    mode = st.radio("Modo de solución", ["Paso a paso", "Solución directa"],
                    help="Directa: solo el resultado. Paso a paso: forma estándar e iteraciones.")
    decimals = st.radio("Formato de números", ["Fracciones", "Decimales"], horizontal=True) == "Decimales"
    st.divider()
    st.subheader("📂 Problemas")
    ex = st.selectbox("Cargar un ejemplo", ["—"] + list(EXAMPLES), key="ex_select")
    if ex != "—" and ss.get("ex_loaded") != ex:
        p = EXAMPLES[ex]
        _load_raw(p.sense, [str(v) for v in p.c], [[str(v) for v in r] for r in p.A],
                  [SIGN_LABEL[s] for s in p.signs], [str(v) for v in p.b], p.name)
        ss.ex_loaded = ex
        ss.result = None
        st.rerun()
    if ex == "—":
        ss.ex_loaded = None
    up = st.file_uploader("Cargar problema (JSON)", type=["json"])
    if up is not None and ss.uploaded_id != (up.name, up.size):
        try:
            _load_raw(*raw_from_json(up.getvalue().decode("utf-8")))
            ss.uploaded_id = (up.name, up.size)
            ss.result = None
            st.rerun()
        except ValidationError as e:
            st.error("\n\n".join(e.messages))
        except UnicodeDecodeError:
            st.error("No se pudo leer el archivo: no es texto UTF-8.")
    st.caption("🌙 Modo oscuro: menú ⋮ (arriba a la derecha) → Dark.")
    st.caption("Equipo: David Arango Pineda · Juan Ignacio Parra")

# ====================================================================== entrada del problema

st.title("📐 Programación Lineal")
st.caption("Resuelve con el método de la Gran M o el simplex revisado y muestra todo el proceso.")

st.subheader("1. Problema")
with st.expander("ℹ️ Cómo escribir el problema"):
    st.markdown(ayuda.ENTRADA)
ss.sense = st.radio("Tipo de problema", ["Maximizar", "Minimizar"],
                    index=0 if ss.sense in ("max", "Maximizar") else 1, horizontal=True)

n_vars = ss.obj.shape[1]
col_cfg = {f"x{j + 1}": st.column_config.TextColumn(f"x{j + 1}", width="small") for j in range(n_vars)}
st.markdown("**Función objetivo** — coeficientes de cada variable (acepta enteros, decimales y fracciones como 1/3)")
obj_ed = st.data_editor(ss.obj, key=f"obj_{ss.ver}", column_config=col_cfg, width="stretch")
st.markdown("**Restricciones** — coeficientes, signo y lado derecho (puede ser negativo). Todas las variables son ≥ 0.")
con_cfg = dict(col_cfg)
con_cfg["Signo"] = st.column_config.SelectboxColumn("Signo", options=SIGN_OPTIONS, required=True, width="small")
con_cfg["Lado derecho"] = st.column_config.TextColumn("Lado derecho", width="small")
con_ed = st.data_editor(ss.con, key=f"con_{ss.ver}", column_config=con_cfg, width="stretch")


def _resize(dn=0, dm=0):
    obj, con = obj_ed.copy(), con_ed.copy()
    n = obj.shape[1]
    if dn == 1:
        nm = f"x{n + 1}"
        obj.insert(n, nm, "")
        con.insert(n, nm, "")
    elif dn == -1 and n > 1:
        obj = obj.iloc[:, :-1]
        con = con.drop(columns=[f"x{n}"])
    if dm == 1:
        con.loc[f"R{len(con) + 1}"] = [""] * (con.shape[1] - 2) + ["≤", ""]
    elif dm == -1 and len(con) > 1:
        con = con.iloc[:-1]
    ss.obj, ss.con = obj, con
    ss.ver += 1
    ss.result = None
    st.rerun()


b1, b2, b3, b4, _ = st.columns([1, 1, 1, 1, 3])
if b1.button("➕ Variable"):
    _resize(dn=1)
if b2.button("➖ Variable", disabled=n_vars <= 1):
    _resize(dn=-1)
if b3.button("➕ Restricción"):
    _resize(dm=1)
if b4.button("➖ Restricción", disabled=len(con_ed) <= 1):
    _resize(dm=-1)

go = st.button("▶ Resolver", type="primary")
problem = None
try:
    problem = _problem_from_grids(obj_ed, con_ed)
except ValidationError as e:
    if go:
        st.error("**No se puede resolver: revise los datos.**\n\n" + "\n".join(f"- {m}" for m in e.messages))
    else:
        st.warning("Hay datos por corregir antes de resolver:\n\n" + "\n".join(f"- {m}" for m in e.messages))

if problem is not None:
    with st.expander("Vista del modelo formulado", expanded=False):
        st.markdown(f"**{objective_text(problem, decimals)}**")
        for line in constraints_text(problem, decimals):
            st.markdown("&nbsp;&nbsp;" + line)
        st.markdown("&nbsp;&nbsp;" + ", ".join(problem.var_names) + " ≥ 0")
    st.download_button("💾 Guardar problema (JSON)", problem_to_json(problem), file_name="problema_pl.json",
                       mime="application/json")

if go and problem is not None:
    ss.result = {"problem": problem, "sols": {k: solve(problem, k) for k in METHODS}}
    ss.pdf = None
    ss.presentacion = None

# ====================================================================== resultados

res = ss.result
if res is None:
    st.info("Ingrese el problema (o cargue un ejemplo en la barra lateral) y pulse **Resolver**.")
    st.stop()

problem, sol = res["problem"], res["sols"][method]
st.divider()
st.subheader("2. Resultados")
tabs = st.tabs(["📋 Resultado", "🪜 Paso a paso", "📈 Método gráfico", "🎯 Sensibilidad", "⚖️ Comparar métodos", "📄 Exportar"])


def _ayuda(*textos):
    """Desplegable con la explicación de la pestaña: qué muestra y cómo leerla."""
    with st.expander("ℹ️ ¿Qué muestra esta pestaña y cómo leerla?"):
        for t in textos:
            st.markdown(t)


# Resaltados semitransparentes: se leen bien con el tema claro y con el oscuro.
VERDE = "rgba(46, 160, 67, 0.28)"
ROJO = "rgba(248, 81, 73, 0.28)"


def _tema_oscuro():
    """True si el usuario tiene activo el tema oscuro (menú ⋮ → Dark)."""
    try:
        return st.context.theme.type == "dark"
    except AttributeError:      # versiones de Streamlit sin st.context.theme
        return False


def _df(header, rows, meta=None):
    # los encabezados repetidos romperían el DataFrame; se hacen únicos
    seen, cols = {}, []
    for h in header:
        seen[h] = seen.get(h, 0) + 1
        cols.append(h if seen[h] == 1 else f"{h} ")
    df = pd.DataFrame(rows, columns=cols)
    if not meta:
        return df
    sty = df.style
    ec, lr, er = meta.get("enter_col"), meta.get("leave_row"), meta.get("enter_row")

    def paint(data):
        out = pd.DataFrame("", index=data.index, columns=data.columns)
        if ec is not None:
            out.iloc[:, ec] = f"background-color: {VERDE}"
        if lr is not None:
            out.iloc[lr, :] = f"background-color: {ROJO}"
        if er is not None:
            out.iloc[er, :] = f"background-color: {VERDE}"
        if ec is not None and lr is not None:
            out.iloc[lr, ec] = "background-color: #ffd54f; color: #111; font-weight: bold"
        return out

    return sty.apply(paint, axis=None)


# ---- Resultado
with tabs[0]:
    _ayuda(ayuda.RESULTADO)
    st.caption(f"Método utilizado: **{METHODS[method][0]}** · {len(sol.run.steps) - 1} iteración(es)")
    if sol.status == "optimal":
        st.success("✅ Solución óptima encontrada")
        c1, c2 = st.columns([1, 2])
        c1.metric("Valor de Z", fmt(sol.z, decimals))
        c2.table(pd.DataFrame({"Variable": problem.var_names, "Valor": [fmt(v, decimals) for v in sol.x]}).set_index("Variable").T)
        rows = []
        for i, (t, v) in enumerate(sol.slacks):
            lhs = sum(a * x for a, x in zip(problem.A[i], sol.x))
            rows.append([f"R{i + 1}", fmt(lhs, decimals), SIGN_LABEL[problem.signs[i]], fmt(problem.b[i], decimals),
                         t.capitalize() if t != "igualdad" else "—", fmt(v, decimals),
                         "Activa (se cumple con igualdad)" if v == 0 else "Inactiva (sobra holgura)" if t == "holgura" else "Inactiva (sobra exceso)"])
        st.markdown("**Holgura o exceso de cada restricción**")
        st.dataframe(pd.DataFrame(rows, columns=["Restricción", "Lado izquierdo", "Signo", "Lado derecho", "Tipo", "Valor", "Estado"]),
                     hide_index=True, width="stretch")
    elif sol.status == "infeasible":
        st.error("⛔ El problema no tiene solución factible")
    elif sol.status == "unbounded":
        st.warning("♾️ La solución es no acotada")
    else:
        st.error("No se pudo completar la resolución.")
    for msg in sol.messages:
        (st.info if sol.status == "optimal" else st.markdown)(msg)
    for n in sol.run.notes:
        st.caption(n)

# ---- Paso a paso
with tabs[1]:
    _ayuda(ayuda.PASO_A_PASO_COMUN, ayuda.PASO_A_PASO_BIGM if method == "bigm" else ayuda.PASO_A_PASO_REVISADO)
    if mode != "Paso a paso":
        st.info("Está en modo **Solución directa**. Cambie a **Paso a paso** en la barra lateral para ver la forma estándar y las iteraciones.")
    else:
        sf = sol.sf
        st.markdown("### Forma estándar")
        for n in sf.notes:
            st.markdown("- " + n)
        st.markdown("Se agrega **holgura** (s) a cada ≤, se resta **exceso** (e) y se agrega **artificial** (a) a cada ≥, y se agrega **artificial** a cada =. "
                    "Las artificiales se penalizan con −M en la función objetivo.")
        st.code("\n".join(standard_form_lines(problem, sf, decimals)), language=None)
        if problem.sense == "min":
            st.caption("Z' = −Z: en los tableros, la fila zj muestra Z' (el valor de Z se obtiene al final como −Z').")
        st.markdown("### Iteraciones")
        st.caption("🟩 columna de la variable que entra · 🟥 fila de la variable que sale · 🟨 pivote")
        for stp in sol.run.steps:
            last = stp is sol.run.steps[-1]
            title = f"Iteración {stp['k']}" + (" — tablero final" if last else "")
            with st.expander(title, expanded=last or stp["k"] == 0):
                if stp["kind"] == "tableau":
                    header, rows, meta = tableau_table(sf, stp, decimals)
                    st.dataframe(_df(header, rows, meta), hide_index=True, width="stretch")
                else:
                    for t, header, rows, meta in revised_blocks(sf, stp, decimals):
                        st.markdown(f"**{t}**")
                        st.dataframe(_df(header, rows, meta), hide_index=True, width="stretch")
                st.markdown(f"Z{'′' if problem.sense == 'min' else ''} actual = {stp['z'].fmt(decimals)}")
                for line in step_text(sf, stp, decimals, problem.sense):
                    st.markdown("- " + line)
                if last:
                    if sol.status == "optimal":
                        st.success("Solución óptima: " + ", ".join(f"{problem.var_names[j]} = {fmt(sol.x[j], decimals)}" for j in range(problem.n))
                                   + f", Z = {fmt(sol.z, decimals)}")
                    elif sol.status == "infeasible":
                        st.error("Termina con una variable artificial positiva en la base → problema infactible.")
                    elif sol.status == "unbounded":
                        st.warning("Columna sin elementos positivos → problema no acotado.")

# ---- Método gráfico
with tabs[2]:
    _ayuda(ayuda.GRAFICO)
    info = graph_2d(problem, sol, dark=_tema_oscuro())
    if not info.applicable:
        st.warning("⚠️ " + info.messages[0])
    else:
        for msg in info.messages:
            st.warning(msg) if ("VACÍA" in msg or "no acotada" in msg.lower()) else st.info(msg)
        st.pyplot(info.figure, clear_figure=True)
        if info.vertices:
            st.markdown("**Vértices de la región factible y su valor de Z**")
            opt = {(v[0], v[1]) for v in info.optimal_vertices}
            st.dataframe(pd.DataFrame([[f"({fmt(a, decimals)}, {fmt(b, decimals)})", fmt(z, decimals),
                                        "⭐ óptimo" if (a, b) in opt and sol.status == "optimal" else ""]
                                       for a, b, z in info.vertices], columns=["Vértice (x1, x2)", "Z", ""]),
                         hide_index=True)

# ---- Sensibilidad
with tabs[3]:
    _ayuda(ayuda.SENSIBILIDAD)
    if sol.status != "optimal":
        st.info("El análisis de sensibilidad solo existe cuando hay una solución óptima.")
    else:
        sn = sol.sens
        sense_txt = "aumenta" if problem.sense == "max" else "disminuye"
        st.markdown("### Restricciones: precios sombra y rango del lado derecho")
        rows = []
        for i in range(problem.m):
            lo, hi = sn.rhs_ranges[i]
            rows.append([f"R{i + 1}", fmt(problem.b[i], decimals), fmt(sn.shadow[i], decimals),
                         f"[{fmt_bound(lo, decimals)} ; {fmt_bound(hi, decimals)}]"])
        st.dataframe(pd.DataFrame(rows, columns=["Restricción", "LD actual", "Precio sombra", "Rango del LD (precio válido)"]),
                     hide_index=True, width="stretch")
        for i in range(problem.m):
            lo, hi = sn.rhs_ranges[i]
            if sn.shadow[i] == 0:
                st.markdown(f"- **R{i + 1}**: precio sombra 0. {'No es limitante' if sol.slacks[i][1] > 0 else 'Está activa pero no cambia Z'}: "
                            f"cambiar su lado derecho dentro de [{fmt_bound(lo, decimals)} ; {fmt_bound(hi, decimals)}] no altera Z.")
            else:
                st.markdown(f"- **R{i + 1}**: cada unidad adicional en el lado derecho cambia Z en **{fmt(sn.shadow[i], decimals)}** "
                            f"(Z {'aumenta' if sn.shadow[i] > 0 else 'disminuye'}), mientras el LD esté en "
                            f"[{fmt_bound(lo, decimals)} ; {fmt_bound(hi, decimals)}].")
        st.markdown("### Variables: costos reducidos y rango de los coeficientes de Z")
        rows = []
        for j in range(problem.n):
            lo, hi = sn.cost_ranges[j]
            rows.append([problem.var_names[j], fmt(sol.x[j], decimals), "Básica" if sn.basic[j] else "No básica",
                         fmt(problem.c[j], decimals), fmt(sn.reduced[j], decimals),
                         f"[{fmt_bound(lo, decimals)} ; {fmt_bound(hi, decimals)}]"])
        st.dataframe(pd.DataFrame(rows, columns=["Variable", "Valor", "Estado", "Coef. actual", "Costo reducido", "Rango del coeficiente (misma base óptima)"]),
                     hide_index=True, width="stretch")
        for j in range(problem.n):
            lo, hi = sn.cost_ranges[j]
            nm = problem.var_names[j]
            if sn.basic[j]:
                st.markdown(f"- **{nm}** es básica: la solución óptima no cambia mientras su coeficiente esté en [{fmt_bound(lo, decimals)} ; {fmt_bound(hi, decimals)}].")
            else:
                st.markdown(f"- **{nm}** es no básica (vale 0): forzar una unidad de {nm} cambia Z en **{fmt(sn.reduced[j], decimals)}**; "
                            f"solo entraría a la solución si su coeficiente saliera del rango [{fmt_bound(lo, decimals)} ; {fmt_bound(hi, decimals)}].")
        for n in sn.notes:
            st.caption(n)
        st.caption("Convención: precio sombra y costo reducido = cambio en Z (en el sentido original, "
                   f"{'maximización' if problem.sense == 'max' else 'minimización'}) por cada unidad adicional. "
                   "Los rangos son válidos moviendo un solo parámetro a la vez.")

# ---- Comparar métodos
with tabs[4]:
    _ayuda(ayuda.COMPARAR)
    a, b = res["sols"]["bigm"], res["sols"]["revised"]
    st.markdown("Comparación de las iteraciones de **Gran M (tablero)** y **simplex revisado** (misma regla de pivoteo).")

    def _name(s, j):
        return "—" if j is None else s.sf.names[j]

    rows = []
    for k in range(max(len(a.run.steps), len(b.run.steps))):
        row = [k]
        for s in (a, b):
            if k < len(s.run.steps):
                t = s.run.steps[k]
                lv = None if t["leaving_row"] is None else t["basis"][t["leaving_row"]]
                row += [_name(s, t["entering"]), _name(s, lv), t["z"].fmt(decimals)]
            else:
                row += ["", "", ""]
        rows.append(row)
    cols = pd.MultiIndex.from_tuples([("", "Iter."), ("Gran M", "Entra"), ("Gran M", "Sale"), ("Gran M", "Z"),
                                      ("Simplex revisado", "Entra"), ("Simplex revisado", "Sale"), ("Simplex revisado", "Z")])
    st.dataframe(pd.DataFrame(rows, columns=cols), hide_index=True, width="stretch")
    same = a.status == b.status and a.z == b.z and a.x == b.x
    st.markdown(f"- Iteraciones: Gran M = **{len(a.run.steps) - 1}**, simplex revisado = **{len(b.run.steps) - 1}**.")
    st.markdown("- Ambos métodos llegan " + ("**al mismo resultado** ✅" if same else "a resultados distintos ⚠️") + ".")
    st.markdown("- El tablero actualiza toda la matriz en cada iteración; el revisado solo mantiene **B⁻¹**, "
                "y calcula bajo demanda los costos reducidos y la columna de la variable que entra.")

# ---- Exportar
with tabs[5]:
    _ayuda(ayuda.EXPORTAR)
    st.markdown("Exporta el problema, la forma estándar, **todas las iteraciones**, la solución, la sensibilidad y el gráfico en un PDF.")
    if st.button("Generar PDF"):
        with st.spinner("Generando PDF..."):
            ss.pdf = build_pdf(sol, decimals)
    if ss.pdf:
        st.download_button("⬇️ Descargar PDF", ss.pdf, file_name="solucion_programacion_lineal.pdf", mime="application/pdf")

    st.divider()
    st.markdown("### 🎬 Presentación animada")
    st.markdown("Genera **El viaje del Simplex** para este problema: un solo archivo HTML con la explicación narrada "
                "por capítulos (región factible, forma estándar, iteraciones en tablero con la Gran M, el mismo recorrido con el "
                "simplex revisado y su comparación, sensibilidad y casos especiales). "
                "Ábrelo en Microsoft Edge, pulsa **F** para pantalla completa y **Av Pág** para avanzar.")
    if st.button("Generar presentación"):
        with st.spinner("Preparando la presentación con el motor propio..."):
            ss.presentacion = presentation_html(problem)
    if ss.get("presentacion"):
        st.download_button("⬇️ Descargar presentación (HTML)", ss.presentacion, file_name="viaje_del_simplex.html",
                           mime="text/html")
