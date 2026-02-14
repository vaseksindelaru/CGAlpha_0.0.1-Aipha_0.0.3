# Code Craft Sage - Fase 3: Test Generator

## Resumen Ejecutivo

La Fase 3 de Code Craft Sage implementa el **Test Generator**, un componente dual responsable de:

1. **Generar tests unitarios específicos** para cada cambio de código (usando Jinja2 Templates)
2. **Ejecutar la suite de tests existente** para validar NO REGRESIÓN (Regression Test)
3. **Verificar la cobertura de código** (Coverage > 80%)

Esta fase es crítica para cumplir con los requisitos de calidad definidos en la **Parte 9 de la Constitución**, que establece que Code Craft Sage debe generar Unit Tests, Integration Tests y validar Regression Tests con cobertura mínima del 80%.

---

## Constitución Compliance (Parte 9)

### Requisitos Constitucionales

Según la Parte 9 de la Constitución, Code Craft Sage debe:

| Requisito | Descripción | Implementación |
|-----------|-------------|----------------|
| **Unit Tests** | Generar tests unitarios para cada cambio | [`_generate_unit_test()`](../cgalpha/codecraft/test_generator.py:95) |
| **Integration Tests** | Ejecutar tests de integración existentes | [`_run_regression_tests()`](../cgalpha/codecraft/test_generator.py:195) |
| **Regression Tests** | Validar que no se rompa funcionalidad existente | [`_run_regression_tests()`](../cgalpha/codecraft/test_generator.py:195) |
| **Coverage** | Cobertura mínima del 80% | [`_check_coverage()`](../cgalpha/codecraft/test_generator.py:265) |

### Estrategia de Cumplimiento

#### 1. Unit Tests (Tests Unitarios)

**Implementación:**
- El método [`_generate_unit_test()`](../cgalpha/codecraft/test_generator.py:95) genera automáticamente un archivo de test específico para cada cambio
- Utiliza templates Jinja2 para generar código de test determinista y seguro
- El test generado valida:
  - Que el nuevo valor se haya aplicado correctamente
  - Que el tipo de dato sea correcto
  - Que el valor esté dentro de los rangos válidos (si aplica)

**Ejemplo de Test Generado:**
```python
def test_threshold_updated_to_0_5():
    """Unit Test: Validates that threshold was updated to 0.5."""
    obj = OracleEngine()
    assert obj.threshold == 0.5, \
        f"Expected threshold to be 0.5, got {obj.threshold}"
```

#### 2. Integration Tests (Tests de Integración)

**Estrategia Pragmática:**
- Generar "Integration Tests" completos automáticamente es frágil y propenso a errores
- En su lugar, nos aseguramos de **ejecutar los tests de integración existentes**
- Esto protege el estatus "Golden Master" de Aipha (123/123 tests pasando)

**Implementación:**
- El método [`_find_related_tests()`](../cgalpha/codecraft/test_generator.py:235) busca tests existentes relacionados con el módulo modificado
- Estos tests se ejecutan como parte de la validación de regresión

#### 3. Regression Tests (Tests de Regresión)

**CRÍTICO:** El sistema NO debe permitir un cambio si rompe aunque sea UNO de los tests existentes.

**Implementación:**
- El método [`_run_regression_tests()`](../cgalpha/codecraft/test_generator.py:195) ejecuta pytest sobre todos los tests existentes relacionados
- Si CUALQUIER test falla, el cambio es rechazado
- Esto cumple con el requisito de "Triple Barrera" definido en la Constitución

**Flujo de Validación:**
```
Parser (Fase 1)
    ↓
AST Modifier (Fase 2) → Código modificado
    ↓
Test Generator (Fase 3):
    a. Escribe test_change_prop_001.py
    b. Ejecuta pytest tests/test_oracle.py (Tests viejos)
       ¿Pasan? Sí → Continuar
       ¿Pasan? No → RECHAZAR (Regresión detectada)
    c. Ejecuta pytest --cov oracle
       ¿Cobertura > 80%? Sí → Continuar
       ¿Cobertura > 80%? No → ADVERTENCIA CRÍTICA
    d. Si todo OK → Code Craft Sage devuelve "Éxito"
```

#### 4. Coverage (Cobertura de Código)

**Requisito:** Cobertura mínima del 80%

**Implementación:**
- El método [`_check_coverage()`](../cgalpha/codecraft/test_generator.py:265) ejecuta `pytest --cov` para medir la cobertura
- Si la cobertura cae por debajo del 80%, se emite una advertencia crítica
- La configuración de cobertura está definida en [`pyproject.toml`](../../pyproject.toml:38)

**Configuración en pyproject.toml:**
```toml
[tool.coverage.run]
source = ["cgalpha", "core", "oracle", "aiphalab"]

[tool.coverage.report]
precision = 2
show_missing = true
```

---

## Arquitectura del Test Generator

### Componentes Principales

#### 1. Clase `TestGenerator`

Ubicación: [`cgalpha/codecraft/test_generator.py`](../cgalpha/codecraft/test_generator.py)

**Responsabilidades:**
- Generar archivos de test unitario específicos para cambios
- Ejecutar pytest para detectar regresiones
- Verificar cobertura de código
- Reportar estado global de validación

**API Pública:**

```python
class TestGenerator:
    def __init__(self, template_dir: str = "cgalpha/codecraft/templates/"):
        """Inicializa el TestGenerator con directorio de templates."""
        
    def generate_and_validate(self, spec: TechnicalSpec, modified_file_path: str) -> Dict:
        """
        Genera test nuevo y ejecuta suite de validación completa.
        
        Returns:
            {
                "new_test_path": str,
                "new_test_status": "passed"|"failed",
                "regression_status": "passed"|"failed",
                "coverage_percentage": float,
                "overall_status": "ready"|"needs_fix",
                "details": {
                    "new_test_output": str,
                    "regression_output": str,
                    "coverage_output": str,
                    "warnings": List[str]
                }
            }
        """
```

#### 2. Métodos Privados

| Método | Responsabilidad |
|--------|-----------------|
| [`_generate_unit_test()`](../cgalpha/codecraft/test_generator.py:95) | Genera el archivo del test unitario específico |
| [`_run_new_test()`](../cgalpha/codecraft/test_generator.py:175) | Ejecuta el test recién generado |
| [`_run_regression_tests()`](../cgalpha/codecraft/test_generator.py:195) | Ejecuta pytest en el módulo objetivo para detectar fallos |
| [`_find_related_tests()`](../cgalpha/codecraft/test_generator.py:235) | Busca archivos de tests relacionados con el módulo |
| [`_check_coverage()`](../cgalpha/codecraft/test_generator.py:265) | Ejecuta pytest --cov y retorna el porcentaje |
| [`_determine_overall_status()`](../cgalpha/codecraft/test_generator.py:325) | Determina el estado global de validación |
| [`_collect_warnings()`](../cgalpha/codecraft/test_generator.py:355) | Recopila advertencias basadas en el estado de validación |

---

## Jinja2 Templates

### Template para Cambios de Parámetros

Ubicación: [`cgalpha/codecraft/templates/parameter_change_test.j2`](../cgalpha/codecraft/templates/parameter_change_test.j2)

**Estructura:**
```jinja2
"""
Autogenerated Unit Test by Code Craft Sage
Proposal: {{ proposal_id }}
Change: {{ attribute_name }} {{ old_value }} → {{ new_value }}
Generated: {{ timestamp }}
"""

import pytest
from {{ module_path }} import {{ class_name }}

def test_{{ attribute_name }}_updated_to_{{ new_value|replace('.', '_') }}():
    """Unit Test: Validates that {{ attribute_name }} was updated to {{ new_value }}."""
    obj = {{ class_name }}()
    assert obj.{{ attribute_name }} == {{ new_value }}

def test_{{ attribute_name }}_type_is_{{ data_type }}():
    """Unit Test: Validates that {{ attribute_name }} has correct type."""
    obj = {{ class_name }}()
    actual_value = obj.{{ attribute_name }}
    # Type validation based on data_type
```

### Templates Adicionales

El sistema soporta múltiples tipos de cambios, cada uno con su template:

| Tipo de Cambio | Template |
|----------------|----------|
| `PARAMETER_CHANGE` | `parameter_change_test.j2` |
| `METHOD_ADDITION` | `method_addition_test.j2` |
| `CLASS_MODIFICATION` | `class_modification_test.j2` |
| `CONFIG_UPDATE` | `config_update_test.j2` |
| `IMPORT_ADDITION` | `import_addition_test.j2` |
| `DOCSTRING_UPDATE` | `docstring_update_test.j2` |

---

## Flujo de Trabajo Completo

### Diagrama de Secuencia

```
Usuario
    ↓ Propuesta de cambio
ProposalParser (Fase 1)
    ↓ TechnicalSpec
ASTModifier (Fase 2)
    ↓ Código modificado
TestGenerator (Fase 3)
    ↓
    ├─→ _generate_unit_test() → test_change_prop_001.py
    ├─→ _run_new_test() → "passed"|"failed"
    ├─→ _run_regression_tests() → "passed"|"failed"
    └─→ _check_coverage() → 82.5%
    ↓
    _determine_overall_status()
    ↓
    "ready"|"needs_fix"
    ↓
    Usuario (Resultado)
```

### Ejemplo de Uso

```python
from cgalpha.codecraft.test_generator import TestGenerator
from cgalpha.codecraft.technical_spec import TechnicalSpec, ChangeType

# Crear especificación técnica
spec = TechnicalSpec(
    proposal_id="prop_001",
    change_type=ChangeType.PARAMETER_CHANGE,
    file_path="core/oracle.py",
    class_name="OracleEngine",
    attribute_name="threshold",
    old_value=0.3,
    new_value=0.5,
    data_type="float",
    validation_rules={"min": 0.0, "max": 1.0}
)

# Generar y validar tests
generator = TestGenerator()
result = generator.generate_and_validate(spec, "core/oracle.py")

# Analizar resultado
if result["overall_status"] == "ready":
    print("✓ Cambio aprobado")
    print(f"  - Nuevo test: {result['new_test_status']}")
    print(f"  - Regresión: {result['regression_status']}")
    print(f"  - Cobertura: {result['coverage_percentage']}%")
else:
    print("✗ Cambio rechazado")
    for warning in result["details"]["warnings"]:
        print(f"  - {warning}")
```

---

## Requisitos de Calidad

### Triple Barrera de Calidad

El Test Generator implementa una "Triple Barrera" para asegurar calidad:

1. **Barrera 1: Unit Test**
   - El test generado debe ser ejecutable y pasar
   - Valida que el cambio se aplicó correctamente

2. **Barrera 2: Regression Test**
   - Todos los tests existentes deben seguir pasando
   - Si falla CUALQUIER test, el cambio es rechazado

3. **Barrera 3: Coverage**
   - La cobertura debe ser >= 80%
   - Si cae por debajo, se emite advertencia crítica

### Estados de Validación

| Estado | Descripción | Acción |
|--------|-------------|--------|
| `ready` | Todas las barreras pasaron | Aprobar cambio |
| `needs_fix` | Alguna barrera falló | Rechazar cambio y revisar |

### Advertencias

El sistema genera advertencias en diferentes niveles:

- **CRITICAL:** Violación de requisitos constitucionales (regresión, cobertura < 80%)
- **WARNING:** El nuevo test falló
- **INFO:** Cobertura aceptable pero mejorable (< 90%)

---

## Integración con el Ecosistema

### Vínculo con Aipha

- La Fase 1 menciona que Aipha ya tiene tests (123/123 pasando)
- El `TestGenerator` de Fase 3 se encarga de proteger ese estatus "Golden Master"
- No es solo crear, es **proteger**

### Vínculo con CGAlpha

- Al exigir cobertura >80%, nos aseguramos de que el "Cerebro" (CGAlpha) no genere código "zombie"
- Código "zombie" = código que nadie puede mantener ni auditar en el futuro

### Vínculo con Code Craft Sage

- Fase 1: ProposalParser - Convierte propuestas en especificaciones técnicas
- Fase 2: AST Modifier - Aplica cambios al código
- Fase 3: Test Generator - Valida que los cambios sean seguros y de calidad

---

## Configuración

### Dependencias Requeridas

Las siguientes dependencias ya están en [`requirements.txt`](../../requirements.txt):

```
pytest>=7.0.0
pytest-cov>=4.0.0
pytest-mock>=3.10.0
jinja2>=3.0.0
```

### Configuración de pytest

Archivo: [`pytest.ini`](../../pytest.ini)

```ini
[pytest]
pythonpath = .
testpaths = tests
python_files = test_*.py
```

### Configuración de cobertura

Archivo: [`pyproject.toml`](../../pyproject.toml)

```toml
[tool.coverage.run]
source = ["cgalpha", "core", "oracle", "aiphalab"]

[tool.coverage.report]
precision = 2
show_missing = true
```

---

## Testing del Test Generator

### Tests Unitarios

Para probar el Test Generator:

```bash
# Ejecutar tests del Test Generator
pytest tests/test_test_generator.py -v

# Ejecutar con cobertura
pytest tests/test_test_generator.py --cov=cgalpha.codecraft.test_generator
```

### Tests de Integración

Para probar la integración completa:

```bash
# Ejecutar todos los tests de Code Craft Sage
pytest tests/codecraft/ -v

# Ejecutar con cobertura
pytest tests/codecraft/ --cov=cgalpha.codecraft
```

---

## Troubleshooting

### Problema: Tests de regresión fallan

**Causa:** El cambio rompe funcionalidad existente.

**Solución:**
1. Revisar el output de `_run_regression_tests()`
2. Identificar qué tests fallaron
3. Revisar el cambio aplicado por AST Modifier
4. Corregir el cambio o actualizar los tests existentes

### Problema: Cobertura baja

**Causa:** El nuevo código no tiene suficiente cobertura.

**Solución:**
1. Revisar el reporte de cobertura (`htmlcov/index.html`)
2. Identificar líneas no cubiertas
3. Añadir tests adicionales manualmente si es necesario

### Problema: Template no encontrado

**Causa:** El template para el tipo de cambio no existe.

**Solución:**
1. Crear el template en `cgalpha/codecraft/templates/`
2. O usar el template genérico `parameter_change_test.j2`

---

## Referencias

- **Constitución:** [`UNIFIED_CONSTITUTION_v0.0.3.md`](../../UNIFIED_CONSTITUTION_v0.0.3.md)
- **Fase 1:** [`phase1_fundamentals.md`](phase1_fundamentals.md)
- **Fase 2:** [`phase2_ast_modifier.md`](phase2_ast_modifier.md)
- **Test Generator:** [`cgalpha/codecraft/test_generator.py`](../cgalpha/codecraft/test_generator.py)
- **Templates:** [`cgalpha/codecraft/templates/`](../cgalpha/codecraft/templates/)

---

## Changelog

### v0.0.1 (2026-02-09)
- Implementación inicial del Test Generator
- Soporte para generación de tests unitarios
- Ejecución de tests de regresión
- Verificación de cobertura de código
- Cumplimiento con Parte 9 de la Constitución
