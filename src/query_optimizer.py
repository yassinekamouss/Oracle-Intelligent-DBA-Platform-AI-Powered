import pandas as pd
import json
import os
from llm_engine import LLMEngine
from rag_setup import OracleRAG

class QueryOptimizer:
    def __init__(self):
        # Initialisation des briques précédentes
        self.engine = LLMEngine() # Module 3
        self.rag = OracleRAG()     # Module 2

    def analyze_slow_queries(self, metrics_file="data/performance_metrics.csv"):
        """Analyse toutes les requêtes lentes détectées dans le Module 1 """
        if not os.path.exists(metrics_file):
            return {"error": "Fichier de métriques introuvable. Relancez le Module 1."}

        # 1. Chargement des métriques de performance et des plans
        df_metrics = pd.read_csv(metrics_file)
        
        # Chargement des plans pour avoir l'opération
        plans_file = "data/execution_plans.csv"
        if os.path.exists(plans_file):
            df_plans = pd.read_csv(plans_file)
            # On cherche l'opération la plus coûteuse ou la première significative
            # Nettoyage et tri par COST descendant pour chaque SQL_ID
            if 'COST' in df_plans.columns:
                df_plans['COST'] = pd.to_numeric(df_plans['COST'], errors='coerce').fillna(0)
                df_plans = df_plans.sort_values(by=['SQL_ID', 'COST'], ascending=[True, False])
            
            # On garde une seule ligne par SQL_ID (celle avec le coût le plus élevé ou la première)
            df_plans_unique = df_plans.drop_duplicates(subset=['SQL_ID'])
            
            # Fusion
            df = pd.merge(df_metrics, df_plans_unique[['SQL_ID', 'OPERATION', 'OBJECT_NAME']], on='SQL_ID', how='left')
            df.rename(columns={'OPERATION': 'PLAN_OPERATION'}, inplace=True)
        else:
            df = df_metrics
            df['PLAN_OPERATION'] = 'UNKNOWN'
            df['OBJECT_NAME'] = ''

        # Gestion des valeurs manquantes après fusion
        df['PLAN_OPERATION'] = df['PLAN_OPERATION'].fillna('UNKNOWN')
        df['OBJECT_NAME'] = df['OBJECT_NAME'].fillna('')

        # On ne filtre plus, on prend les 3 dernières requêtes pour analyse (ou les 3 premières selon le tri)
        # Comme l'extraction trie par ELAPSED_TIME DESC, head(3) sont les plus lentes.
        # Le code précédent utilisait tail(3)... on garde tail(3) pour la cohérence demandée ("3 derniers")
        slow_queries = df.tail(3)
        
        results = []

        for _, row in slow_queries.iterrows():
            sql_text = row['SQL_TEXT']
            plan_op = row['PLAN_OPERATION']
            sql_id = row['SQL_ID']

            # 2. Récupération du contexte d'optimisation via le RAG (Module 2) [cite: 65]
            context_docs, _ = self.rag.retrieve_context(f"Comment optimiser une opération {plan_op} sur la table {row.get('OBJECT_NAME', '')}")
            context_text = "\n".join(context_docs)

            # 3. Génération de l'analyse via Gemini (Module 3) 
            print(f"⚡ Analyse de la requête {sql_id} en cours...")
            analysis_raw = self.engine.analyze_query(sql_text, plan_op, context_text)

            try:
                # Nettoyage et conversion en JSON
                clean_json = analysis_raw.replace("```json", "").replace("```", "").strip()
                analysis_data = json.loads(clean_json)
                analysis_data["sql_id"] = sql_id
                results.append(analysis_data)
            except Exception as e:
                print(f"⚠️ Erreur de parsing pour {sql_id}: {e}")
                results.append({"sql_id": sql_id, "raw_response": analysis_raw})

        # 4. Sauvegarde des analyses pour le Dashboard (Module 9)
        with open("data/query_analysis.json", "w", encoding='utf-8') as f:
            json.dump(results, f, indent=4, ensure_ascii=False)

        return results

if __name__ == "__main__":
    optimizer = QueryOptimizer()
    print("\n--- ANALYSE D'OPTIMISATION SQL ---")
    analyses = optimizer.analyze_slow_queries()
    
    # Affichage du résultat final
    print(json.dumps(analyses, indent=4, ensure_ascii=False))