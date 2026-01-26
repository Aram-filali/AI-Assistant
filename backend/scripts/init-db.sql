-- Initialisation de la base de données AI Sales Assistant

-- 1. Configuration de base
SET timezone = 'UTC';

-- 2. Activation des extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";      -- Pour les UUIDs
CREATE EXTENSION IF NOT EXISTS "pg_trgm";        -- Pour la recherche floue
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements"; -- Pour le monitoring
CREATE EXTENSION IF NOT EXISTS "btree_gin";      -- Pour l'indexation avancée

-- 3. Création du schéma dédié
CREATE SCHEMA IF NOT EXISTS app;

-- 4. Fonction pour gérer automatiquement updated_at
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- 5. Création d'un rôle readonly pour l'analytique (si besoin futur)
DO $$
BEGIN
  IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'analytics_readonly') THEN
    CREATE ROLE analytics_readonly;
    GRANT USAGE ON SCHEMA app TO analytics_readonly;
    GRANT SELECT ON ALL TABLES IN SCHEMA app TO analytics_readonly;
    ALTER DEFAULT PRIVILEGES IN SCHEMA app GRANT SELECT ON TABLES TO analytics_readonly;
  END IF;
END
$$;

-- Message de succès
DO $$
BEGIN
    RAISE NOTICE '✅ Base de données initialisée avec succès :';
    RAISE NOTICE '   - Extensions installées';
    RAISE NOTICE '   - Schéma "app" créé';
    RAISE NOTICE '   - Timezone UTC configurée';
    RAISE NOTICE '   - Fonction update_updated_at prête';
END
$$;
