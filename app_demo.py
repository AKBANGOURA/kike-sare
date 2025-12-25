import streamlit as st
import sqlite3
import smtplib
from email.mime.text import MIMEText
import random
import time
from datetime import datetime, timedelta
import os

# --- 1. CONFIGURATION & STYLE ---
st.set_page_config(page_title="Kiké Saré - Business", layout="wide", page_icon="🇬🇳")

# --- 2. BASE DE DONNÉES (LOGIQUE IMMUABLE) ---
def get_db_connection():
    # Utilisation de check_same_thread=False pour éviter les erreurs OperationalError sur Streamlit Cloud
    return sqlite3.connect('kikesare.db', check_same_thread=False)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (identifier TEXT PRIMARY KEY, password TEXT, full_name TEXT, type TEXT, verified INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS echeances 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, service TEXT, date_limite DATE, montant REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS historique 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, service TEXT, montant REAL, date_paiement DATETIME, moyen TEXT, reference TEXT, num_debit TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. GESTION DES ÉTATS ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- 4. INTERFACE D'ACCÈS ---
if not st.session_state['connected']:
    # Correction pour le logo : ne s'affiche que si le fichier existe pour éviter le crash
    if os.path.exists("kikesare_logo.png"):
        st.image("kikesare_logo.png", width=200)
    
    st.markdown("<h1 style='color: #ce1126;'>KIKÉ SARÉ</h1>", unsafe_allow_html=True)
    
    if st.session_state['verifying']:
        st.info(f"📩 Code envoyé à : **{st.session_state['temp_id']}**")
        code_s = st.text_input("Saisissez le code reçu")
        if st.button("Activer mon compte"):
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
        t1, t2 = st.tabs(["Connexion", "Inscription Business"])
        with t1:
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
        with t2:
            with st.form("signup_form"):
                id_u = st.text_input("Email ou Téléphone")
                nom = st.text_input("Nom complet")
                p1 = st.text_input("Nouveau mot de passe", type="password")
                p2 = st.text_input("Confirmer le mot de passe", type="password")
                if st.form_submit_button("🚀 Créer mon compte"):
                    if p1 == p2 and len(p1) >= 6:
                        code = random.randint(100000, 999999)
                        st.session_state.update({'temp_id': id_u, 'temp_pwd': p1, 'temp_name': nom, 'temp_type': "Business", 'correct_code': code, 'verifying': True})
                        st.rerun()
                    else: st.error("Vérifiez la correspondance des mots de passe (min 6 car.)")

# --- 5. INTERFACE BUSINESS (SERVICES & HISTORIQUE) ---
else:
    st.sidebar.markdown(f"### 👤 {st.session_state['user_name']}")
    tabs = st.tabs(["📊 Échéances", "💳 Paiement", "📜 Historique"])

    with tabs[0]: # Suivi avec codes couleurs
        st.subheader("🔔 Mes prochains paiements")
        conn = get_db_connection()
        echs = conn.execute("SELECT service, date_limite, montant FROM echeances WHERE user_id=? ORDER BY date_limite ASC", (st.session_state['user_id'],)).fetchall()
        conn.close()
        if echs:
            cols = st.columns(4)
            for idx, e in enumerate(echs):
                d_lim = datetime.strptime(e[1], '%Y-%m-%d')
                jours = (d_lim - datetime.now()).days
                # Couleur : Vert (>10j), Jaune (>5j), Rouge (Urgent)
                color = "#009460" if jours > 10 else "#fcd116" if jours > 5 else "#ce1126"
                with cols[idx % 4]:
                    st.markdown(f"<div style='border-left:5px solid {color}; padding:10px; background:#f9f9f9; border-radius:5px;'><b>{e[0]}</b><br>{e[2]} GNF<br>Échéance: {e[1]}</div>", unsafe_allow_html=True)
        else: st.info("Aucun paiement futur programmé.")

    with tabs[1]: # Paiement avec icônes
        st.subheader("Effectuer une transaction")
        c1, c2 = st.columns(2)
        with c1:
            serv_map = {
                "🏠 Frais de loyer": "Frais de loyer",
                "🛍️ Achat Commerçant": "Achat Commerçant",
                "📺 Réabonnement Canal+": "Réabonnement Canal+",
                "💡 Facture EDG": "Facture EDG",
                "💧 Facture SEG": "Facture SEG"
            }
            serv_display = st.selectbox("Sélectionnez le service :", list(serv_map.keys()))
            serv_nom = serv_map[serv_display]
            ref = st.text_input("Référence (N° Facture/Boutique)")
            montant = st.number_input("Montant (GNF)", min_value=5000)
        with c2:
            moyen = st.radio("Moyen de paiement :", ["📱 Orange Money", "📱 MTN MoMo", "💳 Carte Visa"])
            num_debit = st.text_input("📱 Numéro à débiter", placeholder="622...")
            # Paiement en 3 fois uniquement pour Loyer, Commerçant et EDG
            can_split = serv_nom in ["Achat Commerçant", "Frais de loyer", "Facture EDG"]
            mode = st.selectbox("Modalité :", ["Comptant (1x)", "Échelonné (3x - 1er, 5, 10 du mois)"] if can_split else ["Comptant (1x)"])
        
        if st.button("💎 Valider le Paiement Sécurisé"):
            if ref and num_debit:
                conn = get_db_connection()
                now = datetime.now().strftime('%Y-%m-%d %H:%M')
                # Enregistrement historique
                conn.execute("INSERT INTO historique (user_id, service, montant, date_paiement, moyen, reference, num_debit) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                            (st.session_state['user_id'], serv_nom, montant, now, moyen, ref, num_debit))
                
                if "3x" in mode:
                    m_suiv = (datetime.now().replace(day=28) + timedelta(days=4)).replace(day=1)
                    for d in ["01", "05", "10"]:
                        date_e = m_suiv.strftime(f'%Y-%m-{d}')
                        conn.execute("INSERT INTO echeances (user_id, service, date_limite, montant) VALUES (?, ?, ?, ?)", 
                                    (st.session_state['user_id'], f"Partiel: {serv_nom}", date_e, montant/3))
                
                conn.commit()
                conn.close()
                st.balloons()
                st.success(f"Transaction réussie pour {serv_nom} !")
            else: st.warning("Veuillez remplir tous les champs.")

    with tabs[2]: # Historique
        st.subheader("📜 Historique des transactions")
        conn = get_db_connection()
        hist = conn.execute("SELECT service, montant, date_paiement, moyen, reference, num_debit FROM historique WHERE user_id=? ORDER BY date_paiement DESC", (st.session_state['user_id'],)).fetchall()
        conn.close()
        for h in hist:
            st.markdown(f"<div style='border-bottom:1px solid #eee; padding:10px;'><b>{h[2]}</b> | {h[0]} : {h[1]} GNF<br><small>Débité de : {h[5]} | Réf : {h[4]}</small></div>", unsafe_allow_html=True)

    if st.sidebar.button("🔌 Déconnexion"):
        st.session_state['connected'] = False
        st.rerun()
