import streamlit as st
import sqlite3
import random
from datetime import datetime, timedelta
import os

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

# --- 2. BASE DE DONNÉES ---
def get_db_connection():
    return sqlite3.connect('kikesare.db', check_same_thread=False)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (identifier TEXT PRIMARY KEY, password TEXT, full_name TEXT, type TEXT, verified INTEGER, profile_pic BLOB)''')
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

# --- 4. ACCÈS & INSCRIPTION (AVEC OPTION RENVOYER LE CODE) ---
if not st.session_state['connected']:
    display_logo()
    
    if st.session_state['verifying']:
        st.info(f"📩 Code de sécurité envoyé à : **{st.session_state['temp_id']}**")
        code_s = st.text_input("Saisissez le code de validation")
        
        col_v1, col_v2 = st.columns([1, 1])
        with col_v1:
            if st.button("✅ Valider mon compte"):
                if code_s == str(st.session_state['correct_code']):
                    conn = get_db_connection()
                    conn.execute("INSERT OR REPLACE INTO users (identifier, password, full_name, type, verified) VALUES (?, ?, ?, ?, 1)", 
                                (st.session_state['temp_id'], st.session_state['temp_pwd'], 
                                 st.session_state['temp_name'], st.session_state['temp_type']))
                    conn.commit(); conn.close()
                    st.success("Compte activé !")
                    st.session_state['verifying'] = False; st.rerun()
                else: st.error("Code incorrect.")
        
        with col_v2:
            # --- NOUVELLE OPTION : RENVOYER LE CODE ---
            if st.button("🔄 Renvoyer le code"):
                st.session_state['correct_code'] = random.randint(100000, 999999)
                st.toast(f"Nouveau code généré : {st.session_state['correct_code']}") # Simulation d'envoi
                st.warning("Un nouveau code vous a été envoyé.")

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
                else: st.error("Identifiants incorrects.")

        with tab2:
            with st.form("inscription_form"):
                st.subheader("Créer un nouveau compte")
                new_id = st.text_input("Email ou Téléphone")
                new_name = st.text_input("Nom complet ou Nom de l'entreprise")
                u_type = st.radio("Type de compte :", ["Particulier", "Entrepreneur (École, Loyer, Commerce)"])
                p1 = st.text_input("Mot de passe", type="password")
                p2 = st.text_input("Confirmer le mot de passe", type="password")
                
                if st.form_submit_button("🚀 Recevoir mon code"):
                    if p1 == p2 and len(p1) >= 6:
                        code = random.randint(100000, 999999)
                        st.session_state.update({'temp_id': new_id, 'temp_pwd': p1, 'temp_name': new_name, 'temp_type': u_type, 'correct_code': code, 'verifying': True})
                        st.rerun()
                    else: st.error("Vérifiez les mots de passe (min 6 car.).")

# --- 5. ESPACES UTILISATEURS ---
else:
    with st.sidebar:
        conn = get_db_connection()
        user_pic = conn.execute("SELECT profile_pic FROM users WHERE identifier=?", (st.session_state['user_id'],)).fetchone()
        conn.close()
        if user_pic and user_pic[0]: st.image(user_pic[0], width=100)
        else: st.image("https://www.w3schools.com/howto/img_avatar.png", width=100)
        st.write(f"### {st.session_state['user_name']}")
        st.caption(f"Profil : {st.session_state['user_type']}")
        
        if st.button("🔌 Déconnexion"):
            st.session_state['connected'] = False; st.rerun()

    # ESPACE PARTICULIER (Logique immuable)
    if st.session_state['user_type'] == "Particulier":
        t_ech, t_pay, t_hist = st.tabs(["📊 Échéances", "💳 Paiement", "📜 Historique"])
        with t_pay:
            st.subheader("Effectuer un règlement")
            c1, c2 = st.columns(2)
            with c1:
                serv = st.selectbox("Service", ["🎓 Frais de scolarité", "🏠 Frais de loyer", "🛍️ Achat Commerçant", "💡 Facture EDG"])
                ref = st.text_input("Référence")
                montant = st.number_input("Montant (GNF)", min_value=5000)
                mode = st.selectbox("Modalité", ["Comptant", "2 fois (5 et 20)", "3 fois (5, 15, 25)"])
            with c2:
                moyen = st.radio("Moyen", ["📱 Orange Money", "📱 MTN MoMo", "💳 Carte Visa"])
                if moyen == "💳 Carte Visa":
                    st.text_input("N° de Carte"); st.text_input("Nom sur la carte")
                    st.columns(2)[0].text_input("Exp (MM/AA)"); st.columns(2)[1].text_input("CVV", type="password")
                else: st.text_input("📱 Numéro à débiter")
            
            if st.button("💎 Valider"):
                st.balloons(); st.success("Paiement validé !")

    # ESPACE ENTREPRENEUR (Nouveau Dashboard)
    else:
        st.title("💼 Dashboard de Gestion Entrepreneur")
        tb1, tb2 = st.tabs(["📈 Tableau de bord", "👥 Suivi Clients"])
        with tb1:
            st.metric
