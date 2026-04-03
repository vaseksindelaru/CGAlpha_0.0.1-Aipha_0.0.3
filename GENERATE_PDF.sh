#!/bin/bash

# CGAlpha v2: PDF Master Guide Generator (Bash)

echo "🚀 CGAlpha v2: PDF Master Guide Generator"
echo "======================================================"

# Verificar Pandoc
echo ""
echo "1. Verificando Pandoc..."

if ! command -v pandoc &> /dev/null; then
    echo "⚠ Pandoc no encontrado. Instalando..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        brew install pandoc
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update
        sudo apt-get install -y pandoc
    else
        echo "✗ Por favor instala Pandoc manualmente desde https://pandoc.org/"
        exit 1
    fi
fi

echo "✓ Pandoc verificado"

# Generar PDF
echo ""
echo "2. Generando PDF (esto puede tomar 1-2 minutos)..."

pandoc "CGALPHA_V2_MASTERGUIDE_COMPLETE.md" \
  -o "CGALPHA_V2_COMPLETE_MASTERGUIDE.pdf" \
  --pdf-engine=xelatex \
  --toc \
  --toc-depth=3 \
  --number-sections \
  --highlight-style=kate \
  --variable="geometry:margin=1in" \
  --variable="fontsize:11pt" \
  --variable="linkcolor:blue" \
  --variable="urlcolor:blue" \
  --variable="toccolor:blue" \
  -V mainfont="Calibri" \
  -V monofont="Courier New" \
  -V title="CGAlpha v2: Complete Master Guide" \
  -V author="Vaclav Trading Systems" \
  -V date="$(date +%Y-%m-%d)"

if [ $? -eq 0 ]; then
    echo "✓ PDF generado exitosamente"
else
    echo "✗ Error generando PDF"
    exit 1
fi

# Verificar
echo ""
echo "3. Verificando PDF..."

if [ -f "CGALPHA_V2_COMPLETE_MASTERGUIDE.pdf" ]; then
    SIZE=$(du -sh "CGALPHA_V2_COMPLETE_MASTERGUIDE.pdf" | cut -f1)
    echo "✓ PDF verificado: $SIZE"
else
    echo "✗ PDF no encontrado"
    exit 1
fi

# Resumen
echo ""
echo "======================================================"
echo "✅ COMPLETADO!"
echo "======================================================"
echo ""
echo "📄 PDF Generado: CGALPHA_V2_COMPLETE_MASTERGUIDE.pdf"
echo "📏 Tamaño: $(du -sh CGALPHA_V2_COMPLETE_MASTERGUIDE.pdf | cut -f1)"
echo "📋 Páginas estimadas: ~150"
echo ""
echo "🎯 Próximos pasos:"
echo "  1. Abrir: open CGALPHA_V2_COMPLETE_MASTERGUIDE.pdf"
echo "  2. Leer: Parte 1 (Resumen Ejecutivo)"
echo "  3. Implementar: Semana 1 - Capa 0a"
echo ""
