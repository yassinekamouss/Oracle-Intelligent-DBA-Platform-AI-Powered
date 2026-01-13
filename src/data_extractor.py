import pandas as pd
import os
import random
from datetime import datetime, timedelta

class OracleSimulator:
    def __init__(self, output_dir='data'):
        self.output_dir = output_dir
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        print(f"🚀 Simulateur Oracle initialisé (Version Complète Module 1 & 6).")

    def generate_audit_logs(self):
        """Livrable : Logs d'audit (table AUD$) """
        data = []
        # 50 logs normaux 
        for i in range(50):
            hour = random.randint(8, 17)
            data.append({
                "TIMESTAMP": f"2026-01-13 {hour:02d}:{random.randint(0, 59):02d}:00",
                "USER": random.choice(["HR_APP", "FINANCE_USR", "REPORT_BOT"]),
                "ACTION": random.choice(["SELECT", "UPDATE", "INSERT"]),
                "OBJECT": random.choice(["EMPLOYEES", "ORDERS", "PRODUCTS"]),
                "STATUS": "SUCCESS", "OS_USER": "oracle_client", "TERMINAL": "T1"
            })
        # 20 logs suspects (Anomalies) [cite: 116, 240]
        for _ in range(20):
            data.append({
                "TIMESTAMP": "2026-01-13 03:15:00", 
                "USER": "SYS", "ACTION": "LOGON", "OBJECT": "DATABASE", 
                "STATUS": "SUCCESS", "OS_USER": "unknown", "TERMINAL": "Remote"
            })
        random.shuffle(data)
        pd.DataFrame(data).to_csv(f"{self.output_dir}/audit_logs.csv", index=False)
        print(f"✅ audit_logs.csv (AUD$) généré.")

    def generate_security_config(self):
        """Livrable : DBA_USERS, DBA_ROLES, DBA_SYS_PRIVS [cite: 50, 83]"""
        # 1. DBA_USERS
        users = [
            {"USERNAME": "SYS", "ACCOUNT_STATUS": "OPEN", "PROFILE": "DEFAULT", "LAST_LOGIN": "2026-01-13 08:00"},
            {"USERNAME": "HR_APP", "ACCOUNT_STATUS": "OPEN", "PROFILE": "APP_PROFILE", "LAST_LOGIN": "2026-01-13 09:30"},
            {"USERNAME": "GHOST_USER", "ACCOUNT_STATUS": "OPEN", "PROFILE": "DEFAULT", "LAST_LOGIN": "2026-01-12 23:45"}
        ]
        pd.DataFrame(users).to_csv(f"{self.output_dir}/dba_users.csv", index=False)

        # 2. DBA_ROLES (Nouveau) 
        roles = [
            {"ROLE": "DBA", "PASSWORD_REQUIRED": "NO", "AUTHENTICATION_TYPE": "NONE"},
            {"ROLE": "CONNECT", "PASSWORD_REQUIRED": "NO", "AUTHENTICATION_TYPE": "NONE"},
            {"ROLE": "RESOURCE", "PASSWORD_REQUIRED": "NO", "AUTHENTICATION_TYPE": "NONE"},
            {"ROLE": "APP_ADMIN", "PASSWORD_REQUIRED": "YES", "AUTHENTICATION_TYPE": "PASSWORD"}
        ]
        pd.DataFrame(roles).to_csv(f"{self.output_dir}/dba_roles.csv", index=False)

        # 3. DBA_SYS_PRIVS (Nouveau) 
        privs = [
            {"GRANTEE": "SYS", "PRIVILEGE": "ANY PRIVILEGE", "ADMIN_OPTION": "YES"},
            {"GRANTEE": "DBA", "PRIVILEGE": "CREATE TABLE", "ADMIN_OPTION": "YES"},
            {"GRANTEE": "GHOST_USER", "PRIVILEGE": "DROP ANY TABLE", "ADMIN_OPTION": "NO"}, # Risque sécurité
            {"GRANTEE": "HR_APP", "PRIVILEGE": "CREATE SESSION", "ADMIN_OPTION": "NO"}
        ]
        pd.DataFrame(privs).to_csv(f"{self.output_dir}/dba_sys_privs.csv", index=False)
        print("✅ Configurations sécurité générées (Users, Roles, Privs).")

    def generate_performance_metrics(self):
        """Livrable : V$SQLSTAT, V$SQL_PLAN, V$SYSTEM_EVENT [cite: 49, 51]"""
        # 1. V$SQLSTAT & V$SQL_PLAN
        perf = [
            {"SQL_ID": "sql_slow_001", "SQL_TEXT": "SELECT * FROM SALES...", "ELAPSED_TIME": 15000, "CPU_TIME": 14500, "EXECUTIONS": 1, "DISK_READS": 80000, "OPTIMIZER_COST": 4500, "PLAN_OPERATION": "TABLE ACCESS FULL", "OBJECT_NAME": "SALES"},
            {"SQL_ID": "sql_fast_002", "SQL_TEXT": "SELECT name FROM EMP...", "ELAPSED_TIME": 10, "CPU_TIME": 8, "EXECUTIONS": 100, "DISK_READS": 2, "OPTIMIZER_COST": 2, "PLAN_OPERATION": "INDEX UNIQUE SCAN", "OBJECT_NAME": "EMP_PK"}
        ]
        pd.DataFrame(perf).to_csv(f"{self.output_dir}/performance_metrics.csv", index=False)

        # 2. V$SYSTEM_EVENT (Nouveau) 
        events = [
            {"EVENT": "db file sequential read", "TOTAL_WAITS": 4500, "TIME_WAITED": 1200, "AVERAGE_WAIT": 0.26},
            {"EVENT": "log file sync", "TOTAL_WAITS": 1200, "TIME_WAITED": 850, "AVERAGE_WAIT": 0.70},
            {"EVENT": "buffer busy waits", "TOTAL_WAITS": 300, "TIME_WAITED": 150, "AVERAGE_WAIT": 0.50},
            {"EVENT": "direct path read", "TOTAL_WAITS": 800, "TIME_WAITED": 400, "AVERAGE_WAIT": 0.50}
        ]
        pd.DataFrame(events).to_csv(f"{self.output_dir}/system_events.csv", index=False)
        print("✅ Métriques de performance générées (SQL Stat + System Events).")

    def run_all(self):
        self.generate_audit_logs()
        self.generate_security_config()
        self.generate_performance_metrics()
        print("\nModule 1 : Toutes les données (simulées) sont normalisées en CSV.")

if __name__ == "__main__":
    simulator = OracleSimulator()
    simulator.run_all()