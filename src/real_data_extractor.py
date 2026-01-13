import oracledb
import pandas as pd
import os
import sys
import datetime

# =============================================================================
# CONFIGURATION DE LA CONNEXION (Docker / Local)
# =============================================================================
DB_CONFIG = {
    "username": "SYS",  
    "password": "Kamouss@123",
    "host": "localhost",
    "port": "1521",
    "service_name": "FREEPDB1"
}
OUTPUT_DIR = 'data'

class OracleDataExtractor:
    def __init__(self):
        """
        Module 1 : Extraction de Données & Infrastructure.
        Utilise le driver moderne 'oracledb' (Thin mode) - Pas d'Instant Client requis.
        
        Documentation pour connexion distante [Livrable 53]:
        1. Changer 'host' par l'IP du serveur cible.
        2. Changer 'service_name' par le SID/Service de la base.
        3. Vérifier que le port 1521 est accessible.
        """
        self.output_dir = OUTPUT_DIR
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            print(f"📂 Dossier '{self.output_dir}' prêt.")
        
        print(f"🚀 Démarrage Module 1 avec python-oracledb (Mode Thin)")
        self.conn = self._connect()

    def _connect(self):
        """Etablit la connexion en mode SYSDBA."""
        try:
            dsn = oracledb.makedsn(DB_CONFIG["host"], DB_CONFIG["port"], 
                                service_name=DB_CONFIG["service_name"])
            
            # Connexion avec SYSDBA nécessite parfois SYS au lieu de SYSTEM
            conn = oracledb.connect(
                user="SYS",  # Changez SYSTEM par SYS
                password=DB_CONFIG["password"],
                dsn=dsn,
                mode=oracledb.AUTH_MODE_SYSDBA
            )
            print(f"✅ Connexion SYSDBA réussie")
            return conn
        except oracledb.Error as e:
            error_obj, = e.args
            print(f"❌ Erreur : {error_obj.message}")
            sys.exit(1)
    def extract_query_to_csv(self, query, filename, description):
        """Exécute SQL et sauvegarde en CSV normalisé."""
        print(f"   ⏳ Extraction : {description}...")
        try:
            # Pandas supporte oracledb via SQLAlchemy ou connection directe
            # Ici on utilise la méthode directe simple
            df = pd.read_sql(query, self.conn)
            
            # Normalisation [Livrable 52] : Colonnes en majuscules
            df.columns = [col.upper() for col in df.columns]
            
            path = os.path.join(self.output_dir, filename)
            df.to_csv(path, index=False)
            print(f"      ✅ {filename} généré ({len(df)} lignes).")
        except Exception as e:
            print(f"      ⚠️ Erreur sur {filename}: {e}")

    def run_full_extraction(self):
        """Exécute les extractions des livrables demandés."""
        
        # 1. Logs d'audit (AUD$) [Livrable 48]
        # On utilise DBA_AUDIT_TRAIL pour lire AUD$
        q_audit = """
            SELECT 
                OS_USERNAME, USERNAME, USERHOST, TERMINAL, TIMESTAMP, 
                OWNER, OBJ_NAME, ACTION_NAME, RETURNCODE, SQL_TEXT
            FROM DBA_AUDIT_TRAIL
            WHERE TIMESTAMP > SYSDATE - 30
            ORDER BY TIMESTAMP DESC
            FETCH FIRST 2000 ROWS ONLY
        """
        self.extract_query_to_csv(q_audit, "audit_logs.csv", "Logs d'audit")

        # 2. Plans d'exécution (V$SQL_PLAN) 
        q_plans = """
            SELECT 
                SQL_ID, PLAN_HASH_VALUE, ID, OPERATION, OPTIONS, 
                OBJECT_NAME, OPTIMIZER, COST, CPU_COST, IO_COST, TIME
            FROM V$SQL_PLAN
            WHERE ROWNUM <= 2000
        """
        self.extract_query_to_csv(q_plans, "execution_plans.csv", "Plans d'exécution")

        # 3. Configurations de sécurité 
        # A. Users
        self.extract_query_to_csv(
            "SELECT USERNAME, ACCOUNT_STATUS, LOCK_DATE, EXPIRY_DATE, PROFILE, LAST_LOGIN FROM DBA_USERS",
            "dba_users.csv", "Config Users"
        )
        # B. Roles
        self.extract_query_to_csv(
            "SELECT ROLE, PASSWORD_REQUIRED, AUTHENTICATION_TYPE FROM DBA_ROLES",
            "dba_roles.csv", "Config Roles"
        )
        # C. Privilèges Système
        self.extract_query_to_csv(
            "SELECT GRANTEE, PRIVILEGE, ADMIN_OPTION FROM DBA_SYS_PRIVS",
            "dba_sys_privs.csv", "Privilèges Système"
        )

        # 4. Métriques de performance 
        # A. SQL Stats
        q_sqlstat = """
            SELECT 
                SQL_ID, 
                SUBSTR(SQL_TEXT, 1, 200) AS SQL_TEXT,
                ELAPSED_TIME, 
                CPU_TIME, 
                EXECUTIONS, 
                DISK_READS, 
                BUFFER_GETS,
                OPTIMIZER_COST
            FROM V$SQL
            WHERE EXECUTIONS > 0
            ORDER BY ELAPSED_TIME DESC
            FETCH FIRST 500 ROWS ONLY
        """
        self.extract_query_to_csv(q_sqlstat, "performance_metrics.csv", "Stats SQL")

        # B. System Events
        q_sysevent = """
            SELECT EVENT, TOTAL_WAITS, TIME_WAITED, AVERAGE_WAIT 
            FROM V$SYSTEM_EVENT 
            ORDER BY TIME_WAITED DESC
        """
        self.extract_query_to_csv(q_sysevent, "system_events.csv", "Events Système")

        print(f"\n✅ Extraction terminée. Fichiers disponibles dans '{self.output_dir}/'")
        self.conn.close()

if __name__ == "__main__":
    extractor = OracleDataExtractor()
    extractor.run_full_extraction()