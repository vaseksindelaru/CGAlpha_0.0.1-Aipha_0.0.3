
# Roadmap de Creación de CGAlpha v3

## Semana 1: Fundamentos y Base Funcional
- Reestructurar carpetas siguiendo Clean Architecture y DDD.  
	_Justificación: Garantiza una base profesional, desacoplada y escalable, facilitando el mantenimiento y la extensión futura._
- Documentar el propósito de cada carpeta con README.md.  
	_Justificación: Permite a cualquier desarrollador entender rápidamente la función de cada módulo y reduce la curva de aprendizaje._
- Implementar la estrategia simple de triple coincidencia como fallback en el motor de trading.  
	_Justificación: Asegura funcionalidad mínima desde el inicio, permitiendo operar y validar el sistema mientras se desarrolla la lógica avanzada._
- Crear knowledge_base/ con CSV inicial de papers y README explicativo.  
	_Justificación: Sienta las bases de la biblioteca inteligente, centralizando la documentación y el conocimiento desde el primer día._
- Validar que el sistema pueda ejecutar trades simples y registrar resultados.  
	_Justificación: Permite comprobar que la arquitectura y la integración básica funcionan correctamente antes de añadir complejidad._

## Semana 2: Biblioteca Inteligente y Documentación
- Ingestar 20 papers clave en la biblioteca (knowledge_base/), rellenando metadatos mínimos.  
	_Justificación: Proporciona una base teórica sólida y relevante, asegurando que las decisiones futuras estén respaldadas por evidencia._
- Documentar cada indicador y decisión en la biblioteca (curator.py, phase_1_trading.py).  
	_Justificación: Facilita la trazabilidad y justificación de cada cambio, permitiendo aprendizaje y mejora continua._
- Mapear los primeros trades reales a referencias teóricas en la biblioteca.  
	_Justificación: Vincula la práctica con la teoría, asegurando que cada resultado pueda ser explicado y auditado._
- Añadir scripts para búsqueda y recuperación básica de información en knowledge_base/.  
	_Justificación: Permite explotar el conocimiento almacenado y agiliza la consulta de información relevante para el desarrollo y la toma de decisiones._

## Semana 3: Modularización y Primeros Experimentos
- Separar lógica de trading, indicadores y orquestación en módulos independientes.  
	_Justificación: Mejora la mantenibilidad, permite pruebas aisladas y facilita la evolución de cada componente sin afectar el resto._
- Implementar tests unitarios para la estrategia simple y los indicadores.  
	_Justificación: Garantiza la calidad del código y permite detectar errores rápidamente durante el desarrollo iterativo._
- Realizar backtesting con datos reales y documentar resultados en la biblioteca.  
	_Justificación: Valida la efectividad de la estrategia y proporciona evidencia empírica para futuras mejoras._
- Ajustar la estructura de la biblioteca según necesidades emergentes.  
	_Justificación: Permite que la biblioteca evolucione de forma orgánica, adaptándose a los retos y aprendizajes reales del proyecto._

## Semana 4: Integración y Mejora Continua
- Integrar la biblioteca inteligente con el motor de trading para trazabilidad automática.  
	_Justificación: Automatiza la documentación y el registro de decisiones, reduciendo errores humanos y asegurando memoria viva del sistema._
- Añadir documentación de cada experimento, ajuste y resultado relevante.  
	_Justificación: Refuerza la cultura de aprendizaje y mejora continua, facilitando auditorías y revisiones._
- Preparar la infraestructura para incorporar análisis de order book (OBI) y lógica avanzada en futuras fases.  
	_Justificación: Deja el sistema listo para escalar y evolucionar hacia funcionalidades más complejas sin reestructuraciones costosas._
- Revisar y mejorar la arquitectura según feedback y resultados reales.  
	_Justificación: Permite corregir desvíos y optimizar el diseño en base a la experiencia y el uso real._

## Semana 5+: Escalabilidad y Evolución
- Iniciar implementación de OBI y lógica avanzada en domain/models/ y indicators/.  
	_Justificación: Permite avanzar hacia una estrategia profesional y sofisticada, integrando análisis de order book y nuevos indicadores._
- Ampliar la biblioteca con nuevos papers, experimentos y aprendizajes.  
	_Justificación: Mantiene la biblioteca como núcleo de conocimiento actualizado y relevante para el sistema._
- Integrar síntesis automática (LLM local) para justificar decisiones de trading.  
	_Justificación: Aporta explicabilidad y respaldo académico a las decisiones, facilitando la confianza y la validación externa._
- Mantener la documentación y trazabilidad como núcleo del desarrollo.  
	_Justificación: Asegura que cada avance esté respaldado, documentado y pueda ser auditado o replicado en el futuro._

---

> **Nota:** Cada avance debe estar documentado en la biblioteca inteligente, permitiendo aprendizaje iterativo y mejora continua. La estrategia simple sirve como benchmark y fallback durante toda la evolución de v3.
