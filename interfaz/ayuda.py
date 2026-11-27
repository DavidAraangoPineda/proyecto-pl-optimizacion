"""Textos de ayuda de la interfaz: qué hace cada parte de la aplicación y cómo leer lo que muestra.

Están separados de app.py para que la lógica de la interfaz no se mezcle con la redacción, y para
revisarlos en un solo lugar. Son Markdown de Streamlit.
"""

ENTRADA = """
**Cómo escribir el problema**

1. Elija si quiere **maximizar** o **minimizar** Z.
2. En **Función objetivo**, escriba el coeficiente de cada variable en Z.
3. En **Restricciones**, cada fila es una restricción: coeficientes, signo (≤, ≥ o =) y lado derecho.
4. Se aceptan enteros, decimales (`2.5`) y fracciones (`1/3`). El lado derecho puede ser negativo.
5. Todas las variables son **no negativas** (x ≥ 0); no hace falta escribir esas restricciones.

Con **➕/➖ Variable** y **➕/➖ Restricción** cambia el tamaño sin perder lo escrito. Si algún dato
está vacío o no es un número, la aplicación indica exactamente cuál es antes de resolver.
"""

METODOS = """
**Los dos métodos son implementación propia** y trabajan con fracciones exactas (sin errores de redondeo).

- **Gran M (tablero):** agrega variables artificiales a las restricciones ≥ y = y las castiga con −M en Z.
  En cada iteración actualiza **todo el tablero**.
- **Simplex revisado:** sigue exactamente las mismas reglas, pero solo guarda la inversa de la base
  (**B⁻¹**) y calcula lo que necesita en cada paso. Hace menos trabajo en problemas grandes.

M nunca toma un valor numérico: cada costo se guarda como *a + b·M* y se compara primero la parte de M.
"""

RESULTADO = """
**Qué muestra:** la respuesta final del método elegido.

- **Estado:** óptima, infactible (ningún punto cumple todas las restricciones) o no acotada
  (Z puede mejorar sin límite).
- **Valor de Z** y **valor de cada variable** en la solución óptima.
- **Holgura o exceso de cada restricción:**
  - *Holgura* (restricciones ≤): cuánto falta para llegar al límite.
  - *Exceso* (restricciones ≥): cuánto se pasa del mínimo.
  - Una restricción **activa** tiene holgura/exceso 0: se cumple con igualdad y es la que limita la solución.
- **Avisos:** óptimos múltiples (hay más de una solución con el mismo Z) y solución degenerada
  (una variable básica vale 0).
"""

PASO_A_PASO_COMUN = """
**Qué muestra:** cómo llegó el método a la respuesta, iteración por iteración.

1. **Forma estándar:** cada desigualdad se convierte en ecuación.
   - ≤ → se suma una **holgura** *s*.
   - ≥ → se resta un **exceso** *e* y se suma una **artificial** *a*.
   - = → se suma una **artificial** *a*.
   - Si el lado derecho es negativo, primero se multiplica la restricción por −1 (y el signo se invierte).
   - Si se minimiza, se maximiza Z′ = −Z (es el mismo problema).
2. **Cada iteración** responde tres preguntas:
   - **¿Quién entra?** La variable no básica con el mayor costo reducido *cj − zj* positivo: es la que más mejora Z.
   - **¿Quién sale?** La **prueba de la razón mínima**: se divide el lado derecho entre la columna de la
     que entra (solo donde es positiva). La menor razón indica la restricción que se agota primero.
   - **¿Cómo se actualiza?** Pivoteando sobre el elemento donde se cruzan la fila que sale y la columna que entra.
3. **Fin:** cuando ningún *cj − zj* es positivo, ninguna variable puede mejorar Z y la solución es óptima.
   Si al final queda una artificial positiva, el problema es infactible; si la columna que entra no tiene
   elementos positivos, es no acotado.

Colores: 🟩 columna de la variable que entra · 🟥 fila de la variable que sale · 🟨 pivote.
"""

PASO_A_PASO_BIGM = """
**Cómo leer el tablero (Gran M):** cada fila es una variable básica con su costo *cB* y su valor *b*.
La fila **zj** es lo que «cuesta» cada columna con la base actual y la fila **cj − zj** dice cuánto
mejoraría Z por cada unidad de esa variable. El valor de Z está en la columna *b* de la fila zj.
"""

PASO_A_PASO_REVISADO = """
**Cómo leer las tablas (simplex revisado):**

- **B⁻¹ y xB:** la inversa de la base y el valor actual de las básicas, *xB = B⁻¹·b*.
- **α = B⁻¹·aₑ:** la columna de la variable que entra, calculada solo para ella; con ella se hace la razón mínima.
- **Multiplicadores y = cB·B⁻¹:** permiten calcular cada costo reducido sin el tablero completo: *cj − y·aj*.
- **Costos reducidos:** solo de las no básicas; la fila resaltada es la que entra.
"""

ANIMACION = """
**Qué muestra:** «El viaje del Simplex», la explicación animada y narrada de **este mismo problema**,
calculada con el motor propio. Tiene 8 capítulos:

1. El problema y su región factible.
2. La forma estándar (holguras, excesos y artificiales).
3. El recorrido de la Gran M en el tablero: quién entra, la razón mínima, quién sale y el pivote.
4. El mismo recorrido con el simplex revisado (B⁻¹, multiplicadores y costos reducidos) y la comparación.
5. Cómo la Gran M saca a las variables artificiales.
6. La sensibilidad: qué pasa al mover un lado derecho.
7. Los casos especiales (infactible, no acotado, óptimos múltiples, degenerado).
8. El resultado.

**Controles:** clic en la portada o **Av Pág / →** para avanzar, **Re Pág / ←** para retroceder, **1–8** para
ir a un capítulo, **H** para verla de corrido, **F** pantalla completa y **M** silencio. En el panel de la
derecha se cambian la voz, el volumen y el ritmo.
"""

GRAFICO = """
**Qué muestra (solo con 2 variables):**

- Cada restricción es una **recta**; el lado que la cumple se sombrea.
- La **región factible** es la zona que cumple todas a la vez (incluida x₁, x₂ ≥ 0).
- Los **vértices** son las esquinas de la región, con su valor de Z. En un problema lineal, si hay
  óptimo, siempre está en un vértice.
- La **recta de Z** pasa por el óptimo: moverla en la dirección que mejora Z la sacaría de la región.
- Una restricción **redundante** no toca la región: quitarla no cambia nada.
"""

LEER_GRAFICO = """
**Cómo leer el gráfico**
- Zona sombreada: **región factible** (cumple todas las restricciones).
- Líneas de colores: una por restricción (ver la leyenda debajo del gráfico).
- Puntos: **vértices**, con sus coordenadas y su valor de Z.
- ⭐ y recta punteada: el **óptimo** y la recta de Z que pasa por él.
- Flecha: dirección en la que **mejora Z**; ya no se puede avanzar sin salir de la región.
"""

SENSIBILIDAD = """
**Qué muestra:** cuánto se puede cambiar un dato sin que cambie la solución óptima.

- **Precio sombra** de una restricción: cuánto cambia Z por cada unidad que aumenta su lado derecho.
  Es 0 si a la restricción le sobra holgura (más recurso no sirve).
- **Rango del lado derecho:** el intervalo en el que ese precio sombra sigue siendo válido.
- **Costo reducido** de una variable no básica (vale 0): cuánto cambiaría Z si se la obligara a tomar una unidad.
- **Rango del coeficiente:** cuánto puede cambiar el coeficiente de una variable en Z sin que cambie la
  solución óptima.

Los rangos se calculan **moviendo un solo dato a la vez**; si cambian varios, hay que volver a resolver.
"""

COMPARAR = """
**Qué muestra:** las iteraciones de los dos métodos lado a lado.

Los dos usan la misma regla para elegir quién entra (mayor *cj − zj*, empates por menor índice) y quién
sale (razón mínima, empates por menor índice), así que **recorren las mismas bases y llegan al mismo
resultado**. La diferencia está en el trabajo por iteración: el tablero actualiza toda la matriz;
el revisado solo B⁻¹.
"""

EXPORTAR = """
**Qué puede descargar:**

- **PDF:** problema, forma estándar, todas las iteraciones, solución, sensibilidad y gráfico. Útil para
  entregar o imprimir.
- **Presentación animada (HTML):** «El viaje del Simplex» explica este mismo problema por capítulos, con
  narración y animaciones. Es un solo archivo que funciona sin internet.
- **Problema (JSON):** el botón «Guardar problema» bajo el enunciado guarda los datos para cargarlos después
  desde la barra lateral.
"""
