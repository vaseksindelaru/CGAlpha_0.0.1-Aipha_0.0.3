#!/bin/bash
# scripts/start_redis.sh
# Inicializa Redis para CGAlpha

# Colores
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

echo "🚀 Iniciando Redis Service para CGAlpha..."

# Verificar si redis-server está instalado
if ! command -v redis-server &> /dev/null; then
    echo -e "${RED}❌ redis-server no encontrado.${NC}"
    echo "Por favor instala Redis: sudo apt-get install redis-server"
    exit 1
fi

# Cargar variables de entorno si existen
if [ -f .env ]; then
    export $(grep -v '^#' .env | xargs)
fi

PORT=${REDIS_PORT:-6379}

# Verificar si ya está corriendo en ese puerto
if lsof -i :$PORT > /dev/null; then
    echo -e "${GREEN}✅ Redis ya está corriendo en el puerto $PORT${NC}"
    exit 0
fi

# Intentar iniciar servicio systemd si es posible
if systemctl is-active --quiet redis; then
    echo -e "${GREEN}✅ Servicio Redis (systemd) activo.${NC}"
    exit 0
fi

# Si no, intentar iniciarlo localmente en background
echo "Iniciando instancia local en puerto $PORT..."
redis-server --port $PORT --daemonize yes

# Verificar de nuevo
sleep 1
if lsof -i :$PORT > /dev/null; then
    echo -e "${GREEN}✅ Redis iniciado exitosamente.${NC}"
else
    echo -e "${RED}❌ Fallo al iniciar Redis.${NC}"
    exit 1
fi
