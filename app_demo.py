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
                  verified INTEGER, profile_pic BLOB, siret TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. SESSION STATE ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- 4. ACCÈS (LOGIN / INSCRIPTION DYNAMIQUE) ---
if not st.session_state['connected']:
    display_logo()
    
    if st.session_state['verifying']:
        st.info(f"📩 Un code de validation a été envoyé à : **{st.session_state['temp_id']}**")
        code_s = st.text_input("Saisissez le code de validation")
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if st.button("✅ Valider l'inscription"):
                if code_s == str(st.session_state['correct_code']):
                    conn = get_db_connection()
                    conn.execute("INSERT OR REPLACE INTO users (identifier, password, full_name, type, verified, siret) VALUES (?, ?, ?, ?, 1, ?)", 
                                (st.session_state['temp_id'], st.session_state['temp_pwd'], 
                                 st.session_state['temp_name'], st.session_state['temp_type'], st.session_state.get('temp_siret', '')))
                    conn.commit(); conn.close()
                    st.success("Compte créé avec succès ! Connectez-vous.")
                    st.session_state['verifying'] = False
                    st.rerun()
                else:
                    st.error("Code de validation incorrect.")
        
        with col_v2:
            # OPTION RENVOYER LE CODE [Action demandée]
            if st.button("🔄 Renvoyer le code par mail"):
                st.session_state['correct_code'] = random.randint(100000, 999999)
                st.toast(f"Nouveau code envoyé : {st.session_state['correct_code']}")
                st.info("Un nouveau code a été généré et envoyé.")

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
            st.subheader("Créer votre compte")
            u_role = st.radio("Vous êtes :", ["Particulier", "Entrepreneur (Entreprise)"], horizontal=True)
            
            with st.form("inscription_form"):
                if u_role == "Particulier":
                    prenom = st.text_input("Prénom")
                    nom = st.text_input("Nom")
                    nom_final = f"{prenom} {nom}"
                    siret_val = ""
                else:
                    nom_final = st.text_input("Nom de l'entreprise")
                    siret_val = st.text_input("Numéro SIRET / RCCM")
                
                new_id = st.text_input("Email de contact")
                
                # MOT DE PASSE EN DOUBLE [Action demandée]
                p1 = st.text_input("Créer un mot de passe", type="password")
                p2 = st.text_input("Confirmer le mot de passe", type="password")
                
                if st.form_submit_button("🚀 Recevoir le code de validation"):
                    if p1 != p2:
                        st.error("Les mots de passe ne correspondent pas.")
                    elif len(p1) < 6:
                        st.error("Le mot de passe doit contenir au moins 6 caractères.")
                    elif not new_id or not nom_final:
                        st.error("Veuillez remplir tous les champs.")
                    else:
                        code = random.randint(100000, 999999)
                        st.session_state.update({
                            'temp_id': new_id, 'temp_pwd': p1, 'temp_name': nom_final, 
                            'temp_type': u_role, 'temp_siret': siret_val, 
                            'correct_code': code, 'verifying': True
                        })
                        st.rerun()

# --- 5. INTERFACES (Logique conservée) ---
else:
    st.sidebar.write(f"Connecté en tant que : **{st.session_state['user_name']}**")
    if st.sidebar.button("Déconnexion"):
        st.session_state['connected'] = False; st.rerun()
    
    if st.session_state['user_type'] == "Particulier":
        st.title("📱 Espace Particulier")
    else:
        st.title("💼 Espace Business")
