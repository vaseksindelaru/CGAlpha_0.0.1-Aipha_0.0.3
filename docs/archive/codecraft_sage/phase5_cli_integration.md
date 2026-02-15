# Code Craft Sage - Fase 5: CLI Integration

## Resumen Ejecutivo

La Fase 5 de Code Craft Sage implementa la **integración CLI** que conecta todos los componentes anteriores en un pipeline unificado:

- **CodeCraftOrchestrator**: Ejecuta el pipeline completo de 4 fases
- **CLI Integration**: Comando `aipha codecraft` para ejecutar el pipeline
- **Visual Report**: Salida enriquecida con emojis para fácil lectura
- **Status Command**: Verificar estado del sistema

Esta fase es el "Director" que orquesta las Fases 1-4 y proporciona la "Interfaz" para que el usuario interactúe con Code Craft Sage.

---

## Arquitectura del Orchestrator

### Componentes del Pipeline

```
┌─────────────────────────────────────────────────────────────┐
│                    CodeCraftOrchestrator                     │
├─────────────────────────────────────────────────────────────┤
│  Fase 1: ProposalParser                                      │
│           Convierte propuesta en TechnicalSpec              │
├─────────────────────────────────────────────────────────────┤
│  Fase 2: ASTModifier                                        │
│           Modifica el código fuente                          │
├─────────────────────────────────────────────────────────────┤
│  Fase 3: TestGenerator                                      │
│           Genera y valida tests                              │
│           SI FALLA -> ROLLBACK                               │
├─────────────────────────────────────────────────────────────┤
│  Fase 4: GitAutomator                                       │
│           Crea rama y hace commit                            │
└─────────────────────────────────────────────────────────────┘
```

### Clase `CodeCraftOrchestrator`

Ubicación: [`cgalpha/codecraft/orchestrator.py`](../../cgalpha/codecraft/orchestrator.py)

**API Principal:**

```python
class CodeCraftOrchestrator:
    def __init__(self, working_dir: str = ".", auto_rollback: bool = True):
        """
        Inicializa el Orchestrator.
        
        Args:
            working_dir: Directorio de trabajo (raíz del proyecto)
            auto_rollback: Si True, hace rollback si los tests fallan
        """
        
    def execute_pipeline(self, proposal_text: str, proposal_id: str = None) -> Dict:
        """
        Ejecuta el ciclo completo de automejora.
        
        Returns:
            {
                "status": "success"|"failed",
                "proposal_id": str,
                "branch_name": str,
                "commit_hash": str,
                "test_results": dict,
                "changes_summary": dict,
                "errors": list,
                "timing": dict
            }
        """
```

---

## Integración CLI

### Comando Principal

```bash
aipha codecraft apply --text "TU PROPUESTA"
```

### Opciones

| Opción | Descripción |
|--------|-------------|
| `--text` | Texto de la propuesta (requerido) |
| `--id` | ID de la propuesta (opcional) |
| `--working-dir` | Directorio de trabajo (default: `.`) |
| `--no-rollback` | Deshabilitar rollback automático |
| `--verbose` | Mostrar output detallado |

### Ejemplos de Uso

```bash
# Aplicar propuesta directa
aipha codecraft apply --text "Cambiar threshold de 0.3 a 0.65"

# Con ID personalizado
aipha codecraft apply --text "Update confidence" --id my_custom_id

# Directorio específico
aipha codecraft apply --text "Update threshold" --working-dir /path/to/project

# Modo verbose
aipha codecraft apply --text "Update threshold" --verbose
```

### Comando Status

```bash
aipha codecraft status
```

Muestra:
- Estado del sistema Code Craft Sage
- Componentes disponibles
- Estado del repositorio Git
- Última propuesta procesada

---

## Visual Report

### Salida de Éxito

```
🎨 CODE CRAFT SAGE - PIPELINE EXECUTION

[1/4] 🧠 ProposalParser         Done (0.3s)
[2/4] 🔨 ASTModifier            Done (0.8s)
[3/4] 🧪 TestGenerator          Done (0.5s)
        ├─ Unit Test:       PASSED ✅
        ├─ Regression:      PASSED ✅
        └─ Coverage:        82.5%  ✅
[4/4] 📝 GitAutomator           Done (0.2s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ SUCCESS: Change Applied Successfully!

Branch:     feature/prop_20260208_001
Commit:     a1b2c3d

Next Steps:
1. Review changes: git diff main feature/prop_20260208_001
2. Run full tests: pytest
3. Merge when ready: git merge feature/prop_20260208_001
```

### Salida de Error

```
🎨 CODE CRAFT SAGE - PIPELINE EXECUTION

[1/4] 🧠 ProposalParser         Done (0.3s)
[2/4] 🔨 ASTModifier           Done (0.8s)
[3/4] 🧪 TestGenerator         FAILED
        ├─ Unit Test:       PASSED
        ├─ Regression:      FAILED ❌
        └─ Coverage:        65.0%  ❌

🔄 Rollback performed - Original code restored

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
❌ FAILED: Pipeline Execution Failed

Errors:
  1. Validation tests failed

Suggestions:
- Check your proposal text for errors
- Ensure the target file exists
- Verify the class/attribute names are correct
- Run with --verbose for more details
```

---

## Flujo de Trabajo Recomendado

### Paso 1: Aplicar Cambio

```bash
aipha codecraft apply --text "Cambiar confidence_threshold de 0.70 a 0.65"
```

### Paso 2: Revisar Cambios

```bash
# Ver diferencias
git diff main feature/prop_XXXX

# Ver logs
git log --oneline feature/prop_XXXX

# Ver commit específico
git show a1b2c3d
```

### Paso 3: Ejecutar Tests Completos

```bash
# Ejecutar suite de tests
pytest -v

# Ejecutar con cobertura
pytest --cov=.
```

### Paso 4: Mergear (Cuando Listo)

```bash
# Cambiar a main
git checkout main

# Actualizar main
git pull

# Merge feature branch
git merge feature/prop_XXXX

# Eliminar feature branch (opcional)
git branch -d feature/prop_XXXX
```

---

## Códigos de Error

| Código | Significado | Solución |
|--------|-------------|----------|
| 0 | Éxito | Continuar con revisión |
| 1 | Error general | Verificar mensaje de error |
| 2 | Error de parsing | Revisar texto de propuesta |
| 3 | Error de modificación | Verificar archivo objetivo |
| 4 | Tests fallidos | Revisar tests y código |
| 5 | Error de Git | Verificar estado del repo |

---

## API del Orchestrator

### Resultado del Pipeline

```python
{
    "status": "success",  # o "failed"
    "proposal_id": "prop_20260208_001",
    "branch_name": "feature/prop_20260208_001",
    "commit_hash": "a1b2c3d4e5f6...",
    "test_results": {
        "new_test_status": "passed",
        "regression_status": "passed",
        "coverage_percentage": 82.5,
        "overall_status": "ready"
    },
    "changes_summary": {
        "total_phases": 4,
        "phases_completed": 4,
        "rollback_performed": False
    },
    "errors": [],
    "timing": {
        "phase1_parsing": 0.3,
        "phase2_modification": 0.8,
        "phase3_validation": 0.5,
        "phase4_git": 0.2
    },
    "pipeline_history": [
        {"phase": 1, "name": "ProposalParser", "status": "success", "duration": 0.3},
        {"phase": 2, "name": "ASTModifier", "status": "success", "duration": 0.8},
        {"phase": 3, "name": "TestGenerator", "status": "success", "duration": 0.5},
        {"phase": 4, "name": "GitAutomator", "status": "success", "duration": 0.2}
    ]
}
```

---

## Integración con el Sistema

### Dependencias entre Fases

```
Fase 1: ProposalParser
    ↓ (TechnicalSpec)
Fase 2: ASTModifier
    ↓ (modified_file_path, backup_path)
Fase 3: TestGenerator
    ↓ (validation_result)
    ↓ SI "ready": CONTINUA
    ↓ SI "failed": ROLLBACK
Fase 4: GitAutomator
    ↓ (branch_name, commit_hash)
FIN
```

### Backup y Rollback

**Backup:**
- Se crea antes de modificar cualquier archivo
- Se almacena en `aipha_memory/temporary/ast_backups/`
- Formato: `{nombre}_{timestamp}_{uuid}.py.bak`

**Rollback:**
- Automático si `auto_rollback=True`
- Se ejecuta si Fase 3 (Tests) falla
- Restaura el backup original

---

## Testing

### Ejecutar Tests de Integración

```bash
# Todos los tests
pytest tests/test_codecraft_integration.py -v

# Tests específicos
pytest tests/test_codecraft_integration.py::TestCodeCraftOrchestratorIntegration -v

# Con cobertura
pytest tests/test_codecraft_integration.py --cov=cgalpha.codecraft.orchestrator
```

### Tests Incluidos

| Test | Descripción |
|------|-------------|
| `test_execute_pipeline_success` | Verifica ejecución exitosa |
| `test_execute_pipeline_timing` | Verifica timing de fases |
| `test_execute_pipeline_proposal_id` | Verifica ID personalizado |
| `test_backup_creation` | Verifica creación de backup |
| `test_pipeline_creates_git_commit` | Verifica commit Git |
| `test_pipeline_creates_feature_branch` | Verifica rama feature |
| `test_pipeline_generates_test` | Verifica generación de test |

---

## Configuración

### Variables de Entorno

No se requieren variables de entorno adicionales. El Orchestrator usa:
- `working_dir`: Directorio actual o especificado
- `auto_rollback`: Default True

### Dependencias

```bash
# Requeridas
pip install -r requirements.txt

# Incluyen:
# - click>=8.0.0
# - rich>=10.0.0
# - gitpython>=3.1.0
# - jinja2>=3.0.0
# - pytest>=7.0.0
# - pytest-cov>=4.0.0
```

---

## Ejemplo Completo

### 1. Propuesta

```
"Update the confidence_threshold parameter in OracleEngine from 0.70 to 0.65"
```

### 2. Ejecución

```bash
$ aipha codecraft apply --text "Update confidence_threshold from 0.70 to 0.65"

🎨 CODE CRAFT SAGE - PIPELINE EXECUTION

[1/4] 🧠 ProposalParser         Done (0.3s)
[2/4] 🔨 ASTModifier            Done (0.8s)
[3/4] 🧪 TestGenerator          Done (0.5s)
        ├─ Unit Test:       PASSED ✅
        ├─ Regression:      PASSED ✅
        └─ Coverage:        82.5%  ✅
[4/4] 📝 GitAutomator           Done (0.2s)

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
✅ SUCCESS: Change Applied Successfully!

Branch:     feature/prop_20260208_001
Commit:     a1b2c3d

Next Steps:
1. Review changes: git diff main feature/prop_20260208_001
2. Run full tests: pytest
3. Merge when ready: git merge feature/prop_20260208_001
```

### 3. Revisión

```bash
$ git diff main feature/prop_20260208_001
diff --git a/oracle/models/oracle_v2.py b/oracle/models/oracle_v2.py
-    self.confidence_threshold = 0.70
+    self.confidence_threshold = 0.65
```

---

## Solución de Problemas

### Error: "No es un repositorio Git"

```bash
# Verificar que estamos en un repo Git
git status

# Si no existe, inicializar
git init
git add .
git commit -m "Initial commit"
```

### Error: "Target file not found"

```bash
# Verificar que el archivo existe
ls -la oracle/models/

# Revisar el path en la propuesta
# "Update oracle/models/oracle_v2.py"
```

### Error: "Validation tests failed"

```bash
# Verificar detalles con --verbose
aipha codecraft apply --text "..." --verbose

# Revisar tests existentes
pytest tests/ -v
```

---

## Referencias

- **Fase 1:** [`phase1_fundamentals.md`](phase1_fundamentals.md)
- **Fase 2:** [`phase2_ast_modifier.md`](phase2_ast_modifier.md)
- **Fase 3:** [`phase3_test_generator.md`](phase3_test_generator.md)
- **Fase 4:** [`phase4_git_automator.md`](phase4_git_automator.md)
- **Orchestrator:** [`cgalpha/codecraft/orchestrator.py`](../../cgalpha/codecraft/orchestrator.py)
- **CLI Command:** [`aiphalab/commands/codecraft.py`](../../aiphalab/commands/codecraft.py)

---

## Changelog

### v0.0.1 (2026-02-09)
- Implementación inicial del Orchestrator
- Integración CLI con Rich para salida enriquecida
- Comando `aipha codecraft apply`
- Comando `aipha codecraft status`
- Visual Report con emojis
- Backup y Rollback automático
- Tests de integración completos
