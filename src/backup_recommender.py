import json
import os
import pandas as pd
import re
from llm_engine import LLMEngine

class BackupRecommender:
    def __init__(self):
        # Initialisation du moteur IA 
        self.engine = LLMEngine() 
        # Chemins vers les fichiers de métriques générés par le Module 1
        self.metrics_path = "data/performance_metrics.csv"
        self.roles_path = "data/dba_roles.csv" 

    def fetch_real_metrics(self):
        """
        Récupère les métriques réelles (simulées) pour l'IA
        """
        metrics = {
            "taille": "Inconnue (Estimation 500GB)", 
            "volume_transactions": "Faible", 
            "criticite": "Standard"
        }
        
        # 1. Volume de transactions (via V$SQLSTAT simulé)
        if os.path.exists(self.metrics_path):
            try:
                df = pd.read_csv(self.metrics_path)
                total_execs = df['EXECUTIONS'].sum() if 'EXECUTIONS' in df.columns else 0
                metrics["volume_transactions"] = "Élevé" if total_execs > 1000 else "Moyen"
            except Exception:
                pass

        # 2. Criticité (via DBA_ROLES simulé)
        if os.path.exists(self.roles_path):
            try:
                df_sec = pd.read_csv(self.roles_path)
                roles_list = df_sec['ROLE'].values if 'ROLE' in df_sec.columns else []
                if "DBA" in roles_list:
                    metrics["criticite"] = "CRITIQUE (Rôle DBA détecté)"
            except Exception:
                pass
        
        return metrics

    def ask_user_questions(self):
        """
        Interface utilisateur : pose les 3 questions obligatoires
        """
        print("\n--- 🛠️  INTERFACE DE CONFIGURATION DE SAUVEGARDE ---")
        # Valeurs par défaut si l'utilisateur appuie juste sur Entrée
        rpo = input("1. RPO requis (ex: 15min, 24h) [Défaut: 24h] ? : ") or "24h"
        rto = input("2. RTO requis (ex: 1h, 4h) [Défaut: 4h] ? : ") or "4h"
        budget = input("3. Budget/Ressources (Bas, Moyen, Haut) [Défaut: Moyen] ? : ") or "Moyen"
        
        return {"rpo": rpo, "rto": rto, "budget": budget}

    def generate_full_plan(self):
        """
        Génère la stratégie JSON et le script RMAN via l'IA avec découpage strict.
        """
        db_metrics = self.fetch_real_metrics()
        user_reqs = self.ask_user_questions()
        
        # Construction du prompt
        template = self.engine.prompts['backup']['prompt']
        final_prompt = template.format(
            metrics=json.dumps(db_metrics, ensure_ascii=False),
            user_inputs=json.dumps(user_reqs, ensure_ascii=False)
        )
        
        print("\n🧠 L'IA analyse les contraintes et génère la stratégie...")
        full_response = self.engine.generate(final_prompt)
        
        strategy_json = {}
        rman_script = ""

        # --- LOGIQUE D'EXTRACTION CORRIGÉE ---
        
        # Cas 1 (Idéal) : L'IA a respecté les marqueurs demandés dans le prompt
        if "---JSON---" in full_response and "---RMAN---" in full_response:
            try:
                # On coupe tout ce qui est entre ---JSON--- et ---RMAN---
                parts = full_response.split("---RMAN---")
                json_part = parts[0].split("---JSON---")[1].strip()
                rman_script = parts[1].strip()
                
                # Parsing JSON
                strategy_json = json.loads(json_part)
            except Exception as e:
                print(f"⚠️ Erreur parsing (Mode Marqueurs) : {e}")
                # Si échec, on laisse le Cas 2 essayer
        
        # Cas 2 (Fallback Regex) : Si le Cas 1 a échoué ou si les marqueurs sont absents
        if not strategy_json:
            # Cette Regex cherche un bloc {...} mais s'arrête AVANT le mot 'RUN' ou '---RMAN'
            # (?=...) est un "Lookahead" : vérifie la présence sans consommer les caractères
            json_match = re.search(r'\{.*?\}(?=\s*(?:RUN|---|Script))', full_response, re.DOTALL | re.IGNORECASE)
            
            if json_match:
                try:
                    strategy_json = json.loads(json_match.group(0))
                except:
                    # Dernier recours : Regex simple non-greedy
                    try:
                        simple_match = re.search(r'\{.*\}', full_response.split("RUN")[0], re.DOTALL)
                        if simple_match:
                            strategy_json = json.loads(simple_match.group(0))
                    except:
                        strategy_json = {"error": "Format JSON invalide", "raw_sample": full_response[:100]}
            else:
                 # Si vraiment aucun JSON n'est trouvé, on tente de parser le tout début
                 pass

        # Extraction Script RMAN (si pas déjà trouvé par le Cas 1)
        if not rman_script:
            rman_match = re.search(r'RUN\s*\{.*\}', full_response, re.DOTALL | re.IGNORECASE)
            if rman_match:
                rman_script = rman_match.group(0)
            else:
                # Fallback : on prend tout ce qui contient BACKUP
                lines = [l for l in full_response.split('\n') if "BACKUP" in l or "CONFIGURE" in l or "DELETE" in l]
                if lines:
                    rman_script = "RUN {\n" + "\n".join(lines) + "\n}"
                else:
                    rman_script = "/* Erreur : Aucun script RMAN valide détecté */"

        return strategy_json, rman_script

if __name__ == "__main__":
    recommender = BackupRecommender()
    
    # 1. Exécution du processus
    json_res, rman_res = recommender.generate_full_plan()
    
    # 2. Sauvegarde des fichiers sur le disque (C'est ce qui manquait !)
    output_dir = "data"
    os.makedirs(output_dir, exist_ok=True) # Crée le dossier s'il n'existe pas

    # Sauvegarde du JSON
    json_path = os.path.join(output_dir, "backup_plan.json")
    with open(json_path, "w", encoding='utf-8') as f:
        json.dump(json_res, f, indent=4, ensure_ascii=False)
    
    # Sauvegarde du script RMAN
    rman_path = os.path.join(output_dir, "backup_script.rman")
    with open(rman_path, "w", encoding='utf-8') as f:
        f.write(rman_res)

    # 3. Affichage de confirmation et des résultats
    print(f"\n✅ Fichiers générés avec succès dans '{output_dir}/' :")
    print(f"   - {json_path}")
    print(f"   - {rman_path}")

    print("\n" + "="*40)
    print(" 📄 CONTENU JSON (Aperçu)")
    print("="*40)
    print(json.dumps(json_res, indent=4, ensure_ascii=False))
    
    print("\n" + "="*40)
    print(" 💾 SCRIPT RMAN (Aperçu)")
    print("="*40)
    print(rman_res)