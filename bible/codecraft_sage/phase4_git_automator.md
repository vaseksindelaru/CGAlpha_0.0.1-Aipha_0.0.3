# Code Craft Sage - Fase 4: Git Automator

## Resumen Ejecutivo

La Fase 4 de Code Craft Sage implementa el **Git Automator**, un componente de versionado control responsable de:

1. **Crear ramas de características aisladas** (nunca toca main/master)
2. **Realizar commits con mensajes estandarizados** (Conventional Commits)
3. **Gestionar el estado del repositorio Git**
4. **Preparar el entorno para una revisión humana futura** (Pull Requests)

Esta fase es crítica para mantener la integridad del repositorio y facilitar la colaboración humana en el proceso de revisión de cambios.

---

## Seguridad Crítica

### Principios de Seguridad

El Git Automator implementa una política de seguridad estricta para proteger el repositorio:

| Principio | Implementación |
|-----------|----------------|
| **NUNCA hacer push automático** | No existe método `push()` o `push_to_remote()` |
| **NUNCA modificar rama principal** | [`PROTECTED_BRANCHES`](../cgalpha/codecraft/git_automator.py:38) incluye main, master, develop, staging, production |
| **Manejo seguro de errores** | [`GitAutomatorError`](../cgalpha/codecraft/git_automator.py:28) para todos los errores |
| **Detección de conflictos** | Reporta conflictos sin intentar resolverlos automáticamente |

### Ramas Protegidas

Las siguientes ramas están protegidas y nunca pueden ser modificadas directamente por el Git Automator:

```python
PROTECTED_BRANCHES = {"main", "master", "develop", "staging", "production"}
```

**Intentar crear una rama de feature o hacer commit en estas ramas resultará en un error:**

```python
GitAutomatorError: SEGURIDAD: No se puede crear feature branch desde rama protegida 'main'.
Por favor, cambia a una rama de desarrollo primero.
```

---

## Arquitectura del Git Automator

### Componentes Principales

#### 1. Clase `GitAutomator`

Ubicación: [`cgalpha/codecraft/git_automator.py`](../cgalpha/codecraft/git_automator.py)

**Responsabilidades:**
- Detectar rama actual
- Crear nueva rama de feature (si no existe)
- Staging de archivos modificados
- Commit con mensaje estructurado
- Retornar el hash del commit

**API Pública:**

```python
class GitAutomator:
    def __init__(self, repo_path: str = "."):
        """Inicializa el GitAutomator con ruta al repositorio."""
        
    def get_status(self) -> Dict:
        """Retorna estado actual del repo (branch, archivos modificados, etc.)."""
        
    def has_uncommitted_changes(self) -> bool:
        """Verifica si hay cambios pendientes."""
        
    def create_feature_branch(self, proposal_id: str) -> str:
        """
        Crea y cambia a una rama de feature.
        Formato: feature/prop_{proposal_id}
        """
        
    def commit_changes(self, spec: TechnicalSpec, files_changed: List[str]) -> str:
        """
        Realiza git add y git commit.
        Genera mensaje de commit estilo Conventional Commits.
        Returns: commit_hash (str)
        """
        
    def get_current_branch(self) -> str:
        """Retorna el nombre de la rama actual."""
        
    def is_protected_branch(self, branch_name: str) -> bool:
        """Verifica si una rama está protegida."""
        
    def get_commit_info(self, commit_hash: str) -> Dict:
        """Retorna información de un commit específico."""
        
    def get_recent_commits(self, limit: int = 10) -> List[Dict]:
        """Retorna los commits más recientes de la rama actual."""
```

#### 2. Excepción `GitAutomatorError`

Excepción base para todos los errores del Git Automator:

```python
class GitAutomatorError(Exception):
    """Excepción base para errores del GitAutomator."""
    pass
```

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
    ↓ Resultado de validación
    ↓ SI Resultado == "ready":
GitAutomator (Fase 4):
    ├─→ create_feature_branch(spec.proposal_id)
    │   └─→ feature/prop_{proposal_id}
    ├─→ commit_changes(spec, [modified_file, test_file])
    │   └─→ commit_hash
    └─→ Retornar "Commit creado con éxito en rama feature/..."
    ↓
Usuario (Resultado)
    ↓
Revisión Humana (Pull Request)
```

### Integración con el Orchestrator

El GitAutomator debe ser invocado **DESPUÉS** de que [`generate_and_validate()`](../cgalpha/codecraft/test_generator.py:45) retorne `"ready"`:

```python
# Flujo lógico en el Orchestrator (futuro)
spec = parser.parse(proposal)           # Fase 1
modified_file = modifier.apply_change(spec)  # Fase 2
result = generator.generate_and_validate(spec, modified_file)  # Fase 3

if result["overall_status"] == "ready":
    # Fase 4: Git Automator
    automator = GitAutomator()
    branch_name = automator.create_feature_branch(spec.proposal_id)
    commit_hash = automator.commit_changes(spec, [modified_file, test_file])
    
    return {
        "status": "success",
        "branch": branch_name,
        "commit": commit_hash,
        "message": "Commit creado con éxito en rama feature/..."
    }
else:
    return {
        "status": "failed",
        "reason": "Validación falló",
        "details": result["details"]
    }
```

---

## Política de Ramas

### Formato de Ramas de Feature

Las ramas de feature siguen el formato:

```
feature/prop_{proposal_id}
```

**Ejemplos:**
- `feature/prop_001`
- `feature/prop_threshold_update`
- `feature/prop_oracle_v2_refactor`

### Creación de Ramas

**Caso 1: Rama no existe**
```python
automator = GitAutomator()
branch_name = automator.create_feature_branch("prop_001")
# Crea nueva rama: feature/prop_prop_001
```

**Caso 2: Rama ya existe**
```python
automator = GitAutomator()
branch_name = automator.create_feature_branch("prop_001")
# Hace checkout a rama existente: feature/prop_prop_001
```

### Restricciones

1. **No se puede crear desde ramas protegidas**
   - Error: `SEGURIDAD: No se puede crear feature branch desde rama protegida 'main'`

2. **No se puede crear con cambios pendientes**
   - Error: `El repositorio tiene cambios pendientes. Por favor, commitea o stash los cambios antes de crear una nueva rama.`

---

## Formato de Mensajes de Commit

### Conventional Commits

El Git Automator genera mensajes de commit siguiendo el estándar **Conventional Commits**:

```
<type>: <description> (CodeCraft Sage)

Proposal ID: {proposal_id}
Change Type: {change_type}

Files changed:
  - {file_path_1}
  - {file_path_2}

Class: {class_name}
Attribute: {attribute_name}
Change: {old_value} → {new_value}

Original Proposal:
  {proposal_text}
```

### Tipos de Commit

| Tipo de Cambio | Tipo de Commit | Descripción |
|----------------|----------------|-------------|
| `PARAMETER_CHANGE` | `feat` | Nueva funcionalidad o cambio de parámetro |
| `METHOD_ADDITION` | `feat` | Nueva funcionalidad o adición de método |
| `CLASS_MODIFICATION` | `refactor` | Refactorización de clase existente |
| `CONFIG_UPDATE` | `chore` | Cambios de configuración |
| `IMPORT_ADDITION` | `chore` | Adición de imports |
| `DOCSTRING_UPDATE` | `docs` | Actualización de documentación |

### Ejemplo de Mensaje de Commit

```
feat: Update threshold to 0.65 (CodeCraft Sage)

Proposal ID: prop_001
Change Type: parameter_change

Files changed:
  - core/oracle.py
  - tests/test_oracle_update_prop_001.py

Class: OracleEngine
Attribute: threshold
Change: 0.3 → 0.65

Original Proposal:
  Update the threshold parameter in OracleEngine from 0.3 to 0.65
```

---

## Manejo de Errores

### Errores Comunes

#### 1. Repositorio No Válido

```python
GitAutomatorError: El directorio '/nonexistent/path' no es un repositorio Git válido
```

**Solución:** Verificar que la ruta apunta a un repositorio Git válido.

#### 2. Repositorio Bare

```python
GitAutomatorError: El repositorio en '/path/to/repo' es un repositorio bare
```

**Solución:** Usar un repositorio no bare (working directory).

#### 3. Rama Protegida

```python
GitAutomatorError: SEGURIDAD: No se puede crear feature branch desde rama protegida 'main'.
Por favor, cambia a una rama de desarrollo primero.
```

**Solución:** Cambiar a una rama de desarrollo antes de crear feature branch.

#### 4. Cambios Pendientes

```python
GitAutomatorError: El repositorio tiene cambios pendientes.
Por favor, commitea o stash los cambios antes de crear una nueva rama.
```

**Solución:** Commitear o hacer stash de los cambios pendientes.

#### 5. Archivo Inexistente

```python
GitAutomatorError: El archivo 'nonexistent.py' no existe en el repositorio.
```

**Solución:** Verificar que los archivos existen antes de hacer commit.

#### 6. Conflictos de Merge

**Nota:** El Git Automator NO resuelve conflictos automáticamente. Si se detectan conflictos, se reporta el error:

```python
GitAutomatorError: Conflicto detectado, intervención manual requerida.
```

**Solución:** Resolver conflictos manualmente y continuar.

---

## Ejemplo de Uso

### Uso Básico

```python
from cgalpha.codecraft.git_automator import GitAutomator
from cgalpha.codecraft.technical_spec import TechnicalSpec, ChangeType

# Crear automator
automator = GitAutomator()

# Crear rama de feature
branch_name = automator.create_feature_branch("prop_001")
print(f"Rama creada: {branch_name}")

# Preparar spec
spec = TechnicalSpec(
    proposal_id="prop_001",
    change_type=ChangeType.PARAMETER_CHANGE,
    file_path="core/oracle.py",
    class_name="OracleEngine",
    attribute_name="threshold",
    old_value=0.3,
    new_value=0.5,
    data_type="float"
)

# Hacer commit
commit_hash = automator.commit_changes(spec, ["core/oracle.py"])
print(f"Commit creado: {commit_hash}")

# Obtener información del commit
commit_info = automator.get_commit_info(commit_hash)
print(f"Mensaje: {commit_info['message']}")
```

### Uso con Función de Conveniencia

```python
from cgalpha.codecraft.git_automator import create_feature_branch_and_commit
from cgalpha.codecraft.technical_spec import TechnicalSpec, ChangeType

# Preparar spec
spec = TechnicalSpec(
    proposal_id="prop_001",
    change_type=ChangeType.PARAMETER_CHANGE,
    file_path="core/oracle.py",
    class_name="OracleEngine",
    attribute_name="threshold",
    old_value=0.3,
    new_value=0.5,
    data_type="float"
)

# Crear rama y hacer commit en una sola llamada
branch_name, commit_hash = create_feature_branch_and_commit(
    spec,
    ["core/oracle.py", "tests/test_oracle_update_prop_001.py"],
    repo_path="."
)

print(f"Rama: {branch_name}")
print(f"Commit: {commit_hash}")
```

---

## Demo Integral

El script [`examples/codecraft_phase4_demo.py`](../../examples/codecraft_phase4_demo.py) demuestra el ciclo completo de Code Craft Sage hasta la Fase 4:

```bash
python examples/codecraft_phase4_demo.py
```

**El demo:**
1. Crea un repositorio Git temporal
2. Parsea una propuesta (Fase 1)
3. Modifica el código (Fase 2)
4. Genera y valida tests (Fase 3)
5. Crea rama Git y hace commit (Fase 4)
6. Muestra el resultado final

---

## Testing

### Ejecutar Tests

```bash
# Ejecutar todos los tests del Git Automator
pytest tests/test_codecraft_phase4.py -v

# Ejecutar con cobertura
pytest tests/test_codecraft_phase4.py --cov=cgalpha.codecraft.git_automator
```

### Tests de Seguridad

Los tests verifican:

1. **No hay método de push automático**
   - Verifica que no existen métodos `push()` o `push_to_remote()`

2. **Protección de ramas principales**
   - Verifica que no se puede crear feature branch desde ramas protegidas
   - Verifica que no se puede hacer commit en ramas protegidas

3. **Manejo de errores**
   - Verifica que todos los errores lanzan `GitAutomatorError`
   - Verifica que los mensajes de error son claros

---

## Configuración

### Dependencias Requeridas

La siguiente dependencia ya está en [`requirements.txt`](../../requirements.txt):

```
gitpython>=3.1.0
```

### Instalación

```bash
pip install gitpython>=3.1.0
```

---

## Integración con el Ecosistema

### Vínculo con Fases Anteriores

- **Fase 1 (ProposalParser):** Proporciona el `TechnicalSpec` con el `proposal_id`
- **Fase 2 (ASTModifier):** Modifica el código y retorna la ruta del archivo modificado
- **Fase 3 (TestGenerator):** Genera tests y valida que todo funciona correctamente
- **Fase 4 (GitAutomator):** Crea rama y hace commit SOLO si la validación fue exitosa

### Vínculo con el Futuro

- **Pull Requests:** Las ramas de feature creadas por el Git Automator están listas para ser convertidas en Pull Requests
- **Code Review:** Los commits con mensajes estandarizados facilitan la revisión humana
- **CI/CD:** Los commits pueden ser integrados con pipelines de CI/CD

---

## Referencias

- **Constitución:** [`UNIFIED_CONSTITUTION_v0.0.3.md`](../../UNIFIED_CONSTITUTION_v0.0.3.md)
- **Fase 1:** [`phase1_fundamentals.md`](phase1_fundamentals.md)
- **Fase 2:** [`phase2_ast_modifier.md`](phase2_ast_modifier.md)
- **Fase 3:** [`phase3_test_generator.md`](phase3_test_generator.md)
- **Git Automator:** [`cgalpha/codecraft/git_automator.py`](../cgalpha/codecraft/git_automator.py)
- **Demo:** [`examples/codecraft_phase4_demo.py`](../../examples/codecraft_phase4_demo.py)

---

## Changelog

### v0.0.1 (2026-02-09)
- Implementación inicial del Git Automator
- Creación de ramas de feature con formato `feature/prop_{proposal_id}`
- Commits con mensajes estilo Conventional Commits
- Protección de ramas principales (main, master, develop, staging, production)
- Manejo seguro de errores con `GitAutomatorError`
- Sin push automático a remoto
- Demo integral del ciclo completo
- Suite de tests completa
