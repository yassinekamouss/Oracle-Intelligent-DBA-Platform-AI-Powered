import json
from llm_engine import LLMEngine
from rag_setup import OracleRAG

class RecoveryAssistant:
    def __init__(self):
        self.engine = LLMEngine()
        self.rag = OracleRAG()

    def chat(self, user_input):
        #Déballage du tuple (docs, metas)
        context_docs, _ = self.rag.retrieve_context(user_input)
        context_text = "\n".join(context_docs)
        
        # Récupération de la configuration depuis prompts.yaml
        recovery_conf = self.engine.prompts['recovery']
        scenarios = recovery_conf['scenarios']
        system_rules = recovery_conf['system_role']
        few_shots = recovery_conf.get('few_shot', "")
        
        # Construction des instructions dynamiques
        full_instructions = f"{system_rules}\n\nEXEMPLES DE CAS (FEW-SHOT) :\n{few_shots}\n"
        full_instructions += "\nINSTRUCTIONS PAR SCÉNARIO :\n"
        for k, v in scenarios.items():
            full_instructions += f"- {v['instruction']}\n"

        # Prompt final combinant Instructions + RAG + Question User
        prompt_final = f"{full_instructions}\n\nCONTEXTE RAG (Documentation Oracle) :\n{context_text}\n\nUSER DBA : {user_input}"
        
        # Génération de la réponse
        response = self.engine.generate(prompt_final)
        
        return response

if __name__ == "__main__":
    assistant = RecoveryAssistant()
    
    print("\n" + "="*50)
    print("🤖 CHATBOT DE RÉCUPÉRATION ORACLE (V2 - CONFORME)")
    print("   Scénarios : Full, PITR, Table, Row-Level")
    print("="*50)
    
    # Test de validation
    # test_question = "Comment récupérer ma base au 15 mars a 14:00:00 ? avec RMAN et une restauration complète."
    # print(f"\n👤 DBA (Test Validation) : {test_question}")
    # print(f"🤖 Assistant :\n{assistant.chat(test_question)}")
    
    # Boucle interactive
    while True:
        try:
            user_msg = input("\n👤 DBA : ")
            if user_msg.lower() in ['exit', 'quit']: break
            print(f"🤖 Assistant : {assistant.chat(user_msg)}")
        except KeyboardInterrupt:
            break