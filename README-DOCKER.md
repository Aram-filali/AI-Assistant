# 🐳 Guide Docker (Windows) : AI Sales Assistant

Ce guide explique comment installer et gérer l'infrastructure locale du projet (PostgreSQL, Redis et outils) sur **Windows** avec Docker.

## 📋 Prérequis

- **Docker Desktop** pour Windows (installé et démarré).
- **Git Bash** (recommandé) ou un terminal supportant les scripts Bash (WSL).

---

## 🚀 Installation Rapide

1.  **Ouvrir un terminal** :
    Lancez **Git Bash** et naviguez vers le dossier du projet.

2.  **Démarrer l'infrastructure** :
    ```bash
    ./manage.sh start-tools
    ```
    *(Cela va télécharger les images, créer les volumes et lancer tous les services)*

3.  **Vérifier que tout fonctionne** :
    ```bash
    ./manage.sh test
    ```
    *(Devrait afficher ✅ CONNECTÉ pour Postgres et Redis)*

---

## 🛠️ Accès aux Interfaces

Une fois la commande `start-tools` lancée, accédez aux outils via votre navigateur :

| Service | URL | Identifiant | Mot de passe |
|---------|-----|-------------|--------------|
| **pgAdmin 4** (SQL) | [http://localhost:5050](http://localhost:5050) | `admin@example.com` | `admin123` |
| **Redis Commander** | [http://localhost:8081](http://localhost:8081) | `admin` | `admin123` |

> **Note :** Dans pgAdmin, le serveur "AI Sales Local" devrait être pré-configuré. Si on vous demande le mot de passe de la DB, c'est `ai_sales_2024_secure`.

---

## 💻 Utilisation Quotidienne

Le script `manage.sh` simplifie toutes les opérations. Utilisez **Git Bash** pour l'exécuter.

| Action | Commande | Description |
|--------|----------|-------------|
| **Démarrer** | `./manage.sh start` | Lance uniquement Postgres et Redis (rapide). |
| **Arrêter** | `./manage.sh stop` | Arrête tous les conteneurs proprement. |
| **Logs** | `./manage.sh logs` | Affiche les logs en temps réel. |
| **Status** | `./manage.sh status` | Voir si les services sont UP. |

### 🔧 Accès Avancé (CLI)

Pour accéder directement aux terminaux des bases de données :

- **PostgreSQL CLI** :
  ```bash
  ./manage.sh psql
  # Vous êtes connecté à la DB "ai_sales_db". Tapez \l pour lister les bases, \dt pour les tables.
  ```

- **Redis CLI** :
  ```bash
  ./manage.sh redis
  # Tapez PING (réponse PONG) ou KEYS * pour voir les clés.
  ```

### 💾 Backup & Restauration

- **Créer un backup** :
  ```bash
  ./manage.sh backup
  # Crée un fichier .sql dans le dossier backups/
  ```

- **Restaurer un backup** :
  ```bash
  ./manage.sh restore backups/backup_2024xxxx.sql
  ```

- **Reset Total** (Attention !) :
  ```bash
  ./manage.sh reset
  # Supprime TOUT (volumes compris) et repart à zéro.
  ```

---

## ⚙️ Configuration Technique

### PostgreSQL 16
- **Port** : 5432
- **User** : `ai_sales_user`
- **Password** : `ai_sales_2024_secure`
- **Database** : `ai_sales_db`
- **Volumes** : Persistants dans `ai_sales_postgres_data`
- **Extensions** : `uuid-ossp`, `pg_trgm` activées.

### Redis 7
- **Port** : 6379
- **Password** : `redis_password_2024`
- **Persistence** : AOF + RDB.

---

## ❓ Troubleshooting (Windows)

**"docker-compose: command not found" ?**
- Docker Desktop n'est peut-être pas installé ou pas dans le PATH.
- Essayez de redémarrer Git Bash.

**Le script ne se lance pas (`permission denied`) ?**
- Sur Windows, les permissions d'exécution sont gérées différemment, mais si cela arrive, vous pouvez essayer : `bash manage.sh <commande>` au lieu de `./manage.sh`.

**Erreur "Ports are not available" ?**
- Vérifiez que vous n'avez pas déjà un PostgreSQL ou Redis installé localement sur Windows qui tourne en arrière-plan.
- Arrêtez le service Windows (Services.msc -> PostgreSQL / Redis -> Stop) ou changez les ports dans `docker-compose.yml`.
