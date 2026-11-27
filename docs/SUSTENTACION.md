# Guía de sustentación (15 minutos)

En la sustentación **el docente elige qué parte del código explica cada integrante** y el equipo
**resuelve en vivo un problema que no conoce**. Lo que un integrante no pueda explicar o modificar cuenta
como no implementado, así que **los dos deben conocer todo el código**. El reparto de abajo es para
prepararse a fondo; después cada uno le explica su parte al otro.

## 1. Plan de los 15 minutos

| Minuto | Qué se hace | Quién |
|---|---|---|
| 0–2 | Presentación: qué hace la app, URL en línea, arquitectura en capas (diagrama de `docs/ARQUITECTURA.md`) | David |
| 2–6 | Resolver en vivo el problema del docente (sección 4) | Los dos |
| 6–13 | Explicar las partes de código que pida el docente (secciones 2 y 3) | El que elija el docente |
| 13–15 | Preguntas | Los dos |

Tener abiertos antes de empezar: la app (en línea **y** local con `streamlit run app.py`, por si falla internet),
VS Code con el repositorio y este documento.

## 2. Reparto del código

| Capa | Archivos | Responsable principal |
|---|---|---|
| Aritmética exacta | `lp/numbers.py` (Fraction, `MNum` = a + b·M, `fmt`), `lp/linalg.py` | David |
| Modelo y validación | `lp/model.py` (`parse_problem`, JSON, ejemplos) | David |
| Forma estándar | `lp/standard.py` (`build_standard_form`) | David |
| Gran M | `lp/bigm.py` (`solve_bigm`), `lp/common.py` (reglas de pivoteo) | David |
| Simplex revisado | `lp/revised.py` (`solve_revised`) | Juan Ignacio |
| Interpretación y casos especiales | `lp/analysis.py` (`interpret`, óptimos múltiples) | Juan Ignacio |
| Sensibilidad | `lp/analysis.py` (`sensitivity`) | Juan Ignacio |
| Método gráfico | `lp/geometry.py`, `lp/graphical.py` | Juan Ignacio |
| Salidas | `lp/render.py` (tablas y justificaciones), `lp/pdf_export.py`, `lp/presentation.py` + `presentacion/` | Los dos |
| Interfaz | `app.py`, `interfaz/ayuda.py` | Los dos |
| Pruebas | `tests/` (scipy **solo** verifica) | Los dos |

## 3. Qué decir de cada parte (y preguntas probables)

### Aritmética exacta — `lp/numbers.py`
- Todo se calcula con `Fraction`: no hay errores de redondeo y el paso a paso sale en fracciones (bono +0.1).
- **`MNum(a, b)`** representa *a + b·M*. Se compara **primero la parte de M** (`key() = (b, a)`), así que M
  nunca toma un valor numérico: no hay que adivinar «qué tan grande» es M.
- *¿Por qué no usar M = 10⁶?* Porque con un M numérico la parte real se puede perder por redondeo o por
  un M insuficiente; con M simbólica la comparación es exacta.

### Modelo y validación — `lp/model.py`
- `parse_problem` recibe los textos de la interfaz y **acumula todos los errores** (campo vacío, valor no
  numérico, signo inválido, dimensiones inconsistentes) para mostrarlos juntos con su ubicación.
- Acepta enteros, decimales y fracciones (`parse_number`).

### Forma estándar — `lp/standard.py`
- Si el lado derecho es negativo, se multiplica la fila por −1 y el signo se invierte (`flipped`).
- ≤ → holgura `s` (+1, entra a la base inicial); ≥ → exceso `e` (−1) y artificial `a`; = → artificial `a`.
- Las artificiales cuestan `MNum(0, -1)` = −M. Si se minimiza, se maximiza Z′ = −Z.
- *¿Por qué la artificial en ≥?* Porque el exceso entra con −1 y no sirve de variable básica inicial
  (valdría negativo); la artificial da la base identidad para arrancar.

### Gran M en tablero — `lp/bigm.py` y `lp/common.py`
- Cada iteración: calcula `zj` y `cj − zj` → `choose_entering` (mayor cj − zj positivo; empates, menor
  índice) → `ratio_test` (mínimo de b/columna solo donde la columna es > 0; empates, menor índice) →
  pivoteo (divide la fila pivote y anula el resto de la columna).
- Termina cuando ningún cj − zj es positivo. Si queda una **artificial positiva** en la base → infactible.
  Si la columna que entra **no tiene positivos** → no acotado.
- **Bland:** después de 200 iteraciones `choose_entering` usa la regla de Bland (menor índice) para evitar ciclos.
- Las artificiales que ya salieron no vuelven a entrar.

### Simplex revisado — `lp/revised.py`
- No guarda el tablero: solo **B⁻¹**. En cada iteración: x_B = B⁻¹·b; multiplicadores y = c_B·B⁻¹; costo
  reducido de cada no básica cj − y·aj; solo para la que entra, α = B⁻¹·aₑ y la razón mínima x_B/α.
- B⁻¹ se actualiza pivoteando sobre [B⁻¹ | α] con el mismo pivote.
- *¿Ventaja?* Trabaja con una matriz m×m en vez de m×(n+holguras+artificiales); en problemas grandes y
  dispersos hace menos operaciones. Usa las mismas reglas que la Gran M, por eso recorren las mismas bases
  (la pestaña «Comparar métodos» lo muestra).

### Casos especiales — `lp/analysis.py` (`interpret`)
- **Infactible:** artificial positiva al final. Caso borde: si la Gran M termina «no acotada» con
  artificiales positivas, se resuelve una **fase 1** (minimizar la suma de artificiales) para distinguir
  infactible de no acotado.
- **No acotado:** columna de la que entra sin elementos positivos.
- **Degenerado:** una variable básica vale 0 en el óptimo (suele venir de un empate en la razón mínima,
  que el paso a paso marca).
- **Óptimos múltiples:** una no básica tiene cj − zj = 0; se la hace entrar para encontrar el otro vértice
  óptimo y se informa el segmento.

### Sensibilidad — `lp/analysis.py` (`sensitivity`)
- Se trabaja con la base óptima: B⁻¹, x_B y los costos reales (artificiales en 0).
- **Precio sombra** de Rᵢ = yᵢ (componente i de c_B·B⁻¹), con el signo ajustado si se minimiza o si la fila
  se multiplicó por −1. Es lo que cambia Z por una unidad más de bᵢ.
- **Rango del lado derecho:** el intervalo de δ con x_B + δ·(columna i de B⁻¹) ≥ 0 (la base sigue siendo factible).
- **Costo reducido** de una no básica: cj − zj en el sentido original.
- **Rango de un coeficiente:** básica → intervalo en que todos los cj − zj siguen ≤ 0; no básica → hasta zj.
- Todo es válido **moviendo un solo dato a la vez**.

### Método gráfico — `lp/geometry.py` y `lp/graphical.py`
- `geometry.py` (sin dibujo): vértices = intersecciones de cada par de rectas (incluidos los ejes) que
  cumplen todas las restricciones; región no acotada si existe una dirección d ≥ 0 con A·d compatible.
- `graphical.py` dibuja: región sombreada (recorte de polígono por semiplanos), rectas rotuladas, vértices con
  Z, recta de Z en el óptimo y flecha de mejora. Si es infactible sombrea cada semiplano; si es no acotado
  dibuja la flecha hacia donde Z crece sin límite. Con n ≠ 2 avisa que no aplica.

### Interfaz y salidas
- `app.py` (Streamlit): `session_state` guarda el problema y la solución, así que se edita y se vuelve a
  resolver sin reiniciar. Cada pestaña tiene su ayuda en `interfaz/ayuda.py`.
- `render.py` arma tablas y justificaciones; `pdf_export.py` el PDF (reportlab); `presentation.py` exporta la
  corrida a datos para la animación (`presentacion/`), que solo los dibuja y narra.
- **Arquitectura:** capas con dependencias hacia abajo, núcleo solo con la biblioteca estándar; lo verifica
  `tests/test_arquitectura.py`.

### Pruebas — `tests/`
- `test_problems.py`: los 7 problemas del enunciado, problemas aleatorios **comparados con scipy** (scipy solo
  verifica, nunca produce resultados), sensibilidad comparada re-resolviendo con el lado derecho movido.
- Correr: `pytest tests -q` (47 pruebas).

## 4. Resolver en vivo el problema del docente

1. Escribir el problema con cuidado (signo de cada restricción y lado derecho negativo tal cual).
   Si es largo, usar **➕ Variable / ➕ Restricción**.
2. **Leer en voz alta la «Vista del modelo formulado»** para confirmar con el docente que quedó bien escrito.
3. Resolver con **Gran M, paso a paso**. Narrar: forma estándar (qué variable se agregó y por qué),
   iteración 0 (quién entra y por qué, razón mínima, quién sale, pivote) y el tablero final.
4. Verificar: cambiar a **simplex revisado** y mostrar en «Comparar métodos» que da lo mismo.
5. Si tiene 2 variables, mostrar el **gráfico** y que el óptimo ⭐ coincide.
6. Interpretar un **precio sombra** y un **rango** en «Sensibilidad».
7. Si el caso es especial (infactible, no acotado, múltiples, degenerado), señalar el mensaje y explicar qué lo
   detectó en el tablero.

## 5. Cambios que el docente podría pedir (y dónde hacerlos)

| Pedido | Dónde | Qué cambiar |
|---|---|---|
| Usar siempre la regla de Bland | `lp/common.py` | `BLAND_AFTER = 0` |
| Cambiar el límite de iteraciones | `lp/common.py` | `MAX_ITER` |
| Mostrar más decimales | `lp/numbers.py` | parámetro `places` de `fmt` |
| Agregar un ejemplo | `lp/model.py` | una entrada nueva en `EXAMPLES` (aparece solo en la barra lateral) |
| Cambiar el mensaje de infactible | `lp/analysis.py` | `interpret`, rama `infeasible` |
| Cambiar un texto de ayuda | `interfaz/ayuda.py` | la constante de esa pestaña |
| Cambiar colores del gráfico | `lp/graphical.py` | diccionarios `LIGHT` y `DARK` |

Después de cualquier cambio: `pytest tests -q`.

## 6. Guion del video (máximo 5 minutos)

| Tiempo | Pantalla | Qué decir |
|---|---|---|
| 0:00–0:20 | Portada de la app en línea | Nombre, equipo, qué resuelve, que el método es propio y exacto. |
| 0:20–1:00 | Ingresar el ejemplo 2 (Min, =, ≥, lado derecho negativo) | Validación: escribir una letra en un coeficiente y mostrar el mensaje; corregir. |
| 1:00–2:00 | Paso a paso | Forma estándar (volteo de R3, exceso y artificiales, M simbólica); una iteración completa con su justificación. |
| 2:00–2:40 | Resultado y Comparar métodos | Solución exacta (2/5, 9/5, Z = 17/5); Gran M y revisado coinciden. |
| 2:40–3:20 | Ejemplo 1: gráfico y sensibilidad | Región, vértices, recta de Z; precio sombra de R1 = 14 y su rango. |
| 3:20–4:00 | Casos especiales | Cargar ejemplos 4 y 5: mensaje claro y gráfico (región vacía, flecha no acotada). |
| 4:00–4:40 | Animación | Pestaña 🎬: capítulo 3 o 4 unos segundos. |
| 4:40–5:00 | Exportar | PDF y cierre. |

## 7. Lista para el día

- [ ] Los dos integrantes tienen commits propios en el repositorio.
- [ ] La app en línea abre, y la local también (`streamlit run app.py`).
- [ ] `pytest tests -q` pasa en el equipo que se va a usar.
- [ ] Cada uno practicó explicar **todas** las secciones de la parte 3, no solo la suya.
- [ ] Practicaron resolver al menos 3 problemas nuevos (uno de cada caso especial).
