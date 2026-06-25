#!/bin/bash
# =============================================================================
# PKB Neuroassistant — Entry point
#
# Восстанавливает права на выполнение и запускает deploy.sh.
# Использование: ./run.sh [deploy|reset]
# =============================================================================

cd "$(dirname "$0")"

# Восстановить права (git может сбросить +x)
chmod +x deploy.sh deploy_reset.sh
chmod +x backend/diagnostics/*.sh backend/diagnostics/*.py 2>/dev/null || true

# Запустить deploy.sh (по умолчанию) или deploy_reset.sh
case "${1:-deploy}" in
    deploy)
        exec ./deploy.sh
        ;;
    reset)
        exec ./deploy_reset.sh
        ;;
    *)
        echo "Usage: $0 {deploy|reset}"
        exit 1
        ;;
esac
