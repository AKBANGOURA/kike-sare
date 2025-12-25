import streamlit as st
import sqlite3
import random
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Kiké Saré - Fintech", layout="wide", page_icon="🇬🇳")

def display_logo():
    st.markdown("""
        <div style="text-align: center;">
            <h1 style="color: #ce1126; margin-bottom: 0;">KIKÉ SARÉ</h1>
            <p style="color: #009460; font-style: italic; font-weight: bold;">La Fintech Guinéenne</p>
            <hr style="border: 1px solid #fcd116; width: 50%;">
        </div>
        """, unsafe_allow_html=True)

# --- 2. BASE DE DONNÉES (MISE À JOUR) ---
def get_db_connection():
    return sqlite3.connect('kikesare.db', check_same_thread=False)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # Ajout de colonnes pour SIRET et distinctions Noms
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (identifier TEXT PRIMARY KEY, password TEXT, full_name TEXT, type TEXT, 
                  verified INTEGER, profile_pic BLOB, siret TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS echeances 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, service TEXT, date_limite DATE, montant REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS historique 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, service TEXT, montant REAL, 
                  date_paiement DATETIME, moyen TEXT, reference TEXT, num_debit TEXT, entrepreneur_id TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. SESSION STATE ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- 4. ACCÈS ---
if not st.session_state['connected']:
    display_logo()
    
    if st.session_state['verifying']:
        st.info(f"📩 Code envoyé à : **{st.session_state['temp_id']}**")
        code_s = st.text_input("Saisissez le code")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if st.button("✅ Valider"):
                if code_s == str(st.session_state['correct_code']):
                    conn = get_db_connection()
                    conn.execute("INSERT OR REPLACE INTO users (identifier, password, full_name, type, verified, siret) VALUES (?, ?, ?, ?, 1, ?)", 
                                (st.session_state['temp_id'], st.session_state['temp_pwd'], 
                                 st.session_state['temp_name'], st.session_state['temp_type'], st.session_state.get('temp_siret', '')))
                    conn.commit(); conn.close()
                    st.success("Compte créé !"); st.session_state['verifying'] = False; st.rerun()
        with col_v2:
            if st.button("🔄 Renvoyer le code"):
                st.session_state['correct_code'] = random.randint(100000, 999999)
                st.toast(f"Nouveau code : {st.session_state['correct_code']}")

    else:
        tab1, tab2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
        with tab1:
            e_log = st.text_input("Identifiant")
            p_log = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter"):
                conn = get_db_connection()
                user = conn.execute("SELECT * FROM users WHERE identifier=? AND password=? AND verified=1", (e_log, p_log)).fetchone()
                conn.close()
                if user:
                    st.session_state.update({'connected': True, 'user_name': user[2], 'user_id': user[0], 'user_type': user[3]})
                    st.rerun()

        with tab2:
            st.subheader("Créer votre espace Kiké Saré")
            # 1. LE CHOIX DU TYPE EN PREMIER [Action demandée]
            u_role = st.radio("Quel type de compte souhaitez-vous ?", ["Particulier", "Entrepreneur (Entreprise)"], horizontal=True)
            
            with st.form("inscription_dynamique"):
                # 2. CHAMPS CONDITIONNELS [Action demandée]
                if u_role == "Particulier":
                    prenom = st.text_input("Prénom")
                    nom = st.text_input("Nom")
                    nom_final = f"{prenom} {nom}"
                    siret_val = None
                else:
                    nom_final = st.text_input("Nom de l'entreprise")
                    siret_val = st.text_input("Numéro SIRET / RCCM")
                
                new_id = st.text_input("Email ou Téléphone")
                p1 = st.text_input("Mot de passe", type="password")
                p2 = st.text_input("Confirmer", type="password")
                
                if st.form_submit_button("🚀 Étape suivante"):
                    if p1 == p2 and len(p1) >= 6 and nom_final and new_id:
                        code = random.randint(100000, 999999)
                        st.session_state.update({
                            'temp_id': new_id, 'temp_pwd': p1, 'temp_name': nom_final, 
                            'temp_type': u_role, 'temp_siret': siret_val, 
                            'correct_code': code, 'verifying': True
                        })
                        st.rerun()
                    else: st.error("Veuillez remplir tous les champs correctement.")

# --- 5. INTERFACES (Logique conservée) ---
else:
    with st.sidebar:
        st.write(f"### {st.session_state['user_name']}")
        st.caption(f"Compte {st.session_state['user_type']}")
        if st.button("🔌 Déconnexion"):
            st.session_state['connected'] = False; st.rerun()

    if st.session_state['user_type'] == "Particulier":
        st.title("📱 Mon Espace Particulier")
        # ... Reste du code de paiement ...
    else:
        st.title("💼 Espace Business")
        st.info(f"Bienvenue, gestionnaire de {st.session_state['user_name']}")
