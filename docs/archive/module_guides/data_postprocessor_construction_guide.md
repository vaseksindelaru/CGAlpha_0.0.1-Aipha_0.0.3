# Guía de Construcción: Data Postprocessor

Esta guía detalla el flujo lógico y la implementación del sistema de auto-mejora de Aipha, basado en el análisis post-mortem de los eventos de trading.

## 1. El Concepto de Feedback Post-Paso 1
El sistema no solo ejecuta órdenes; evalúa qué sucedió después de que una barrera fue tocada. El flujo se divide en cuatro fases críticas:

### Fase 1: Análisis Inicial
Se calcula la barrera usando el estado actual del sistema (multiplicador base).
- **Input**: Historial de precios reciente.
- **Output**: Precio de la barrera (`barrier_price`).

### Fase 2: Simulación y Clasificación del Evento
Es el análisis de lo que el mercado hizo *después* de alcanzar el precio crítico.
- **Escenario de Ruido**: El precio toca la barrera (o se acerca mucho), el trade se cierra en pérdida, pero inmediatamente después el precio se recupera y supera el precio de entrada.
- **Clasificación**: `{'outcome': -1.0, 'reason': 'noise'}`.

### Fase 3: El Proceso de Aprendizaje (`learn`)
Cuando el sistema recibe un feedback de tipo `noise`, reacciona ampliando su margen de seguridad.
```python
if outcome < 0 and reason == 'noise':
    self.multiplier += self.sensitivity
```
Este ajuste es **permanente** para el objeto, lo que significa que la próxima vez que se enfrente a una situación similar, será más tolerante.

### Fase 4: Verificación del Aprendizaje
Se re-ejecuta el proceso con los mismos datos iniciales. Si la nueva `barrier_price` es más lejana que la anterior, el sistema ha "aprendido" exitosamente a ignorar ese nivel de ruido específico.

---

## 2. Implementación Técnica
Para extender esta capa, se deben seguir estos principios:

### Estructura del Feedback
El diccionario de feedback es el contrato entre la ejecución (Trading Manager/Oracle) y la mejora (Data Postprocessor).
- `outcome`: Cuantifica el éxito/fracaso.
- `reason`: Explica la naturaleza del movimiento del mercado.

### Sensibilidad (`sensitivity`)
Es la velocidad de aprendizaje. 
- Un valor muy alto (ej: 0.5) puede hacer que el sistema reaccione de forma exagerada a un solo evento.
- Un valor muy bajo (ej: 0.01) requerirá muchos eventos para notar un cambio significativo.

---

## 3. Conexión con el Resto del Sistema
El Data Postprocessor no vive aislado. Su flujo ideal es:
1. **Trading Manager** detecta la señal.
2. **Oracle** valida la señal.
3. **Data Postprocessor** observa el resultado final y ajusta los parámetros del Trading Manager para la próxima señal.

## 4. Próximos Pasos
- **Auto-Sensibilidad**: Hacer que la `sensitivity` también sea dinámica basándose en la frecuencia de los errores.
- **Múltiples Razones**: Añadir clasificaciones como `'volatility_spike'` o `'liquidity_gap'` para ajustes más granulares.
- **Persistencia de Mejoras**: Guardar el estado de los multiplicadores aprendidos en la base de datos DuckDB del Data Processor.
