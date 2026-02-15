# Code Craft Sage - Fase 2: AST Modifier

## 📋 Overview

Fase 2 implementa modificación segura de código Python usando Abstract Syntax Tree (AST), con backup automático, validación exhaustiva y rollback en caso de error.

## 🎯 Componentes Implementados

### 1. ASTModifier (`ast_modifier.py`)

**Motor de modificación de código** usando AST para cambios precisos y seguros.

**Características:**
- Modificación AST-based (precisa)
- Fallback text-based (robusto)
- Backup automático con timestamp + hash
- Validación de sintaxis post-modificación
- Rollback automático si falla
- Historial de backups

**Ejemplo:**
```python
from cgalpha.codecraft import ASTModifier, TechnicalSpec, ChangeType

modifier = ASTModifier()

spec = TechnicalSpec(
    proposal_id="MOD_001",
    change_type=ChangeType.PARAMETER_CHANGE,
    file_path="oracle/oracle_v2.py",
    class_name="OracleV2",
    attribute_name="confidence_threshold",
    old_value=0.70,
    new_value=0.65,
    data_type="float"
)

result = modifier.modify_file(spec)
# result = {
#     "success": True/False,
#     "backup_path": "path/to/backup",
#     "changes_made": [...],
#     "original_hash": "abc123",
#     "new_hash": "def456"
# }
```

### 2. SafetyValidator (`safety_validator.py`)

**Validador de seguridad** para verificar que cambios no rompan el código.

**Checks implementados:**
- ✅ Sintaxis válida (AST parse + compile)
- ✅ Imports intactos
- ✅ Consistencia de tipos
- ✅ Rangos de validación
- ✅ Risk scoring (0-1)

**Ejemplo:**
```python
from cgalpha.codecraft import SafetyValidator

validator = SafetyValidator()

validation = validator.validate_change(spec, original_code, modified_code)
# validation = {
#     "syntax_valid": True,
#     "imports_intact": True,
#     "type_consistency": True,
#     "risk_score": 0.0,  # 0 = sin riesgo
#     "warnings": [],
#     "errors": []
# }
```

## 🔄 Flujo de Modificación

```
1. TechnicalSpec → Validar spec (SafetyValidator)
2. Crear Backup →  .bak con timestamp + hash
3. Leer código → Parse AST
4. Modificar → AST modification o text fallback
5. Validar → Syntax check + compile test
6. Escribir → Si válido, guardar; si no, rollback
7. Retornar → Result dict con métricas
```

## 🛡️ Características de Seguridad

### Backup Automático
- **Naming**: `{filename}_{timestamp}_{hash}.py.bak`
- **Location**: `aipha_memory/temporary/ast_backups/`
- **Content**: Código original completo
- **Retention**: Indefinido (manual cleanup)

### Validación Multi-Capa
1. **Pre-validación**: TechnicalSpec.is_valid()
2. **Modificación**: AST-based con fallback
3. **Post-validación**: Syntax + compile check
4. **Risk Scoring**: 0.0-1.0 basado en múltiples factores

### Rollback Automático
- Si validación falla → restaurar desde backup
- Si excepción durante modificación → restaurar
- Logs detallados de cada paso

## 📊 Risk Scoring

Factores que aumentan risk score:

| Factor | Risk Increment |
|--------|----------------|
| Sintaxis inválida | +0.5 (crítico) |
| Imports modificados | +0.2 |
| Tipo inconsistente | +0.3 |
| Cambio >50% en valor | +0.1 |
| Archivo crítico (oracle, trading, etc) | +0.1 |

**Risk Score Interpretation:**
- **0.0-0.2**: Bajo riesgo (OK automático)
- **0.2-0.5**: Riesgo moderado (review recomendado)
- **0.5-1.0**: Alto riesgo (requires approval)

## 🧪 Testing

**Coverage**: >80% (11/11 tests pasando)

```bash
pytest tests/test_codecraft/test_codecraft_phase2.py -v
```

**Test categories:**
- AST Modifier (initialization, modification, backup, validation)
- Safety Validator (syntax, imports, types, risk scoring)
- Integration (end-to-end workflow)

## 🚀 Demo

```bash
python examples/codecraft_phase2_demo.py
```

**Demos incluidos:**
1. Modificación AST completa
2. Validación de seguridad
3. Workflow completo (parse → modify → validate)
4. Backup y rollback

## 📊 Resultados de Fase 2

✅ **11 tests pasando** (100% success rate)  
✅ **AST modification** funcionando  
✅ **Text fallback** operativo  
✅ **Backup automático** con historial  
✅ **Safety validation** comprehensiva  
✅ **Risk scoring** implementado  

## 🔜 Próximos Pasos (Fase 3)

1. **Test Generator** - Generación automática de tests unitarios
2. **Git Automator** - Creación de ramas y commits
3. **CLI Integration** - Comandos `aipha codecraft`
4. **Orchestrator** - Integración completa end-to-end

---  

**Versión**: 0.2.0-phase2  
**Estado**: ✅ Completado  
**Siguiente**: Fase 3 - Test Generator & Git Automator
