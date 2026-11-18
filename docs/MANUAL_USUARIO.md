# Manual de usuario (máx. 5 páginas)

> Pendiente: agregar capturas de pantalla de dos problemas resueltos (sugeridos: ejemplo 1 con gráfico y ejemplo 2 con =, ≥ y LD negativo).

## 1. Iniciar la aplicación
`streamlit run app.py` y abrir `http://localhost:8501`.

## 2. Ingresar un problema
1. Elegir **Maximizar** o **Minimizar**.
2. Escribir los coeficientes de la función objetivo (enteros, decimales o fracciones como `1/3`).
3. Escribir cada restricción: coeficientes, signo (≤, ≥, =) y lado derecho (puede ser negativo). Todas las variables son ≥ 0.
4. Usar **➕/➖ Variable** y **➕/➖ Restricción** para cambiar el tamaño sin perder lo escrito.
5. Si hay campos vacíos o valores no numéricos, la aplicación lista cada error con su ubicación.

## 3. Resolver
Elegir en la barra lateral el **método** (Gran M o simplex revisado) y el **modo**:
- **Solución directa:** solo el resultado.
- **Paso a paso:** forma estándar e iteraciones con justificación.

Pulsar **▶ Resolver**. Para cambiar el problema basta editar y volver a resolver; no hace falta reiniciar.

## 4. Leer los resultados
- **Resultado:** valor de cada variable, Z, holgura/exceso por restricción y avisos (infactible, no acotado, óptimos múltiples, degenerado).
- **Paso a paso:** 🟩 columna que entra, 🟥 fila que sale, 🟨 pivote.
- **Método gráfico:** solo con 2 variables.
- **Sensibilidad:** precios sombra, costos reducidos y rangos con su interpretación.
- **Comparar métodos:** iteraciones de ambos métodos lado a lado.
- **Exportar:** PDF del paso a paso.

## 5. Guardar y cargar
**💾 Guardar problema (JSON)** y **Cargar problema (JSON)** en la barra lateral. Hay ejemplos en `examples/`.
