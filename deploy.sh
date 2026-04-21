#!/bin/bash

# 🚀 Quick Deploy Script
# Usage: ./deploy.sh [environment]
# Example: ./deploy.sh production

set -e

ENVIRONMENT=${1:-development}
PROJECT_DIR=$(pwd)

echo ""
echo "🚀 ============================================="
echo "🚀 Déploiement: $ENVIRONMENT"
echo "🚀 ============================================="
echo ""

# Vérifications
if ! command -v docker &> /dev/null; then
    echo "❌ Docker n'est pas installé"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose n'est pas installé"
    exit 1
fi

# Charger les variables d'environnement
if [ "$ENVIRONMENT" = "production" ]; then
    if [ ! -f ".env.production" ]; then
        echo "❌ .env.production n'existe pas!"
        echo "   Créer .env.production et configurer les secrets"
        exit 1
    fi
    ENV_FILE=".env.production"
else
    if [ ! -f "backend/.env" ]; then
        echo "❌ backend/.env n'existe pas!"
        echo "   Créer backend/.env"
        exit 1
    fi
    ENV_FILE="backend/.env"
fi

echo "📋 Configuration: $ENV_FILE"

# Arrêter les services existants
echo "⏹️ Arrêt des services existants..."
docker-compose down --remove-orphans 2>/dev/null || true

# Construire les images
echo "🔨 Construction des images Docker..."
docker-compose build

# Lancer les services
echo "🚀 Lancement des services..."
docker-compose up -d

# Attendre le démarrage
echo "⏳ Attente du démarrage des services..."
sleep 5

# Vérifier la santé
echo ""
echo "🏥 Vérification de la santé..."
docker-compose ps

echo ""
echo "✅ ============================================="
echo "✅ Déploiement complété!"
echo "✅ ============================================="
echo ""

# Afficher les URLs
echo "📍 Services:"
if [ "$ENVIRONMENT" = "production" ]; then
    echo "   Frontend: https://ton-domaine.com"
    echo "   Backend API: https://ton-domaine.com/api"
else
    echo "   Frontend: http://localhost:3000"
    echo "   Backend API: http://localhost:8000"
    echo "   API Docs: http://localhost:8000/docs"
fi

echo ""
echo "Login: admin@gmail.com / admin123"
echo ""

# Afficher les logs (optionnel)
read -p "Afficher les logs? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    docker-compose logs -f
fi
