# 🖥️ Guía de Usuario: CGAlpha v3 Control Room

¡Bienvenido! Entiendo que la interfaz puede parecer abrumadora al principio. Esta guía te explicará detalladamente qué hace cada panel y cómo puedes usarla para supervisar y operar el sistema.

## 📌 Conceptos Clave
La GUI no es solo visual; es una **consola de auditoría**. Su objetivo es darte transparencia total sobre lo que la IA (Lila) está haciendo y permitirte intervenir si el riesgo se dispara.

---

## 1. Dashboard (Misión Control)
Es tu "vista de pájaro". Aquí ves el latido del sistema.
- **Status Pill**: Indica si el sistema está `idle` (esperando), `running` (operando) o en `error`.
- **Market Live**: Muestra el precio actual y, lo más importante, el **Data Quality**. Si ves un aviso naranja o rojo aquí, el sistema dejará de operar para protegerte de datos corruptos.
- **Events Log**: Una lista cronológica de todo lo que ocurre. Los iconos 🚨 indican eventos críticos de seguridad.

## 2. Risk (Gestión de Riesgos)
Aquí controlas la seguridad del capital.
- **Drawdown Bar**: Visualiza cuánto ha caído tu cuenta en la sesión actual.
- **Circuit Breakers**: Interruptores automáticos. Si se activan, detienen la operativa.
- **⚡ Kill-Switch**: El botón rojo. Úsalo en emergencias para desconectar el sistema del exchange en menos de 500ms.
- **Parámetros**: Puedes ajustar los límites de pérdida y tamaño de posición aquí mismo.

## 3. Library (Biblioteca)
El "cerebro pasivo" del sistema.
- **Ingesta**: Puedes subir resúmenes de papers científicos o estrategias aquí.
- **Búsqueda**: Lila consulta esta base de datos para justificar sus decisiones (Teoría Live).
- **Finding/Applicability**: Explican por qué ese documento es relevante para el trading actual.

## 4. Theory Live (Validación de Hipótesis)
Donde la teoría se encuentra con la práctica.
- **Claims**: Puedes escribir una hipótesis (ej: "El RSI sobrecomprado en BTC indica reversión") y Lila la validará contra la biblioteca.
- **Backlog**: Tareas pendientes de investigación que Lila ha identificado como necesarias para mejorar el sistema.

## 5. Experiment Loop (Laboratorio)
Aquí es donde se "cocinan" las nuevas estrategias.
- **Proposal**: Lila propone una hipótesis de trading.
- **Metrics**: Tras ejecutar un experimento, verás el **Sharpe Ratio**, **Win Rate** y si hubo **Leakage** (el pecado capital del trading: usar datos del futuro para entrenar).
- **Approach Histogram**: Muestra qué algoritmos se están usando más (Trend Following vs Mean Reversion, etc.).

## 6. Learning (Memoria Inteligente)
La memoria a largo plazo de Lila.
- **Capas (L0-L4)**: Verás cuántos hechos conoce Lila en cada nivel de profundidad.
- **Regime Shift**: Indica si el mercado ha cambiado de fase (ej: de lateral a tendencia volátil). Lila ajusta su comportamiento basándose en esto.

## 7. Help ? (Centro de Ayuda Interactiva)
**¡Esta es tu mejor herramienta ahora mismo!**
He actualizado esta sección con un motor de búsqueda y artículos detallados. 
- Puedes buscar términos como "Kill-Switch", "Lila" o "VWAP".
- Incluye tutoriales rápidos y un FAQ completo.

---

## 🤖 Cómo hablar con Lila
En la esquina inferior derecha tienes el chat de Lila. Ella puede:
- Darte el estado del sistema (`/status`).
- Explicarte por qué tomó una decisión.
- Ayudarte a configurar los parámetros de riesgo.

> [!TIP]
> Si te sientes perdido, escribe `hola` en el chat de Lila o navega a la pestaña **Help ?** y usa el buscador con palabras clave de lo que veas en pantalla.
