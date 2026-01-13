import os
import json
import sys
from flask import Flask, render_template, request, jsonify

# Ajout du chemin parent pour importer vos modules existants
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from llm_engine import LLMEngine
from rag_setup import OracleRAG

app = Flask(__name__)

# Initialisation unique du Moteur IA pour le chatbot
llm_engine = LLMEngine()
rag_system = OracleRAG()

# --- MÉMOIRE DU CHATBOT ---
CHAT_HISTORY = []

# --- FONCTIONS UTILITAIRES ---

def load_json_data(filename, directory='data'):
    """Charge un fichier JSON depuis le dossier spécifié (défaut: data/)"""
    filepath = os.path.join(os.path.dirname(__file__), '../../', directory, filename)
    if os.path.exists(filepath):
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return None
    return None

def get_security_status(data):
    """Détermine la couleur du statut sécurité"""
    if not data: return "grey"
    score = data.get('score', 0)
    if score >= 80: return "success"
    if score >= 50: return "warning"
    return "danger"

def get_system_context():
    """Résume l'état actuel du système (Audit, Perf, Anomalies)"""
    context = "--- ÉTAT RÉEL DU SYSTÈME (Données Live) ---\n"
    
    # Sécurité
    sec = load_json_data('last_audit.json', directory='data')
    if sec:
        risques = [r['nom'] for r in sec.get('risques', [])]
        context += f"[SÉCURITÉ] Score: {sec.get('score')}/100. Risques: {', '.join(risques[:3])}.\n"
    
    # Performance
    perf = load_json_data('query_analysis.json')
    if perf and isinstance(perf, list):
        exemples = [q.get('sql_id') for q in perf[:2]]
        context += f"[PERFORMANCE] {len(perf)} requêtes lentes. Ex: {', '.join(exemples)}.\n"
    
    # Anomalies
    anom = load_json_data('detected_anomalies.json', directory='data')
    if anom and isinstance(anom, list):
        critiques = [a for a in anom if a.get('classification') == 'CRITIQUE']
        context += f"[ANOMALIES] {len(critiques)} menaces CRITIQUES détectées.\n"
        
    return context

def get_conversation_history(limit=3):
    """
    Formate les derniers échanges pour le prompt (3 paires de questions/réponses max)
    """
    if not CHAT_HISTORY:
        return "Aucun historique précédent."
    
    history_str = ""
    # On prend les 'limit' derniers messages
    recent_msgs = CHAT_HISTORY[-limit:]
    for msg in recent_msgs:
        role = "UTILISATEUR" if msg['role'] == 'user' else "ASSISTANT"
        history_str += f"{role}: {msg['content']}\n"
    return history_str

# --- ROUTES ---

@app.route('/')
def index():
    sec_data = load_json_data('last_audit.json', directory='data')
    perf_data = load_json_data('query_analysis.json')
    anom_data = load_json_data('detected_anomalies.json', directory='data') or []
    
    anomalies_alert = [a for a in anom_data if a.get('classification') in ['CRITIQUE', 'SUSPECT']]
    has_critical = any(a.get('classification') == 'CRITIQUE' for a in anomalies_alert)

    stats = {
        'sec_score': sec_data.get('score', 'N/A') if sec_data else 'N/A',
        'sec_color': get_security_status(sec_data),
        'slow_queries': len(perf_data) if perf_data else 0,
        'anomalies_count': len(anomalies_alert),
        'anom_color': 'danger' if has_critical else 'warning' if anomalies_alert else 'success'
    }
    return render_template('index.html', stats=stats)

@app.route('/security')
def security():
    data = load_json_data('last_audit.json', directory='data')
    return render_template('security.html', data=data or {'score': 0, 'risques': [], 'recommandations': []})

@app.route('/performance')
def performance():
    data = load_json_data('query_analysis.json')
    return render_template('performance.html', queries=data or [])

@app.route('/backup')
def backup():
    plan = load_json_data('backup_plan.json', directory='data') or {}
    rman_path = os.path.join(os.path.dirname(__file__), '../../data', 'backup_script.rman')
    rman_content = "Aucun script généré."
    if os.path.exists(rman_path):
        with open(rman_path, 'r', encoding='utf-8') as f:
            rman_content = f.read()
    return render_template('backup.html', plan=plan, rman=rman_content)

@app.route('/chatbot')
def chatbot_page():
    return render_template('chatbot.html')

# --- API CHATBOT AVEC MÉMOIRE ---

@app.route('/api/chat', methods=['POST'])
def chat_api():
    """
    Endpoint intelligent : RAG + Données Live + Historique
    """
    global CHAT_HISTORY
    user_message = request.json.get('message')
    
    # 1. Récupération des Contextes
    docs, _ = rag_system.retrieve_context(user_message)
    rag_context = "\n".join(docs)
    system_live_data = get_system_context()
    
    # 2. Récupération de l'Historique (Nouveau !)
    history_context = get_conversation_history(limit=6) # On garde les 3 derniers échanges
    
    # 3. Construction du Prompt Complet
    system_instruction = (
        "Tu es l'assistant DBA intelligent. "
        "Tu as accès à :\n"
        "1. L'HISTORIQUE DE LA CONVERSATION (Mémoire).\n"
        "2. L'ÉTAT RÉEL DU SYSTÈME (Audit, Perf...).\n"
        "3. LA DOCUMENTATION (RAG).\n\n"
        "Si l'utilisateur fait référence à une discussion passée (ex: 'la requête dont on parlait'), utilise l'historique.\n"
        "Sois concis."
    )
    
    full_prompt = (
        f"{system_instruction}\n\n"
        f"--- ÉTAT SYSTÈME ACTUEL ---\n{system_live_data}\n\n"
        f"--- HISTORIQUE RÉCENT (MÉMOIRE) ---\n{history_context}\n\n"
        f"--- DOCUMENTATION (RAG) ---\n{rag_context}\n\n"
        f"UTILISATEUR (Message Actuel): {user_message}"
    )
    
    # 4. Génération
    # On passe None comme system_context car il est déjà intégré dans le full_prompt ou géré par generate
    # Mais ici vous avez construit un "full_prompt" manuel qui contient tout.
    # Pour respecter la signature de votre nouvelle méthode generate(user_message, system_context=""),
    # on peut passer tout le prompt comme user_message et rien en système, ou adapter.
    
    # Option simple : Tout passer dans le premier argument, car le prompt est déjà formaté
    bot_reply = llm_engine.generate(full_prompt)
    
    # 5. Mise à jour de la mémoire
    CHAT_HISTORY.append({'role': 'user', 'content': user_message})
    CHAT_HISTORY.append({'role': 'assistant', 'content': bot_reply})
    
    return jsonify({'response': bot_reply})

# Route pour vider la mémoire si besoin (Optionnel)
@app.route('/api/clear_chat', methods=['POST'])
def clear_chat():
    global CHAT_HISTORY
    CHAT_HISTORY = []
    return jsonify({'status': 'cleared'})

if __name__ == '__main__':
    app.run(debug=True, port=5000)