import pandas as pd
import json
import os
from llm_engine import LLMEngine
from rag_setup import OracleRAG

class AnomalyDetector:
    def __init__(self):
        self.engine = LLMEngine() 
        self.rag = OracleRAG()     

    def analyze_logs(self, logs_file="data/audit_logs.csv"):
        """Analyse les logs d'audit Oracle """
        if not os.path.exists(logs_file):
            return {"error": "Fichier de logs introuvable."}

        # 1. Chargement des logs
        df = pd.read_csv(logs_file)
        # Analyse des 20 derniers logs (échantillon pour l'IA)
        logs_text = df.tail(20).to_string(index=False)
        
        # 2. Récupération du contexte RAG 
        context_docs, _ = self.rag.retrieve_context("patterns injection SQL, escalade privilèges, accès hors heures")
        context_text = "\n".join(context_docs)
        
        # 3. Analyse par Gemini 
        print("🕵️ Analyse de cybersécurité en cours...")
        prompt_template = self.engine.prompts['anomaly']['prompt']
        analysis_raw = self.engine.generate(
            user_message=prompt_template.format(logs=logs_text, context=context_text)
        )
        
        try:
            # Nettoyage et conversion JSON [cite: 127-129]
            clean_json = analysis_raw.replace("```json", "").replace("```", "").strip()
            results = json.loads(clean_json)
            
            with open("data/detected_anomalies.json", "w", encoding='utf-8') as f:
                json.dump(results, f, indent=4, ensure_ascii=False)
                
            return results
        except Exception as e:
            # Fallback robuste : même si le LLM ne renvoie pas un JSON parfait,
            # on enregistre quand même un fichier minimal pour ne pas bloquer le reste du projet.
            print(f"⚠️ Erreur de parsing JSON pour la réponse du LLM : {e}")
            fallback = [{
                "classification": "INCONNU",
                "justification": analysis_raw,
                "severity": "INCONNU"
            }]

            with open("data/detected_anomalies.json", "w", encoding='utf-8') as f:
                json.dump(fallback, f, indent=4, ensure_ascii=False)

            return fallback

    def validate_chatbot(self, question):
        """Réponse aux questions d'intrusion (Livrable Validation) """
        try:
            with open("data/detected_anomalies.json", "r", encoding='utf-8') as f:
                data = json.load(f)
            
            # On cherche s'il y a des anomalies critiques ou suspectes
            alerts = [a for a in data if a.get('classification') in ['CRITIQUE', 'SUSPECT']]
            if alerts:
                return f"Oui, j'ai détecté {len(alerts)} anomalie(s). Exemple : {alerts[0]['justification']}"
            return "Aucune intrusion détectée dans les logs récents."
        except FileNotFoundError:
            return "Veuillez d'abord lancer l'analyse des logs."

if __name__ == "__main__":
    # Lancer la détection sur les logs réels déjà extraits dans data/audit_logs.csv
    detector = AnomalyDetector()
    print("\n--- DÉTECTION D'ANOMALIES ---")
    results = detector.analyze_logs()
    
    question = "Y a-t-il une tentative d'intrusion ?"
    reponse = detector.validate_chatbot(question)
    print(f"\n🤖 Question Chatbot : {question}")
    print(f"🤖 Réponse IA : {reponse}")