# 🚀 Guide de Lancement Rapide (Windows) - AI Sales Assistant

Ce guide explique comment lancer l'environnement de développement Docker sur Windows.

## 1️⃣ Prérequis

1.  **Docker Desktop** : Doit être installé et **démarré** (vous devez voir la baleine dans la barre des tâches).
2.  **Git Bash** : Recommandé pour utiliser les scripts de gestion. Il est généralement installé avec [Git for Windows](https://git-scm.com/download/win).

## 2️⃣ Premier Lancement

Ouvrez une fenêtre **Git Bash** à la racine du projet (là où se trouve `manage.sh`) et exécutez :

```bash
# Démarrer toute l'infrastructure (Base de données + Outils)
./manage.sh start-tools
```

> **Note :** Si la commande échoue, vérifiez que Docker Desktop est bien lancé.

## 3️⃣ Vérification

Une fois le démarrage terminé, vérifiez que tout fonctionne :

```bash
./manage.sh test
```
Vous devriez voir :
- ✅ PostgreSQL : Connecté
- ✅ Redis : Connecté

## 4️⃣ Accès aux Interfaces

Ouvrez votre navigateur préféré :

| Outil | URL | Login | Mot de passe |
|-------|-----|-------|--------------|
| **pgAdmin** (SQL) | http://localhost:5050 | `admin@example.com` | `admin123` |
| **Redis Commander** | http://localhost:8081 | `admin` | `admin123` |

## 5️⃣ Commandes Utiles au Quotidien

Dans Git Bash :

- **Tout arrêter** : `./manage.sh stop`
- **Voir les logs** : `./manage.sh logs`
- **Redémarrer** : `./manage.sh restart`
- **Voir l'état** : `./manage.sh status`

---
*Pour plus de détails techniques, consultez le fichier `README-DOCKER.md` complet.*
