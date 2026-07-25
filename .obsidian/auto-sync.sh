#!/bin/bash
# auto-sync.sh — Sincroniza el vault con Git (4 repos)
# Uso: hermes ejecuta este script periódicamente desde cron

VAULT="$HOME/Documents/Obsidian-Vault"
cd "$VAULT" || exit 1

sync_vault() {
    local vault_name="$1"
    local remote="$2"
    local branch="$3"
    
    echo "⏳ Syncing ${vault_name} → ${remote}/${branch}"
    
    # Checkout vault branch
    git checkout "${branch}" 2>/dev/null || git checkout -b "${branch}" 2>/dev/null
    
    # Pull changes
    if git remote get-url "${remote}" &>/dev/null; then
        git pull --rebase "${remote}" "${branch}" 2>/dev/null || true
    fi
    
    # Stage + commit + push
    if ! git diff --quiet || ! git diff --cached --quiet; then
        git add -A
        git commit -m "auto-sync [${vault_name}]: $(date '+%Y-%m-%d %H:%M')" 2>/dev/null || true
        if git remote get-url "${remote}" &>/dev/null; then
            git push "${remote}" "${branch}" 2>/dev/null && echo "✓ ${vault_name} sincronizado" || echo "✗ ${vault_name} push falló"
        fi
    else
        echo "✓ ${vault_name}: sin cambios"
    fi
}

echo "═══ Obsidian vault auto-sync $(date) ═══"

# Sync PC vault → obsidian-pc repo
sync_vault "PC" "pc" "pc-vault"

# Sync CGAlpha vault → CGAlpha_0.0.1-Aipha_0.0.3 repo
sync_vault "CGAlpha" "origin" "obsidian-vault"

# Sync Hermes vault → obsidian-hermes repo
sync_vault "Hermes" "hermes" "hermes-vault"

# Sync Discord-Bot vault → lenguage-room repo
sync_vault "Discord-Bot" "discord" "discord-vault"

echo "═══ Sync completo ═══"