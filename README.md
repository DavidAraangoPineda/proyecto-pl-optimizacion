# Aplicación de Programación Lineal

Proyecto de Optimización — Universidad de Antioquia, Facultad de Ingeniería, Departamento de Ingeniería de Sistemas.

**Integrantes:** David Arango Pineda · Juan Ignacio Parra

Aplicación web (Streamlit) que resuelve problemas de programación lineal con **método propio** —**Gran M** sobre tablero y **simplex revisado**— y muestra el proceso completo, no solo la respuesta. Toda la aritmética es **exacta con fracciones** (sin errores de redondeo).

> Las librerías de optimización (scipy) se usan **únicamente en las pruebas** para verificar los resultados del método propio; nunca para producirlos.

## Funcionalidades

| Requisito del enunciado | Dónde |
|---|---|
| Entrada general: Max/Min, n variables, m restricciones (≤, ≥, =), LD de cualquier signo, validación con mensajes claros | `lp/model.py`, `app.py` |
| Método propio (Gran M y simplex revisado) | `lp/bigm.py`, `lp/revised.py`, `lp/standard.py` |
| Modo directo o paso a paso (forma estándar, entrante, razón mínima, saliente, pivote, tablero / B⁻¹, básicas y costos reducidos) | `lp/render.py`, pestaña «Paso a paso» |
| Solución óptima: variables, Z, holgura/exceso por restricción | `lp/analysis.py`, pestaña «Resultado» |
| Método gráfico (2 variables): región sombreada, restricciones rotuladas, vértices con Z, recta de Z; avisa si n > 2 | `lp/graphical.py` |
| Sensibilidad: precios sombra, costos reducidos, rango de coeficientes y de lados derechos, con interpretación | `lp/analysis.py` |
| Casos especiales: infactible, no acotado, óptimos múltiples, degenerado (mensajes claros) | `lp/analysis.py` |
| Interfaz gráfica: agregar/quitar variables y restricciones, editar y re-resolver sin reiniciar | `app.py` |
| **Bonos:** dos métodos comparados · fracciones exactas · exportar a PDF · cargar/guardar JSON | pestañas «Comparar métodos» y «Exportar», barra lateral |

## Requisitos

- Python 3.10 o superior
- Dependencias de `requirements.txt` (streamlit, matplotlib, pandas, reportlab)

## Instalación

```bash
git clone https://github.com/DavidAraangoPineda/proyecto-pl-optimizacion.git
cd proyecto-pl-optimizacion
python -m venv .venv
# Windows:  .venv\Scripts\activate        Linux/Mac:  source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecución

```bash
streamlit run app.py
```

Se abre en `http://localhost:8501`. Desde la barra lateral se elige el método, el modo (directa / paso a paso), el formato de números (fracciones / decimales) y se pueden cargar los 7 ejemplos del enunciado o un archivo JSON (hay ejemplos en [`examples/`](examples)).

## Pruebas

```bash
pip install -r requirements-dev.txt
pytest tests -q
```

Las pruebas cubren los 7 problemas del enunciado con ambos métodos, 400 problemas aleatorios contra scipy (óptimo, infactible, no acotado), la sensibilidad (re-resolviendo con los parámetros perturbados) y la validación de la entrada.

## Estructura

```
app.py                  Interfaz (Streamlit)
lp/numbers.py           Fracciones y números a + b·M (Gran M simbólica)
lp/model.py             Problema, validación, JSON, ejemplos
lp/standard.py          Forma estándar (holguras, excesos, artificiales)
lp/bigm.py              Método de la Gran M (tablero)
lp/revised.py           Simplex revisado (B⁻¹ explícita)
lp/analysis.py          Interpretación, casos especiales y sensibilidad
lp/graphical.py         Método gráfico
lp/pdf_export.py        Exportación a PDF
tests/                  Pruebas (scipy solo para verificar)
docs/                   Propuesta, planeación de sprints y manual
examples/               Problemas de ejemplo en JSON
```

## Decisiones de diseño

- **M simbólica:** los costos se guardan como `a + b·M` y se comparan lexicográficamente, sin fijar un valor numérico para M.
- **Regla de pivoteo:** entra el mayor `cj − zj` positivo (empates: menor índice); sale la menor razón (empates: menor índice, que además señala degeneración). Tras 200 iteraciones se pasa a la regla de Bland para evitar ciclos. Ambos métodos usan la misma regla, por lo que sus iteraciones son comparables.
- **Infactibilidad:** si la Gran M termina «no acotada» con artificiales positivas, se verifica la factibilidad (fase 1) antes de declarar no acotado.

## Cronograma

| Sprint | Fecha | Entrega |
|--------|-------|---------|
| Sprint 1 | 18 nov 2026 | Propuesta: [informe PDF](docs/Sprint1_Propuesta.pdf) · [resumen](docs/SPRINT1_PROPUESTA.md) |
| Sprint 2 | 27 nov 2026 | Avance |
| Sprint 3 | 4 dic 2026 | Entrega final y sustentación |

## Entregables

- [x] Repositorio con código fuente
- [x] README con requisitos, instalación y ejecución
- [ ] Manual de usuario (máx. 5 páginas, capturas de 2 problemas) — ver [docs/MANUAL_USUARIO.md](docs/MANUAL_USUARIO.md)
- [ ] Video de demostración (máx. 5 min)
- [ ] Historial de commits de ambos integrantes
