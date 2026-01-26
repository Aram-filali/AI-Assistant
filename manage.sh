#!/bin/bash

# ------------------------------------------------------------------------------
# 🛠️ AI SALES ASSISTANT - INFRASTRUCTURE MANAGER
# ------------------------------------------------------------------------------
# Script de gestion Docker pour PostgreSQL et Redis
# Compatible : Linux, macOS, Windows (Git Bash / WSL)

# --- COULEURS & STYLES ---
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
BOLD='\033[1m'
NC='\033[0m' # No Color

# --- CONFIGURATION ---
COMPOSE_CMD="docker-compose"
if ! command -v docker-compose &> /dev/null; then
    if command -v docker &> /dev/null && docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    else
        echo -e "${RED}❌ Erreur : docker-compose ou docker compose n'est pas installé.${NC}"
        exit 1
    fi
fi

# --- FONCTIONS UTILITAIRES ---
print_header() {
    echo -e "\n${BLUE}${BOLD}🔧 $1${NC}"
    echo -e "${BLUE}---------------------------------------------${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ️  $1${NC}"
}

confirm_action() {
    read -p "❓ $1 (y/N) " response
    case "$response" in
        [yY][eE][sS]|[yY]) 
            return 0 
            ;;
        *)
            return 1
            ;;
    esac
}

# --- COMMANDES ---

cmd_start() {
    print_header "Démarrage Infrastructure (Core)"
    $COMPOSE_CMD up -d postgres redis
    print_success "Services PostgreSQL et Redis démarrés"
}

cmd_start_tools() {
    print_header "Démarrage Infrastructure Complète (avec Outils)"
    $COMPOSE_CMD --profile tools up -d
    print_success "Tous les services (y compris pgAdmin & Redis Commander) sont démarrés"
    print_info "pgAdmin : http://localhost:5050"
    print_info "Redis Commander : http://localhost:8081"
}

cmd_stop() {
    print_header "Arrêt des Services"
    $COMPOSE_CMD --profile tools stop
    print_success "Services arrêtés (conteneurs préservés)"
}

cmd_restart() {
    print_header "Redémarrage"
    cmd_stop
    sleep 2
    cmd_start_tools
}

cmd_logs() {
    print_header "Logs en temps réel (Ctrl+C pour quitter)"
    $COMPOSE_CMD --profile tools logs -f --tail=50
}

cmd_status() {
    print_header "Statut des Services"
    $COMPOSE_CMD --profile tools ps
}

cmd_test() {
    print_header "Test des Connexions"
    
    # Test Postgres
    if docker exec ai-sales-postgres pg_isready -U ai_sales_user -d ai_sales_db > /dev/null 2>&1; then
        print_success "PostgreSQL : Connecté (Port 5432)"
    else
        print_error "PostgreSQL : Échec connexion"
    fi

    # Test Redis
    if docker exec ai-sales-redis redis-cli -a redis_password_2024 ping | grep -q "PONG"; then
        print_success "Redis : Connecté (Port 6379)"
    else
        print_error "Redis : Échec connexion"
    fi
}

cmd_stats() {
    print_header "Statistiques Infrastructure"
    docker stats ai-sales-postgres ai-sales-redis --no-stream --format "table {{.Name}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

cmd_psql() {
    print_header "Shell PostgreSQL"
    print_info "Mot de passe : ai_sales_2024_secure"
    docker exec -it ai-sales-postgres psql -U ai_sales_user -d ai_sales_db
}

cmd_redis() {
    print_header "Shell Redis"
    docker exec -it ai-sales-redis redis-cli -a redis_password_2024
}

cmd_backup() {
    print_header "Sauvegarde Base de Données"
    BACKUP_FILE="backups/backup_$(date +%Y%m%d_%H%M%S).sql"
    mkdir -p backups
    
    if docker exec ai-sales-postgres pg_dump -U ai_sales_user ai_sales_db > "$BACKUP_FILE"; then
        print_success "Backup créé : $BACKUP_FILE"
    else
        print_error "Erreur lors du backup"
    fi
}

cmd_restore() {
    if [ -z "$1" ]; then
        print_error "Merci de spécifier le fichier de backup à restaurer"
        echo "Usage: ./manage.sh restore backups/mon_backup.sql"
        exit 1
    fi
    
    FILE=$1
    if [ ! -f "$FILE" ]; then
        print_error "Fichier introuvable : $FILE"
        exit 1
    fi

    if confirm_action "Attention, cela va écraser la base de données actuelle. Continuer ?"; then
        print_header "Restauration en cours..."
        cat "$FILE" | docker exec -i ai-sales-postgres psql -U ai_sales_user ai_sales_db
        print_success "Restauration terminée"
    else
        echo "Annulé."
    fi
}

cmd_reset() {
    print_header "⚠️  RESET COMPLET"
    if confirm_action "Voulez-vous vraiment TOUT supprimer (volumes, données) ?"; then
        $COMPOSE_CMD down -v
        print_success "Infrastructure détruite et nettoyée"
    else
        echo "Annulé."
    fi
}

cmd_help() {
    echo -e "${BLUE}${BOLD}🤖 AI Sales - Docker Manager${NC}"
    echo -e "Usage: ./manage.sh [commande]"
    echo ""
    echo -e "${YELLOW}Commandes Principales :${NC}"
    echo -e "  ${GREEN}start${NC}        : Démarrer Postgres + Redis"
    echo -e "  ${GREEN}start-tools${NC}  : Démarrer tout + pgAdmin + Redis Commander"
    echo -e "  ${GREEN}stop${NC}         : Arrêter tous les services"
    echo -e "  ${GREEN}restart${NC}      : Redémarrer l'infra"
    echo -e "  ${GREEN}reset${NC}        : ⚠️  Reset complet (supprime les données)"
    echo ""
    echo -e "${YELLOW}Outils & Debug :${NC}"
    echo -e "  ${GREEN}status${NC}       : Voir l'état des conteneurs"
    echo -e "  ${GREEN}logs${NC}         : Voir les logs (live)"
    echo -e "  ${GREEN}test${NC}         : Tester la connectivité"
    echo -e "  ${GREEN}stats${NC}        : Voir l'utilisation CPU/RAM"
    echo ""
    echo -e "${YELLOW}Accès CLI :${NC}"
    echo -e "  ${GREEN}psql${NC}         : Connexion au shell PostgreSQL"
    echo -e "  ${GREEN}redis${NC}        : Connexion au shell Redis"
    echo ""
    echo -e "${YELLOW}Maintenance :${NC}"
    echo -e "  ${GREEN}backup${NC}       : Créer un backup SQL"
    echo -e "  ${GREEN}restore <f>${NC}  : Restaurer un backup SQL"
    echo ""
}

# --- ROUTAGE COMMANDES ---
case "$1" in
    start) cmd_start ;;
    start-tools) cmd_start_tools ;;
    stop) cmd_stop ;;
    restart) cmd_restart ;;
    logs) cmd_logs ;;
    status) cmd_status ;;
    test) cmd_test ;;
    stats) cmd_stats ;;
    psql) cmd_psql ;;
    redis) cmd_redis ;;
    backup) cmd_backup ;;
    restore) cmd_restore "$2" ;;
    reset) cmd_reset ;;
    *) cmd_help ;;
esac
