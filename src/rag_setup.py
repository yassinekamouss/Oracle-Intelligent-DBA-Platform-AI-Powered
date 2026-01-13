import os
import chromadb
from chromadb.utils import embedding_functions

class OracleRAG:
    def __init__(self, db_path="data/chroma_db"):
        """Initialise ChromaDB avec un modèle d'embedding local [cite: 55, 58]"""
        if not os.path.exists("data"):
            os.makedirs("data")

        self.client = chromadb.PersistentClient(path=db_path)
        
        self.emb_fn = embedding_functions.SentenceTransformerEmbeddingFunction(
            model_name="all-MiniLM-L6-v2"
        )
        
        self.collection = self.client.get_or_create_collection(
            name="oracle_docs", 
            embedding_function=self.emb_fn
        )
        print("✅ Base Vectorielle ChromaDB prête (Mode Local).")

    def add_documents(self, folder_path):
        """Lit les fichiers .txt et les indexe dans la base [cite: 59]"""
        if not os.path.exists(folder_path):
            print(f"⚠️ Dossier {folder_path} introuvable.")
            return

        documents = []
        ids = []
        metadatas = []

        for filename in os.listdir(folder_path):
            if filename.endswith(".txt"):
                file_path = os.path.join(folder_path, filename)
                with open(file_path, 'r', encoding='utf-8') as f:
                    documents.append(f.read())
                    ids.append(filename)
                    metadatas.append({"source": filename})
        
        if documents:
            self.collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            print(f"📖 {len(documents)} documents indexés/mis à jour avec succès.")

    def retrieve_context(self, query, n_results=5):
        """Recherche par similarité sémantique (TOP-5 requis) """
        results = self.collection.query(
            query_texts=[query],
            n_results=n_results
        )
        # Retourne les textes et les métadonnées pour le test
        return results['documents'][0], results['metadatas'][0]

# --- BLOC DE TEST DE VALIDATION (MODULE 2) ---
if __name__ == "__main__":
    rag = OracleRAG()
    rag.add_documents("data/knowledge") 

    # Test demandé : vérifier que "index lent" retourne des documents sur l'indexation 
    test_query = "Comment optimiser un index lent ?"
    print(f"\n🔍 Test de validation : {test_query}")
    
    try:
        docs, metas = rag.retrieve_context(test_query)
        
        print(f"📊 Top-5 des sources trouvées :")
        found_correct_doc = False
        for i, m in enumerate(metas):
            print(f"  {i+1}. {m['source']}")
            if "index" in m['source'].lower():
                found_correct_doc = True
        
        if found_correct_doc:
            print("\n✅ TEST RÉUSSI : Le système a identifié des documents sur les index.")
        else:
            print("\n❌ TEST ÉCHOUÉ : Aucun document sur les index dans le top-5.")
            
    except Exception as e:
        print(f"❌ Erreur technique : {e}")