# Generación del PDF Maestro CGAlpha v2

## 🚀 Inicio Rápido

### Opción 1: Usar Script Python (Recomendado)

```bash
cd /home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3

# Hacer ejecutable
chmod +x GENERATE_PDF.py

# Ejecutar
python3 GENERATE_PDF.py

# Resultado: CGALPHA_V2_COMPLETE_MASTERGUIDE.pdf (~15MB, 150 páginas)
```

### Opción 2: Usar Script Bash

```bash
cd /home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3

# Hacer ejecutable
chmod +x GENERATE_PDF.sh

# Ejecutar
./GENERATE_PDF.sh

# Resultado: CGALPHA_V2_COMPLETE_MASTERGUIDE.pdf
```

### Opción 3: Comando Pandoc Directo

```bash
pandoc CGALPHA_V2_MASTERGUIDE_COMPLETE.md \
  -o CGALPHA_V2_COMPLETE_MASTERGUIDE.pdf \
  --pdf-engine=xelatex \
  --toc \
  --toc-depth=3 \
  --number-sections \
  -V mainfont="Calibri" \
  -V monofont="Courier New"
```

---

## 📋 Requisitos

### Pandoc (Motor de Conversión)

**macOS:**
```bash
brew install pandoc
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install pandoc
```

**Windows:**
1. Descargar desde: https://github.com/jgm/pandoc/releases
2. Instalar como de costumbre

**Verificar instalación:**
```bash
pandoc --version
```

---

## 🏗️ Estructura del PDF Resultante

El PDF final contendrá 150+ páginas con:

