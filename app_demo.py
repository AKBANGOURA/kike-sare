import streamlit as st
import sqlite3
import random
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Kiké Saré - La Fintech Guinéenne", layout="wide", page_icon="🇬🇳")

def display_logo():
    st.markdown("""
        <div style="text-align: center;">
            <h1 style="color: #ce1126; margin-bottom: 0;">KIKÉ SARÉ</h1>
            <p style="color: #009460; font-style: italic; font-weight: bold;">La Fintech Guinéenne</p>
            <hr style="border: 1px solid #fcd116; width: 50%;">
        </div>
        """, unsafe_allow_html=True)

# --- 2. BASE DE DONNÉES ---
def get_db_connection():
    return sqlite3.connect('kikesare.db', check_same_thread=False)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (identifier TEXT PRIMARY KEY, password TEXT, full_name TEXT, type TEXT, 
                  verified INTEGER, siret TEXT, methode_retrait TEXT, num_retrait TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS historique 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, service TEXT, montant REAL, 
                  date_paiement DATETIME, moyen TEXT, reference TEXT, entrepreneur_id TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. SESSION STATE ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- 4. ACCÈS (LOGIN / INSCRIPTION) ---
if not st.session_state['connected']:
    display_logo()
    
    if st.session_state['verifying']:
        st.info(f"📩 Code envoyé à : **{st.session_state['temp_id']}**")
        code_s = st.text_input("Code de validation")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if st.button("✅ Valider l'inscription"):
                if code_s == str(st.session_state['correct_code']):
                    conn = get_db_connection()
                    conn.execute("INSERT OR REPLACE INTO users (identifier, password, full_name, type, verified, siret) VALUES (?, ?, ?, ?, 1, ?)", 
                                (st.session_state['temp_id'], st.session_state['temp_pwd'], st.session_state['temp_name'], st.session_state['temp_type'], st.session_state.get('temp_siret', '')))
                    conn.commit(); conn.close()
                    st.success("Compte validé ! Connectez-vous.")
                    st.session_state['verifying'] = False; st.rerun()
        with col_v2:
            if st.button("🔄 Renvoyer le code par mail"):
                st.session_state['correct_code'] = random.randint(100000, 999999)
                st.toast(f"Nouveau code généré : {st.session_state['correct_code']}")

    else:
        tab1, tab2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
        with tab1:
            e_log = st.text_input("Identifiant (Email ou Tél)")
            p_log = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter"):
                conn = get_db_connection()
                user = conn.execute("SELECT * FROM users WHERE identifier=? AND password=? AND verified=1", (e_log, p_log)).fetchone()
                conn.close()
                if user:
                    st.session_state.update({'connected': True, 'user_name': user[2], 'user_id': user[0], 'user_type': user[3]})
                    st.rerun()
                else: st.error("Identifiants incorrects ou compte non vérifié.")

        with tab2:
            u_role = st.radio("S'inscrire en tant que :", ["Particulier", "Entrepreneur (Groupe/Entreprise)"], horizontal=True)
            with st.form("inscription_form"):
                if u_role == "Particulier":
                    nom_final = f"{st.text_input('Prénom')} {st.text_input('Nom')}"
                    siret_val = ""
                else:
                    nom_final = st.text_input("Nom de l'entreprise (ex: Groupe AKB)")
                    siret_val = st.text_input("N° SIRET / RCCM")
                
                new_id = st.text_input("Email de validation")
                p1 = st.text_input("Mot de passe", type="password")
                p2 = st.text_input("Confirmer le mot de passe", type="password")
                
                if st.form_submit_button("🚀 Recevoir mon code"):
                    if p1 == p2 and len(p1) >= 6:
                        code = random.randint(100000, 999999)
                        st.session_state.update({'temp_id': new_id, 'temp_pwd': p1, 'temp_name': nom_final, 'temp_type': u_role, 'temp_siret': siret_val, 'correct_code': code, 'verifying': True})
                        st.rerun()
                    else: st.error("Vérifiez vos mots de passe (6 car. min).")

# --- 5. ESPACES DE GESTION ---
else:
    with st.sidebar:
        st.write(f"### {st.session_state['user_name']}")
        st.caption(f"Compte {st.session_state['user_type']}")
        if st.button("🔌 Déconnexion"):
            st.session_state['connected'] = False; st.rerun()

    if st.session_state['user_type'] != "Particulier":
        # ESPACE ENTREPRENEUR / GROUPE
        st.title("💼 Dashboard Business - Gestion de Fonds")
        t1, t2, t3 = st.tabs(["📊 Suivi des Recettes", "💸 Mode de Réception", "👥 Clients"])
        
        with t1:
            st.subheader("Encaissements par catégorie")
            c1, c2, c3 = st.columns(3)
            # Les données suivantes sont simulées pour l'interface
            c1.metric("🏠 Loyers reçus", "45.000.000 GNF", "+10%")
            c2.metric("🎓 Scolarités", "22.500.000 GNF")
            c3.metric("🛒 Marchandises", "8.900.000 GNF")
            
            st.write("### Graphique des revenus")
            st.bar_chart({"Loyers": [30, 45], "Scolarité": [15, 22.5], "Ventes": [5, 8.9]})

        with t2:
            st.subheader("💰 Configuration de la réception des fonds")
            st.write("Enregistrez le moyen par lequel vous souhaitez recevoir l'argent collecté.")
            with st.form("config_retrait"):
                methode = st.selectbox("Moyen de réception", ["Orange Money Business", "MTN MoMo Business", "Virement Bancaire"])
                num = st.text_input("Numéro ou RIB de réception")
                if st.form_submit_button("💾 Enregistrer"):
                    st.success("Moyen de réception configuré avec succès !")

    else:
        # ESPACE PARTICULIER (Paiement)
        st.title("📱 Mon Portefeuille de Paiement")
        st.info("Paiement de loyer, scolarité et factures avec échelonnement.")
