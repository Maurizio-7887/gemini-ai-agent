import streamlit as st
import random
import time
import re
import sys
from google import genai
from google.genai import types

# --- Configurazione API Gemini ---
# Il client cercherà automaticamente la chiave nella variabile d'ambiente GOOGLE_API_KEY
try:
    client = genai.Client()
except Exception as e:
    # Mostra un errore chiaro se l'API non si inizializza (es. chiave mancante)
    st.error(f"ERRORE GRAVE: Impossibile inizializzare il client Gemini. Assicurati che la chiave GOOGLE_API_KEY sia configurata correttamente in secrets.toml.")
    sys.exit()

# Nome del modello da usare per il RAG
GEMINI_MODEL = 'gemini-2.5-flash' 


# --- Base di Conoscenza e Contesto RAG (I Tuoi Dati Estratti) ---

# Questa stringa contiene i punti salienti estratti dal tuo sito web.
# Sarà passata a Gemini come contesto per la risposta.
BASE_CONOSCENZA_RAG = """
MAURIZIO GUSTINICCHI: Controller 5.0 e consulente strategico con esperienza trentennale, specializzato in AI su misura.
MISSIONE: Trasformare i dati complessi (budget, controllo di gestione, R&S) in decisioni chiare e profittevoli, usando algoritmi AI creati su misura.
SETTORI CHIAVE: CFO/Controller, Operations Manager.

SERVIZI E METODOLOGIE:
1. Controllo di Gestione Avanzato (Controller 5.0): Modelli previsionali con AI (Forecasting). Sfrutta Simuazioni Monte Carlo fino a 1 o 10 milioni di opzioni per un'analisi predittiva e per indici (ROA, ROI, ROS). Analisi Costificazione FICO (Full/Direct Costing) e Pricing Dinamico.
2. Operations Smart e Zero Errori: AI per Anomaly Detection (controllo qualità) e Manutenzione Predittiva (PdM) per minimizzare i fermi macchina. Ottimizza la Capacity Planning (pianificazione della capacità produttiva).
3. Innovation Manager (Certificato DNV - UNI 11814 / ISO 56002): Supporto per l'ottenimento di Finanziamenti R&S, bandi e agevolazioni. Implementa Sistemi di Gestione dell'Innovazione (ISO 56002).
4. Digitalizzazione e Lean Process: Mappatura del Valore (VSM) e riorganizzazione dei flussi (Matrici RACI) per creare strutture snelle e distribuite. Sviluppo di Software Snelli (Custom SW).
5. Business Reporting: Sostituzione di sistemi complessi (come Power BI/DAX) con Dashboard di Business Intelligence (BI) su misura, sviluppate in Python/Streamlit, già predisposte per l'AI.
6. Data Quality: Analisi e correzione dei dati (Data Cleansing) per preparare l'infrastruttura aziendale all'implementazione dell'Intelligenza Artificiale.

ROI: L'investimento in AI produce un ROI medio superiore al 150% nel primo anno.
"""

# --- Funzione per il VERO RAG (Integrazione Gemini) ---

def ask_gemini_with_rag(user_input, model=GEMINI_MODEL, context=BASE_CONOSCENZA_RAG):
    """
    Invia la query dell'utente a Gemini insieme al contesto RAG
    per ottenere una risposta generativa, contestualizzata e persuasiva.
    """
    
    # 1. Definizione del Prompt Strategico (Istruzioni all'Agente)
    system_prompt = f"""
    Sei l'Assistente AI specializzato di Maurizio Gustinicchi. Il tuo obiettivo è duplice: informare l'utente con precisione e persuaderlo a prenotare una call, enfatizzando l'uso dell'AI su misura.
    Rispondi alle domande dell'utente solo basandoti sul CONTESTO fornito qui sotto, che deriva dal sito web di Maurizio. Non inventare informazioni.
    Se la domanda riguarda un servizio specifico, usa la terminologia esatta del CONTESTO (es. 'Controller 5.0', 'Simulazioni Monte Carlo', 'Anomaly Detection').
    Mantieni un tono professionale, autorevole e focalizzato sul ROI e sulla soluzione di problemi.

    CONTESTO (Base di Conoscenza del Sito Web):
    ---
    {context}
    ---
    """
    
    try:
        response = client.models.generate_content(
            model=model,
            contents=[user_input],
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=0.4 # Temperatura bassa per risposte fattuali e coerenti
            )
        )
        return response.text
    except Exception as e:
        # Fallback in caso di errore API
        st.error(f"Errore RAG: {e}. Torno alla logica di fallback.")
        return f"Mi scuso, ho riscontrato un errore di comunicazione con l'AI di Gemini. Tuttavia, posso confermarti che la competenza chiave di Maurizio è creare Algoritmi AI su misura per risolvere sfide come la tua. Sei pronto a prenotare una call?"

# --- Dizionario (Solo per Saluti e Logica Agentica/CTA) ---
conoscenza = {
    "saluti_iniziali": { "keywords": ["ciao", "salve", "buongiorno", "buonasera"], "risposte": ["Ciao! Sono il tuo assistente AI specializzato. Come posso aiutarti con i tuoi dati, i costi o l'innovazione aziendale?", "Buongiorno! Sono a tua disposizione. Chiedi pure in che area del Controllo di Gestione o dell'AI ti serve supporto."] },
    "saluti_finali": { "keywords": ["grazie", "a presto", "saluti", "arrivederci"], "risposte": ["È stato un piacere. Ricorda: il mio obiettivo è convertire i tuoi obiettivi in risultati concreti. A presto!", "Prego! Per qualsiasi altra esigenza strategica, sono qui. Buona giornata!"] },
    "lead_capture": {
        "keywords": ["contatto", "contattarti", "riferimenti", "email", "telefono", "richiamato", "parlare con"],
        "risposte": [
            "Certamente. Il modo migliore e più efficace per parlare direttamente con Maurizio (il Controller 5.0) è prenotare una call gratuita dal suo calendario. Ti assicuro che la nostra prima conversazione sarà un'illuminazione: potrai spiegare la tua sfida e lui ti darà un primo feedback di valore. Puoi prenotarla qui:",
            "Assolutamente. Per garantire che la tua richiesta venga gestita con la massima attenzione, il primo passo è una breve call conoscitiva. Ti permette di spiegare la tua situazione e a lui di darti un primo feedback di valore. Puoi prenotarla qui:"
        ]
    },
    "richiesta_consulenza": { "keywords": ["consulenza", "parlare con te", "aiuto", "come lavori", "supporto", "problema", "bisogno"], "pre_analisi_start": "Mi fa molto piacere che tu voglia approfondire. Per capire come posso esserti davvero d'aiuto, posso farti un paio di domande veloci?" },
    "pre_analisi_flow": {
        "domande": [
            "Certamente. Prima di tutto, qual è **la sfida più grande** che la tua azienda sta affrontando in questo momento? (es. costi fuori controllo, processi lenti, difficoltà a innovare...)",
            "Capisco. E ora, immagina per un momento: quale **risultato**, se potessi ottenerlo domani, **cambierebbe tutto** per te e per il tuo business?",
            "Grazie per la chiarezza. Un'ultima domanda per prepararci al meglio: hai già un'idea del **budget di spesa** che vorresti allocare per questo progetto di trasformazione?"
        ],
        "call_to_action": ["Perfetto. Grazie per aver condiviso questi punti. Vedo chiaramente il potenziale inespresso. La consulenza di Maurizio unisce la precisione matematica dell'AI, che programma personalmente, a un'empatia profonda per la tua visione. La nostra prima conversazione sarà un'**illuminazione**.\n\nSei pronto a provare questa sensazione? Parliamone."]
    },
    "domanda_generica": { "keywords": [], "risposte": ["Risposta generica di fallback: posso dirti come affronterei il problema: analizzerei i dati con un algoritmo AI personalizzato per trovare la soluzione più efficiente."] }
}

def get_next_response(service_key):
    # Logica di recupero semplice per saluti e CTA (che sono pre-scritte)
    responses = conoscenza[service_key]["risposte"]
    if not responses: return ""
    return random.choice(responses)

def check_for_engagement(user_input):
    """
    Agentica: Controlla se l'utente è sufficientemente coinvolto per forzare la CTA.
    """
    engagement_keywords = ["soluzione", "budget", "costo", "problema", "investimento", "urgente", "sfida", "crescita"]
    
    score = 0
    for keyword in engagement_keywords:
        if keyword in user_input.lower():
            score += 1
            
    if score > 0:
        st.session_state.engagement_counter += score
        
    # La logica Agentica scatta dopo un coinvolgimento sufficiente
    if st.session_state.engagement_counter >= 4 and len(st.session_state.messages) > 4:
        return True
    
    return False


def get_ai_response(user_input):
    user_input_lower = user_input.lower()
    
    # 1. LOGICA STANDARD (Saluti e CTA esplicite)
    for key in conoscenza["saluti_iniziali"]["keywords"]:
        if key in user_input_lower: return get_next_response("saluti_iniziali")
    for key in conoscenza["saluti_finali"]["keywords"]:
        if key in user_input_lower: return get_next_response("saluti_finali")
    
    if 'lead_capture' in conoscenza:
        for key in conoscenza["lead_capture"]["keywords"]:
            if key in user_input_lower:
                st.session_state.conversation_mode = "lead_capture_cta"
                return get_next_response("lead_capture")

    # 2. AVVIO PRE-ANALISI (se l'utente chiede consulenza)
    for key in conoscenza["richiesta_consulenza"]["keywords"]:
        if key in user_input_lower and st.session_state.conversation_mode == "standard":
            st.session_state.conversation_mode = "pre_analisi"
            st.session_state.question_index = 0
            return conoscenza["richiesta_consulenza"]["pre_analisi_start"]

    # 3. CONTROLLO ENGAGEMENT (Agentica: Forziamo la CTA)
    if check_for_engagement(user_input):
         st.session_state.conversation_mode = "lead_capture_cta"
         return get_next_response("lead_capture")
    
    # 4. VERO RAG CON GEMINI PER TUTTE LE DOMANDE DI CONTENUTO
    return ask_gemini_with_rag(user_input)

def stream_response(response_text):
    placeholder = st.empty()
    full_response = ""
    for chunk in response_text.split():
        full_response += chunk + " "
        time.sleep(0.02)
        placeholder.markdown(full_response + "▌")
    placeholder.markdown(full_response)
    return full_response

# --- Interfaccia Streamlit ---
st.set_page_config(page_title="Assistente AI di Maurizio Gustinicchi", layout="wide")
st.title("Assistente AI di Maurizio Gustinicchi 🚀 (RAG Ibrido con Gemini)")
st.markdown("""
Sono il tuo **Agente AI ibrido** specializzato nel Controllo di Gestione 5.0. Utilizzo l'intelligenza di Gemini e la base di conoscenza del sito di Maurizio Gustinicchi per darti risposte precise e strategiche. Chiedi pure!
""")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "conversation_mode" not in st.session_state:
    st.session_state.conversation_mode = "standard"
if "question_index" not in st.session_state:
    st.session_state.question_index = 0
if "engagement_counter" not in st.session_state:
    st.session_state.engagement_counter = 0

# Visualizzazione messaggi e CTA (Call to Action)
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message.get("is_cta"): 
            st.link_button("🗓️ Prenota una call gratuita con Maurizio", "https://calendly.com/TUO_LINK_QUI")

if prompt := st.chat_input("Descrivi la tua esigenza..."):
    # Messaggio Utente
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response_content = ""
    is_cta_response = False
    
    with st.chat_message("assistant"):
        # GESTIONE FLUSSO PRE-ANALISI (QUESTIONARIO)
        if st.session_state.conversation_mode == "pre_analisi":
            q_index = st.session_state.question_index
            domande = conoscenza["pre_analisi_flow"]["domande"]
            
            if q_index < len(domande):
                response_content = stream_response(domande[q_index])
                st.session_state.question_index += 1
            else:
                # Flusso terminato: Call to Action finale
                response_content = stream_response(get_next_response("pre_analisi_flow"))
                st.link_button("🗓️ Prenota una call gratuita con Maurizio", "https://calendly.com/TUO_LINK_QUI")
                st.session_state.conversation_mode = "standard"
                st.session_state.question_index = 0 
                is_cta_response = True
        
        # LOGICA STANDARD E RAG
        else:
            response_content = get_ai_response(prompt)
            stream_response(response_content)
            
            # Attivazione CTA dopo Lead Capture o Engagement alto
            if st.session_state.get("conversation_mode") == "lead_capture_cta":
                st.link_button("🗓️ Prenota una call gratuita con Maurizio", "https://calendly.com/TUO_LINK_QUI")
                st.session_state.conversation_mode = "standard"
                st.session_state.engagement_counter = 0 
                is_cta_response = True

    # Salva il messaggio dell'assistente nella sessione
    st.session_state.messages.append({"role": "assistant", "content": response_content, "is_cta": is_cta_response})
    st.rerun()