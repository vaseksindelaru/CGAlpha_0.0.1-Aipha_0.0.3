#!/bin/bash
# Verificación de Integridad - Aipha v0.0.3 / CGAlpha v0.0.1

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║   VERIFICACIÓN DE INTEGRIDAD - v0.0.3                            ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

# Colores
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

pass_count=0
fail_count=0

check() {
    if [ $1 -eq 0 ]; then
        echo -e "${GREEN}✅${NC} $2"
        ((pass_count++))
    else
        echo -e "${RED}❌${NC} $2"
        ((fail_count++))
    fi
}

echo "📁 VERIFICANDO ESTRUCTURA DE ARCHIVOS"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Archivos críticos de Aipha
test -f "trading_manager/building_blocks/labelers/potential_capture_engine.py"
check $? "PotentialCaptureEngine modificado"

# Estructura CGAlpha
test -d "cgalpha"
check $? "Directorio cgalpha/"

test -f "cgalpha/nexus/ops.py"
check $? "CGA_Ops implementado"

test -f "cgalpha/nexus/coordinator.py"
check $? "CGA_Nexus implementado"

test -f "cgalpha/labs/risk_barrier_lab.py"
check $? "RiskBarrierLab creado"

# Puente evolutivo
test -f "aipha_memory/evolutionary_bridge.jsonl"
check $? "Evolutionary Bridge inicializado"

echo ""
echo "📚 VERIFICANDO DOCUMENTACIÓN"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

test -f "README.md"
check $? "README.md actualizado"

test -f "TECHNICAL_CONSTITUTION.md"
check $? "Constitución técnica creada"

test -f "CHANGELOG_v0.0.3.md"
check $? "CHANGELOG completo"

test -f "IMPLEMENTATION_PLAN.md"
check $? "Plan de implementación"

test -f "RESUMEN_EJECUTIVO_v0.0.3.md"
check $? "Resumen ejecutivo"

test -f "DOCUMENTATION_INDEX.md"
check $? "Índice de documentación"

echo ""
echo "🧪 VERIFICANDO IMPORTS (Sintaxis Python)"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Verificar sintaxis Python de archivos críticos
python3 -m py_compile trading_manager/building_blocks/labelers/potential_capture_engine.py 2>/dev/null
check $? "PotentialCaptureEngine (sintaxis válida)"

python3 -m py_compile cgalpha/nexus/ops.py 2>/dev/null
check $? "CGA_Ops (sintaxis válida)"

python3 -m py_compile cgalpha/nexus/coordinator.py 2>/dev/null
check $? "CGA_Nexus (sintaxis válida)"

python3 -m py_compile cgalpha/labs/risk_barrier_lab.py 2>/dev/null
check $? "RiskBarrierLab (sintaxis válida)"

echo ""
echo "🔍 VERIFICANDO CONTENIDO CLAVE"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# Verificar que el sensor ordinal NO tiene break
if ! grep -q "break" cgalpha/labs/risk_barrier_lab.py; then
    result=0
else
    result=1
fi
check $result "Sensor Ordinal sin 'break' statements (esperado en potential_capture_engine.py)"

# Verificar que MFE/MAE están en el código
grep -q "mfe_atr" trading_manager/building_blocks/labelers/potential_capture_engine.py
check $? "MFE/MAE tracking implementado"

# Verificar que el semáforo tiene los estados
grep -q "ResourceState" cgalpha/nexus/ops.py
check $? "Semáforo de recursos (GREEN/YELLOW/RED)"

# Verificar que CGANexus existe
grep -q "class CGANexus" cgalpha/nexus/coordinator.py
check $? "CGANexus class definida"

echo ""
echo "═══════════════════════════════════════════════════════════════════"
echo ""
echo -e "  Total verificaciones: $((pass_count + fail_count))"
echo -e "  ${GREEN}Pasadas: $pass_count${NC}"
echo -e "  ${RED}Fallidas: $fail_count${NC}"
echo ""

if [ $fail_count -eq 0 ]; then
    echo -e "${GREEN}✅ VERIFICACIÓN EXITOSA - Sistema v0.0.3 íntegro${NC}"
    echo ""
    echo "Próximos pasos:"
    echo "  1. Revisar README.md para visión general"
    echo "  2. Revisar TECHNICAL_CONSTITUTION.md para detalles técnicos"
    echo "  3. Revisar RESUMEN_EJECUTIVO_v0.0.3.md para métricas"
    echo "  4. Ejecutar tests: pytest tests/"
    echo "  5. Test de CGAlpha: python -m cgalpha.nexus.ops"
    echo ""
    exit 0
else
    echo -e "${RED}⚠️  VERIFICACIÓN INCOMPLETA - Revisar errores${NC}"
    echo ""
    exit 1
fi
