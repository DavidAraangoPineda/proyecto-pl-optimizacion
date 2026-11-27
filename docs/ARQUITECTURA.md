# Arquitectura

La aplicación está separada en **capas**. Cada capa solo puede usar las capas que están debajo de ella.
Así el motor matemático se puede leer, probar y explicar sin saber nada de la interfaz, y la interfaz
se puede cambiar sin tocar el método.

```
 ┌─────────────────────────────────────────────────────────────┐
 │ 6. Interfaz      app.py · interfaz/ayuda.py                 │  Streamlit, textos de ayuda
 ├─────────────────────────────────────────────────────────────┤
 │ 5. Salidas       lp/render.py · lp/graphical.py             │  tablas y textos, gráfico,
 │                  lp/pdf_export.py · lp/presentation.py      │  PDF, presentación animada
 ├─────────────────────────────────────────────────────────────┤
 │ 4. Análisis      lp/analysis.py · lp/geometry.py            │  casos especiales, sensibilidad,
 │                  lp/solver.py                               │  vértices 2D, punto de entrada
 ├─────────────────────────────────────────────────────────────┤
 │ 3. Algoritmos    lp/common.py · lp/bigm.py · lp/revised.py  │  Gran M y simplex revisado
 ├─────────────────────────────────────────────────────────────┤
 │ 2. Modelo        lp/model.py · lp/standard.py               │  problema, validación, forma estándar
 ├─────────────────────────────────────────────────────────────┤
 │ 1. Aritmética    lp/numbers.py · lp/linalg.py               │  fracciones, números a + b·M
 └─────────────────────────────────────────────────────────────┘
```

(En [tests/test_arquitectura.py](../tests/test_arquitectura.py) las capas 1 a 5 se numeran 0 a 4.)

## Reglas

Las reglas 1 a 5 las verifica `pytest` en `tests/test_arquitectura.py`: si un cambio las rompe, la prueba
falla y dice qué import corregir.

1. **Las dependencias van hacia abajo.** Un módulo importa solo de su capa o de capas inferiores.
   Ejemplo: `model.py` no puede importar `render.py`; por eso `lin_expr` vive en `numbers.py`.
2. **El núcleo (capas 1 a 4) solo usa la biblioteca estándar de Python.** Nada de matplotlib, reportlab,
   pandas ni streamlit en el motor: así el método es 100 % propio y fácil de probar.
3. **Las librerías de optimización solo están en las pruebas.** `scipy` y `numpy` se usan únicamente en
   `tests/` para verificar resultados, nunca para producirlos (exigencia del enunciado).
4. **Nada privado cruza de módulo.** Los nombres que empiezan por `_` son internos. Si otro módulo
   necesita algo, se expone con un nombre público (ejemplo: `geometry.feasible_vertices_2d`).
5. **El motor no conoce la interfaz.** `lp/` nunca importa `app`, `interfaz`, `streamlit` ni `pandas`.
6. **Aritmética exacta en todo el cálculo.** Los números son `Fraction` y `MNum`; los decimales solo
   aparecen al mostrar (`fmt(x, decimals=True)`), nunca al calcular.
7. **Los dos métodos comparten las reglas de pivoteo** (`common.py`), para que sus iteraciones sean
   comparables paso a paso.
8. **Los textos para el usuario están en la capa que los muestra.** Las justificaciones de cada
   iteración están en `render.py`; las explicaciones de cada pestaña en `interfaz/ayuda.py`.
9. **Todo dato que va a HTML se escapa.** El PDF usa `_esc` y la presentación usa `E()`/`EL()` en
   `presentacion/js/app.js`.

## Flujo de una resolución

```
app.py ──parse_problem──▶ Problem ──build_standard_form──▶ StandardForm
                                                              │
                          solve_bigm / solve_revised ◀────────┘
                                     │  Run (iteraciones)
                                     ▼
                              interpret ──▶ Solution (estado, x, Z, holguras, casos, sensibilidad)
                                     │
        ┌────────────────┬───────────┴──────┬──────────────────┐
   render (tablas)   graphical (2D)   pdf_export (PDF)   presentation (HTML animado)
```

## Pruebas

| Archivo | Qué verifica |
|---|---|
| `tests/test_problems.py` | Los 7 problemas del enunciado, problemas aleatorios contra scipy, sensibilidad, validación |
| `tests/test_graficos.py` | Vértices, región vacía y no acotada, gráfico de cada ejemplo |
| `tests/test_presentation.py` | Datos de la presentación (ambos métodos) y HTML autónomo |
| `tests/test_app.py` | La interfaz arranca y resuelve cada ejemplo con los dos métodos sin errores |
| `tests/test_arquitectura.py` | Las reglas 1 a 5 de este documento |

Ejecutar todo: `pip install -r requirements-dev.txt` y luego `pytest tests -q`.

## Cómo agregar algo nuevo

- **Un módulo nuevo en `lp/`:** asígnele una capa en `CAPAS` (`tests/test_arquitectura.py`) y en el
  diagrama de arriba.
- **Una pestaña nueva:** el cálculo va en `lp/` (capa 4 o 5), la vista en `app.py` y su explicación en
  `interfaz/ayuda.py`.
- **Un caso especial nuevo:** se detecta en `analysis.py` y se explica con un mensaje en `Solution.messages`;
  nunca con una excepción que llegue al usuario.
