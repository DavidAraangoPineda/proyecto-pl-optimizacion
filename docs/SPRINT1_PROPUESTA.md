# Sprint 1 — Propuesta (18 de noviembre de 2026)

Según el cronograma del enunciado, la propuesta debe incluir: **lenguaje, método elegido, integrantes y boceto de la interfaz**.

## 1. Integrantes
- David Arango Pineda
- Juan Ignacio Parra

## 2. Lenguaje y tecnología
- **Python 3** con **Streamlit** (interfaz web), **matplotlib** (método gráfico) y **reportlab** (PDF).
- Motor propio con `fractions.Fraction`: aritmética exacta, sin redondeo.
- Verificación: scipy **solo en pruebas**, nunca para producir resultados.

## 3. Método elegido
- **Gran M** sobre tablero (método principal) con M simbólica (`a + b·M`).
- **Simplex revisado** con B⁻¹ explícita (bonificación +0.2: comparar iteraciones de ambos).

## 4. Boceto de la interfaz

```
┌ Barra lateral ──────┐ ┌ Programación Lineal ─────────────────────────────┐
│ Método: ◉ Gran M    │ │ 1. Problema     ◉ Maximizar  ○ Minimizar          │
│         ○ Revisado  │ │ Coef. de Z:  [ x1 ][ x2 ][ x3 ]                   │
│ Modo:   ◉ Paso a    │ │ Restricciones:                                    │
│           paso      │ │   R1  [..][..][..] [≤▾] [LD]                      │
│         ○ Directa   │ │   R2  [..][..][..] [≥▾] [LD]                      │
│ Números: Fracc/Dec  │ │ [+Variable][-Variable][+Restricción][-Restricción]│
│ Cargar ejemplo ▾    │ │ [▶ Resolver]                    [💾 Guardar JSON] │
│ Cargar JSON         │ │ 2. Resultados                                     │
└─────────────────────┘ │ [Resultado][Paso a paso][Gráfico][Sensibilidad]   │
                        │ [Comparar métodos][Exportar PDF]                  │
                        └───────────────────────────────────────────────────┘
```

## 5. Plan de sprints
| Sprint | Fecha | Objetivo |
|---|---|---|
| 1 | 18 nov | Propuesta: lenguaje, método, integrantes, boceto |
| 2 | 27 nov | Avance: entrada del problema y método resolviendo problemas como el 1 y el 3 |
| 3 | 4 dic | Entrega final: paso a paso, gráfico, sensibilidad, casos especiales, manual, video, sustentación |

## 6. Reparto sugerido (para que ambos puedan explicar todo el código)
| Parte | Responsable | Respaldo |
|---|---|---|
| Motor: forma estándar, Gran M, simplex revisado | David | Juan |
| Análisis: casos especiales, sensibilidad | Juan | David |
| Interfaz y validación | Juan | David |
| Método gráfico y PDF | David | Juan |
| Manual, video, pruebas | Ambos | — |
