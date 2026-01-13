import os
import yaml
import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

class LLMEngine:
    def __init__(self):
        """Initialisation de Gemini engine"""
        self.api_key = os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("❌ Clé API Gemini manquante dans le fichier .env (GEMINI_API_KEY)")
        
        genai.configure(api_key=self.api_key)
        self.model_name = "gemini-2.5-flash"
        
        # Chargement du fichier prompts.yaml
        try:
            with open("data/prompts.yaml", "r", encoding='utf-8') as f:
                self.prompts = yaml.safe_load(f)
            print(f"✅ LLMEngine initialisé avec {self.model_name}.")
        except FileNotFoundError:
            print("❌ Erreur : Fichier data/prompts.yaml introuvable.")
            self.prompts = {}

    def generate(self, user_message, system_context=""):
        """Méthode de base pour l'appel au LLM via Gemini API"""
        try:
            system_role = self.prompts.get('system_role', 'You are a helpful assistant.')
            # Combine system context if provided
            if system_context:
                system_instruction = f"{system_role}\n\nCONTEXTE :\n{system_context}"
            else:
                system_instruction = system_role

            model = genai.GenerativeModel(self.model_name, system_instruction=system_instruction)
            
            response = model.generate_content(user_message)
            return response.text

        except Exception as e:
            return f"❌ Erreur Gemini : {str(e)}"

    def analyze_query(self, sql, plan, context):
        """Module 5 : Optimisation de requêtes"""
        template = self.prompts['optimization']['prompt']
        prompt_final = template.format(query=sql, plan=plan, context=context)
        return self.generate(prompt_final)

    def assess_security(self, config, context):
        """Module 4 : Audit de sécurité"""
        template = self.prompts['security']['prompt']
        prompt_final = template.format(config=config, context=context)
        return self.generate(prompt_final)
        
    def detect_anomaly(self, log_entry, context):
        """Module 6 : Détection d'anomalies"""
        template = self.prompts['anomaly']['prompt']
        # On passe le log et le contexte au template
        prompt_final = template.format(logs=log_entry, context=context)
        return self.generate(prompt_final)

# --- TEST DE VALIDATION DU MODULE ---
if __name__ == "__main__":
    engine = LLMEngine()
    
    # Test : Expliquer un plan d'exécution simple
    test_sql = "SELECT name FROM employees WHERE id = 100"
    test_plan = "INDEX UNIQUE SCAN ON EMP_PK"
    test_context = "L'opération INDEX UNIQUE SCAN est optimale pour les recherches par clé primaire."
    
    print("\n🤖 Envoi du test d'optimisation (Gemini)...")
    reponse = engine.analyze_query(test_sql, test_plan, test_context)
    print(f"\nRésultat de l'IA :\n{reponse}")