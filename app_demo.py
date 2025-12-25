import streamlit as st
import sqlite3
import smtplib
from email.mime.text import MIMEText
import random
import time
from datetime import datetime, timedelta
import os

# --- 1. CONFIGURATION & DESIGN ---
st.set_page_config(page_title="Kiké Saré - Business Pro", layout="wide", page_icon="🇬🇳")

st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    .stButton>button {
        background-color: #ce1126; color: white; border-radius: 8px;
        height: 3em; width: 100%; border: none; font-weight: bold;
    }
    .stButton>button:hover { background-color: #fcd116; color: black; }
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DONNÉES (LOGIQUE IMMUABLE + CORRECTIF) ---
def get_db_connection():
    return sqlite3.connect('kikesare.db', check_same_thread=False)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # Tables immuables
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (identifier TEXT PRIMARY KEY, password TEXT, full_name TEXT, type TEXT, verified INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS echeances 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, service TEXT, date_limite DATE, montant REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS historique 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, service TEXT, montant REAL, 
                  date_paiement DATETIME, moyen TEXT, reference TEXT, num_debit TEXT)''')
    
    # RÉPARATION : Ajout forcé de num_debit si absent pour éviter OperationalError
    try:
        c.execute("SELECT num_debit FROM historique LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE historique ADD COLUMN num_debit TEXT")
    
    conn.commit()
    conn.close()

init_db()

# --- 3. GESTION DES ÉTATS & AUTHENTIFICATION ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

if not st.session_state['connected']:
    # Affichage du logo sécurisé
    if os.path.exists("kikesare_logo.png"):
        st.image("kikesare_logo.png", width=200)
    st.markdown("<h1 style='color: #ce1126;'>KIKÉ SARÉ</h1>", unsafe_allow_html=True)
    
    if st.session_state['verifying']:
        st.info(f"📩 Code envoyé à : **{st.session_state['temp_id']}**")
        code_s = st.text_input("Saisissez le code reçu")
        if st.button("✅ Activer mon compte"):
            if code_s == str(st.session_state['correct_code']):
                conn = get_db_connection()
                conn.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, 1)", 
                            (st.session_state['temp_id'], st.session_state['temp_pwd'], 
                             st.session_state['temp_name'], st.session_state['temp_type']))
                conn.commit()
                conn.close()
                st.success("Compte Business validé !")
                st.session_state['verifying'] = False
                st.rerun()
    else:
        tab1, tab2 = st.tabs(["🔐 Connexion", "📝 Inscription Business"])
        with tab1:
            e = st.text_input("Identifiant (Email ou Tél)")
            p = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter"):
                conn = get_db_connection()
                user = conn.execute("SELECT * FROM users WHERE identifier=? AND password=? AND verified=1", (e, p)).fetchone()
                conn.close()
                if user:
                    st.session_state.update({'connected': True, 'user_name': user[2], 'user_id': user[0]})
                    st.rerun()
                else: st.error("Identifiants incorrects.")
        with tab2:
            with st.form("signup_pro"):
                id_u = st.text_input("Email ou Téléphone")
                nom = st.text_input("Nom de l'entreprise / Nom complet")
                p1 = st.text_input("Créer mot de passe", type="password")
                p2 = st.text_input("Confirmer mot de passe", type="password")
                if st.form_submit_button("🚀 Créer mon compte"):
                    if p1 == p2 and len(p1) >= 6:
                        code = random.randint(100000, 999999)
                        st.session_state.update({'temp_id': id_u, 'temp_pwd': p1, 'temp_name': nom, 'temp_type': "Business", 'correct_code': code, 'verifying': True})
                        st.rerun()

# --- 4. INTERFACE PRINCIPALE (DASHBOARD BUSINESS) ---
else:
    st.sidebar.markdown(f"### 👤 {st.session_state['user_name']}")
    tabs = st.tabs(["📊 Échéances", "💳 Paiement", "📜 Historique"])

    with tabs[0]: # Suivi des dates (Rouge, Jaune, Vert)
        st.subheader("🔔 Suivi des paiements")
        conn = get_db_connection()
        echs = conn.execute("SELECT service, date_limite, montant FROM echeances WHERE user_id=? ORDER BY date_limite ASC", (st.session_state['user_id'],)).fetchall()
        conn.close()
        if echs:
            cols = st.columns(4)
            for idx, e in enumerate(echs):
                d_lim = datetime.strptime(e[1], '%Y-%m-%d')
                jours = (d_lim - datetime.now()).days
                color = "#009460" if jours > 10 else "#fcd116" if jours > 5 else "#ce1126"
                with cols[idx % 4]:
                    st.markdown(f"<div style='border-left:5px solid {color}; padding:10px; background:#f9f9f9; border-radius:5px;'><b>{e[0]}</b><br>{e[2]} GNF<br>{e[1]}</div>", unsafe_allow_html=True)
        else: st.info("Aucun paiement futur programmé.")

    with tabs[1]: # Nouveau paiement (BNPL 3x + Numéro Débit)
        st.subheader("Effectuer une transaction")
        c1, c2 = st.columns(2)
        with c1:
            serv_map = {"🏠 Frais de loyer": "Frais de loyer", "🛍️ Achat Commerçant": "Achat Commerçant", 
                        "📺 Réabonnement Canal+": "Réabonnement Canal+", "💡 Facture EDG": "Facture EDG", "💧 Facture SEG": "Facture SEG"}
            serv_display = st.selectbox("Service :", list(serv_map.keys()))
            serv_nom = serv_map[serv_display]
            ref = st.text_input("Référence (N° Facture/Boutique)")
            montant = st.number_input("Montant (GNF)", min_value=5000)
        with c2:
            moyen = st.radio("Moyen :", ["📱 Orange Money", "📱 MTN MoMo", "💳 Carte Visa"])
            num_debit = st.text_input("📱 Numéro à débiter", placeholder="622...")
            can_split = serv_nom in ["Achat Commerçant", "Frais de loyer", "Facture EDG"]
            mode = st.selectbox("Modalité :", ["Comptant (1x)", "Échelonné (3x - 1er, 5, 10 du mois)"] if can_split else ["Comptant (1x)"])
        
        if st.button("💎 Confirmer le Paiement"):
            if ref and num_debit:
                conn = get_db_connection()
                now = datetime.now().strftime('%Y-%m-%d %H:%M')
                conn.execute("INSERT INTO historique (user_id, service, montant, date_paiement, moyen, reference, num_debit) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                            (st.session_state['user_id'], serv_nom, montant, now, moyen, ref, num_debit))
                if "3x" in mode:
                    m_suiv = (datetime.now().replace(day=28) + timedelta(days=4)).replace(day=1)
                    for d in ["01", "05", "10"]:
                        conn.execute("INSERT INTO echeances (user_id, service, date_limite, montant) VALUES (?, ?, ?, ?)", 
                                    (st.session_state['user_id'], f"Partiel: {serv_nom}", m_suiv.strftime(f'%Y-%m-{d}'), montant/3))
                conn.commit(); conn.close()
                st.balloons(); st.success("Transaction réussie !")
            else: st.warning("Veuillez remplir la référence et le numéro à débiter.")

    with tabs[2]: # Historique complet sécurisé
        st.subheader("📜 Historique des transactions")
        conn = get_db_connection()
        try:
            hist = conn.execute("SELECT service, montant, date_paiement, moyen, reference, num_debit FROM historique WHERE user_id=? ORDER BY date_paiement DESC", (st.session_state['user_id'],)).fetchall()
            for h in hist:
                st.markdown(f"<div style='border-bottom:1px solid #eee; padding:10px;'><b>{h[2]}</b> | {h[0]} : {h[1]} GNF<br><small>Débité de : {h[5]} | Réf : {h[4]}</small></div>", unsafe_allow_html=True)
        except Exception as e: st.error("Mise à jour de la base de données nécessaire.")
        conn.close()

    if st.sidebar.button("🔌 Déconnexion"):
        st.session_state['connected'] = False; st.rerun()
