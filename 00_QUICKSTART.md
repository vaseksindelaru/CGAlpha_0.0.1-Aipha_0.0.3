# CGAlpha Quick Start (5 minutos)

Esta guía es el punto de entrada rápido para operar CGAlpha sin leer toda la constitución.

## 1) Verificar que el entorno está vivo

```bash
cgalpha --version
cgalpha status show
```

Qué esperar:
- versión del CLI visible,
- estado general sin errores críticos.

## 2) Verificar salud del asistente local (si usas LLM local)

```bash
cgalpha ask-health --smoke
```

Qué esperar:
- `ollama_status: up`,
- `smoke_test: ok`.

## 3) Ejecutar chequeo rápido de calidad del sistema

```bash
python -m pytest -q
```

Qué esperar:
- suite en verde (sin fallos).

## 4) Ejecutar análisis causal actual

```bash
cgalpha auto-analyze --working-dir .
```

Qué revisar en el resultado:
- `blind_test_ratio`,
- cobertura de datos,
- decisión final (`HOLD` o `PROCEED_V03`).

## 5) Navegar documentación clave desde CLI

```bash
cgalpha docs list
cgalpha docs show master
cgalpha docs show guide
cgalpha docs show quickstart
cgalpha docs show version
```

## Si algo falla

1. Ejecuta `cgalpha ask-health --smoke`.
2. Corre `python -m pytest -q` para detectar roturas reales.
3. Revisa `docs/CGALPHA_MASTER_DOCUMENTATION.md`.
4. No apliques cambios de código si los tests no están en verde.

## Regla operativa

Primero estabilidad, después evolución:
- test en verde,
- gate de datos razonable,
- y recién entonces avanzar de fase.
