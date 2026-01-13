import pandas as pd
import json
import os
from llm_engine import LLMEngine
from rag_setup import OracleRAG

class SecurityAuditor:
    def __init__(self):
        """Initialisation des moteurs IA et RAG"""
        self.engine = LLMEngine() 
        self.rag = OracleRAG()     

    def run_audit(self):
        """
        Exécute l'audit de sécurité complet en agrégeant les fichiers CSV
        Livrables : Analyse des utilisateurs, rôles et privilèges
        """
        # Liste des fichiers extraits par le Module 1
        security_files = [
            "data/dba_users.csv", 
            "data/dba_roles.csv", 
            "data/dba_sys_privs.csv"
        ]
        
        all_config_text = ""
        found_files = 0

        # 1. Chargement et agrégation des données de configuration
        for file_path in security_files:
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                # Ajout d'un en-tête pour aider le LLM à distinguer les tables
                all_config_text += f"\n--- TABLE ORACLE : {os.path.basename(file_path).upper()} ---\n"
                all_config_text += df.to_string(index=False) + "\n"
                found_files += 1
        
        if found_files == 0:
            return {"error": "Aucun fichier de configuration (users, roles, privs) trouvé dans data/."}

        # 2. Récupération du contexte via le RAG (Top-5 docs)
        # Recherche basée sur les thèmes du Module 4
        context_docs, _ = self.rag.retrieve_context("privilèges excessifs, sécurité des mots de passe, audit rôles")
        context_text = "\n".join(context_docs)
        
        # 3. Génération du rapport via LLM
        print(f"🕵️ Analyse de {found_files} fichiers de sécurité en cours...")
        report_raw = self.engine.assess_security(all_config_text, context_text)
        
        # 4. Conversion et validation du rapport JSON
        try:
            # Nettoyage pour garantir un JSON valide
            clean_json = report_raw.replace("```json", "").replace("```", "").strip()
            report_data = json.loads(clean_json)
            
            # Sauvegarde pour le Dashboard final (Module 9)
            os.makedirs("data", exist_ok=True)
            with open("data/last_audit.json", "w", encoding='utf-8') as f:
                json.dump(report_data, f, indent=4, ensure_ascii=False)
                
            return report_data
        except Exception as e:
            print(f"⚠️ Erreur de parsing JSON. Retour du texte brut. Erreur: {e}")
            return {"raw_report": report_raw}

if __name__ == "__main__":
    auditor = SecurityAuditor()
    print("\n🛡️  LANCEMENT DE L'AUDIT DE SÉCURITÉ AUTOMATISÉ")
    
    # Exécution de l'audit multi-fichiers
    rapport_json = auditor.run_audit()
    
    # Affichage structuré du résultat
    print(json.dumps(rapport_json, indent=4, ensure_ascii=False))