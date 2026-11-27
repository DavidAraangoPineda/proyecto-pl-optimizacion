"""Reglas de arquitectura (docs/ARQUITECTURA.md) verificadas automáticamente.

Si una prueba de este archivo falla, el cambio rompe la separación por capas: corrija el import
en vez de cambiar la regla, salvo que la regla misma se discuta y se actualice en ARQUITECTURA.md.
"""
import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LP = ROOT / "lp"

# Capas de abajo hacia arriba: un módulo solo importa de su capa o de capas inferiores.
CAPAS = {
    "numbers": 0, "linalg": 0,                                   # aritmética exacta
    "model": 1, "standard": 1,                                   # modelo del problema
    "common": 2, "bigm": 2, "revised": 2,                        # algoritmos
    "analysis": 3, "geometry": 3, "solver": 3,                   # interpretación y geometría
    "render": 4, "graphical": 4, "pdf_export": 4, "presentation": 4,   # salidas
}
NUCLEO = {m for m, c in CAPAS.items() if c <= 3}
STDLIB_PERMITIDA = {"dataclasses", "fractions", "json", "math", "itertools", "re", "pathlib", "io", "os"}


def _imports(path):
    """(módulo importado, nombres importados) de cada import del archivo, incluidos los internos a funciones."""
    out = []
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, ast.Import):
            out += [(a.name, []) for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            mod = ("." * node.level) + (node.module or "")
            out.append((mod, [a.name for a in node.names]))
    return out


def _interno(mod):
    """Nombre del módulo de lp/ al que apunta un import, o None si es externo."""
    if mod.startswith("."):
        return mod.lstrip(".").split(".")[0] or None
    if mod.startswith("lp."):
        return mod.split(".")[1]
    return None


def test_todos_los_modulos_tienen_capa():
    modulos = {p.stem for p in LP.glob("*.py") if p.stem != "__init__"}
    assert modulos == set(CAPAS), f"Asigne una capa en CAPAS y en ARQUITECTURA.md a: {modulos ^ set(CAPAS)}"


def test_las_dependencias_van_hacia_abajo():
    for mod, capa in CAPAS.items():
        for imp, _ in _imports(LP / f"{mod}.py"):
            dest = _interno(imp)
            if dest is not None:
                assert CAPAS[dest] <= capa, f"lp/{mod}.py (capa {capa}) no debe importar lp/{dest}.py (capa {CAPAS[dest]})"


def test_el_nucleo_solo_usa_la_biblioteca_estandar():
    for mod in NUCLEO:
        for imp, _ in _imports(LP / f"{mod}.py"):
            if _interno(imp) is None:
                assert imp.split(".")[0] in STDLIB_PERMITIDA, f"lp/{mod}.py importa '{imp}': el núcleo no usa librerías externas"


def test_nadie_importa_nombres_privados_de_otro_modulo():
    archivos = list(LP.glob("*.py")) + [ROOT / "app.py"] + list((ROOT / "docs").glob("*.py"))
    for path in archivos:
        for imp, nombres in _imports(path):
            if _interno(imp) is not None:
                privados = [n for n in nombres if n.startswith("_")]
                assert not privados, f"{path.name} importa nombres privados {privados} de {imp}"


def test_el_motor_no_conoce_la_interfaz_ni_las_pruebas():
    for path in LP.glob("*.py"):
        for imp, _ in _imports(path):
            raiz = imp.split(".")[0]
            assert raiz not in {"streamlit", "pandas", "scipy", "numpy", "app", "interfaz"}, f"lp/{path.name} importa '{imp}'"
