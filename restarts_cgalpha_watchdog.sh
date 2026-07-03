#!/bin/bash
# CGAlpha Auto-Recovery Script after power outage
# Run as: source /home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3/restarts_cgalpha_watchdog.sh

set -euo pipefail

# Configuration
PROJECT_ROOT="/home/vaclav/CGAlpha_0.0.1-Aipha_0.0.3"
WATCHDOG_LOG="$PROJECT_ROOT/logs/watchdog-$$.log"
WATCHDOG_SCRIPT="$PROJECT_ROOT/harness_watchdog.py"
MAX_RESTART_ATTEMPTS=3
RETRY_DELAY=5

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

cd "$PROJECT_ROOT" || exit 1

log() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')]${NC} $1"
}

warn() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if watchdog is running
check_watchdog() {
    local count=$(ps aux | grep "harness_watchdog.py" | grep -v grep | wc -l)
    if [ "$count" -eq 0 ]; then
        return 1
    elif [ "$count" -gt 1 ]; then
        warn "Found $count watchdog processes (duplicates detected)"
        # Kill all duplicates
        pkill -9 -f "harness_watchdog.py" 2>/dev/null || true
        sleep 1
        return 1
    fi
    return 0
}

# Check if UI server is responding
check_ui_server() {
    local port=8080
    local url="http://localhost:$port/"
    
    if ! curl -s --max-time 3 "$url" >/dev/null 2>&1; then
        return 1
    fi
    return 0
}

# Wait for heartbeat file
wait_heartbeat() {
    local timeout=120
    local heartbeat_file="$PROJECT_ROOT/aipha_memory/operational/heartbeat_BTCUSDT.json"
    
    log "Waiting for heartbeat file..."
    elapsed=0
    while [ ! -f "$heartbeat_file" ] && [ $elapsed -lt $timeout ]; do
        sleep 2
        elapsed=$((elapsed + 2))
    done
    
    if [ ! -f "$heartbeat_file" ]; then
        error "Heartbeat file not found after ${timeout}s"
        return 1
    fi
    
    # Wait for valid price
    while [ $elapsed -lt $timeout ]; do
        price=$(cat "$heartbeat_file" | python3 -c "import sys,json; h=json.load(sys.stdin); print(h.get('last_aggtrade_gap_ms', 99999))" 2>/dev/null || echo "99999")
        if [ "$price" != "99999" ] && [ "$price" -lt 30000 ]; then
            log "Heartbeat valid (gap: ${price}ms)"
            return 0
        fi
        sleep 2
        elapsed=$((elapsed + 2))
    done
    
    error "Heartbeat timeout (>30s gap)"
    return 1
}

# Start watchdog with retry logic
start_watchdog() {
    local attempt=1
    
    while [ $attempt -le $MAX_RESTART_ATTEMPTS ]; do
        log "Starting watchdog (attempt $attempt/$MAX_RESTART_ATTEMPTS)..."
        
        # Try to start
        /home/vaclav/.pyenv/versions/3.11.9/bin/python3 "$WATCHDOG_SCRIPT" --daemon > "$WATCHDOG_LOG" 2>&1 &
        
        # Wait for initialization
        sleep 5
        
        # Verify it started
        if check_watchdog; then
            log "Watchdog started successfully (PID: $!)"
            return 0
        fi
        
        error "Failed to start watchdog"
        cat "$WATCHDOG_LOG" 2>/dev/null | tail -10
        attempt=$((attempt + 1))
        
        if [ $attempt -le $MAX_RESTART_ATTEMPTS ]; then
            warn "Retrying in ${RETRY_DELAY}s..."
            sleep $RETRY_DELAY
        fi
    done
    
    error "Failed after $MAX_RESTART_ATTEMPTS attempts"
    return 1
}

# Verify system state
verify_system() {
    log "Verifying system state..."
    
    # Check watchdog
    if ! check_watchdog; then
        error "Watchdog is not running"
        return 1
    fi
    
    # Check heartbeat price is valid (field name: last_price)
    local price=$(cat "$PROJECT_ROOT/aipha_memory/operational/heartbeat_BTCUSDT.json" 2>/dev/null | python3 -c "import sys,json; h=json.load(sys.stdin); print(h.get('last_price', 0))" 2>/dev/null || echo "0")
    
    if [ "$price" = "0" ]; then
        error "Price not found in heartbeat"
        return 1
    fi
    
    # Check if price is reasonable (BTC should be >10000 USD)
    # Use float comparison with bc or awk
    if echo "$price < 10000" | bc -l 2>/dev/null | grep -q "^1" || echo "$price > 1000000" | bc -l 2>/dev/null | grep -q "^1"; then
        warn "Unusual price detected: \$${price} (may indicate contamination)"
    fi
    
    log "System state verified:"
    log "  - Watchdog: running"
    log "  - Heartbeat: present"
    log "  - Price: \$$price"
    
    # Check UI server if available
    if check_ui_server; then
        log "  - UI Server: responding on port 5000"
    else
        warn "  - UI Server: not responding (may need manual start)"
    fi
    
    return 0
}

# Main recovery process
main() {
    log "=== CGAlpha Auto-Recovery Started ==="
    log "Project root: $PROJECT_ROOT"
    
    # Kill any existing watchdogs
    log "Cleaning up existing processes..."
    pkill -9 -f "harness_watchdog.py" 2>/dev/null || true
    sleep 1
    
    # Start watchdog
    if ! start_watchdog; then
        exit 1
    fi
    
    # Wait for heartbeat
    if ! wait_heartbeat; then
        exit 1
    fi
    
    # Verify system
    if verify_system; then
        log "=== Recovery Complete ==="
        echo ""
        log "System is operational. View logs:"
        echo "  tail -f $WATCHDOG_LOG"
        log "Or check status:"
        echo "  curl -s http://localhost:5000/api/v1/market/pulse"
        exit 0
    else
        error "=== Recovery Failed ==="
        exit 1
    fi
}

# Run main function
main "$@"
