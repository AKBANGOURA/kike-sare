import streamlit as st
import sqlite3
import smtplib
from email.mime.text import MIMEText
import random
import time
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Kiké Saré - Business Pro", layout="wide", page_icon="🇬🇳")

# --- 2. BASE DE DONNÉES IMMUABLE ---
def get_db_connection():
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

# --- 3. LOGIQUE D'AUTHENTIFICATION ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

if not st.session_state['connected']:
    st.markdown("<h1 style='text-align: center; color: #ce1126;'>KIKÉ SARÉ</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center;'>L'excellence du paiement guinéen</p>", unsafe_allow_html=True)
    
    if st.session_state['verifying']:
        st.info(f"📩 Code envoyé à : **{st.session_state['temp_id']}**")
        code_s = st.text_input("Code de validation")
        if st.button("Activer mon compte"):
            if code_s == str(st.session_state['correct_code']):
                conn = get_db_connection()
                conn.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, 1)", 
                            (st.session_state['temp_id'], st.session_state['temp_pwd'], 
                             st.session_state['temp_name'], st.session_state['temp_type']))
                conn.commit()
                conn.close()
                st.success("Compte activé !")
                st.session_state['verifying'] = False
                st.rerun()
    else:
        tab1, tab2 = st.tabs(["Connexion", "Inscription Business"])
        with tab1:
            e = st.text_input("Email ou Téléphone")
            p = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter"):
                conn = get_db_connection()
                user = conn.execute("SELECT * FROM users WHERE identifier=? AND password=? AND verified=1", (e, p)).fetchone()
                conn.close()
                if user:
                    st.session_state.update({'connected': True, 'user_name': user[2], 'user_id': user[0]})
                    st.rerun()
        with tab2:
            with st.form("signup"):
                id_u = st.text_input("Email ou Téléphone (Identifiant)")
                nom = st.text_input("Nom complet / Entreprise")
                p1 = st.text_input("Mot de passe", type="password")
                p2 = st.text_input("Confirmer mot de passe", type="password")
                if st.form_submit_button("🚀 Créer mon compte"):
                    if p1 == p2 and len(p1) >= 6:
                        # (Logique SMTP ici via secrets comme vu précédemment)
                        st.session_state.update({'temp_id': id_u, 'temp_pwd': p1, 'temp_name': nom, 'temp_type': "Business", 'correct_code': "123456", 'verifying': True})
                        st.rerun()

# --- 4. INTERFACE PRINCIPALE ---
else:
    st.sidebar.markdown(f"### 👤 {st.session_state['user_name']}")
    t_dash, t_pay, t_hist = st.tabs(["📊 Tableau de bord", "💳 Nouveau Paiement", "📜 Historique"])

    with t_dash:
        st.subheader("🔔 Suivi des échéances")
        conn = get_db_connection()
        echs = conn.execute("SELECT service, date_limite, montant FROM echeances WHERE user_id=? ORDER BY date_limite ASC", (st.session_state['user_id'],)).fetchall()
        conn.close()
        if echs:
            cols = st.columns(4)
            for idx, e in enumerate(echs):
                d_lim = datetime.strptime(e[1], '%Y-%m-%d')
                jours = (d_lim - datetime.now()).days
                # Couleurs : Rouge (Retard/Imminent), Jaune (Moyen), Vert (Ok)
                color = "#009460" if jours > 10 else "#fcd116" if jours > 5 else "#ce1126"
                with cols[idx % 4]:
                    st.markdown(f"<div style='border-left: 5px solid {color}; background: #f9f9f9; padding: 10px; border-radius: 5px;'><b>{e[0]}</b><br>💰 {e[2]} GNF<br>📅 {e[1]}</div>", unsafe_allow_html=True)
        else: st.info("Aucun paiement futur en attente.")

    with t_pay:
        st.subheader("Nouvelle transaction sécurisée")
        c1, c2 = st.columns([2, 1])
        with c1:
            serv = st.selectbox("Service :", ["Achat Commerçant", "Frais de loyer", "Réabonnement Canal+", "Facture EDG", "Facture SEG", "Frais Scolaires"])
            ref = st.text_input("Référence (N° Facture / Nom du bénéficiaire)")
            montant = st.number_input("Montant (GNF)", min_value=5000)
        with c2:
            moyen = st.radio("Moyen :", ["📱 Orange Money", "📱 MTN MoMo", "💳 Carte Visa"])
            
            # --- LE CHAMP RÉTABLI ICI ---
            num_debit = st.text_input("📱 Numéro à débiter", placeholder="622 00 00 00")
            
            mode = st.selectbox("Modalité :", ["Comptant (1x)", "Échelonné (3x - 1er, 5, 10 du mois)"] if serv in ["Achat Commerçant", "Frais de loyer", "Facture EDG"] else ["Comptant (1x)"])
        
        if st.button("💎 Confirmer le Paiement"):
            if ref and num_debit:
                with st.spinner("Initialisation du débit..."):
                    time.sleep(2)
                    conn = get_db_connection()
                    now_str = datetime.now().strftime('%Y-%m-%d %H:%M')
                    
                    # 1. Historique
                    conn.execute("INSERT INTO historique (user_id, service, montant, date_paiement, moyen, reference, num_debit) VALUES (?, ?, ?, ?, ?, ?, ?)",
                                (st.session_state['user_id'], serv, montant, now_str, moyen, ref, num_debit))
                    
                    # 2. Échéances si 3x
                    if "3x" in mode:
                        mois_suiv = (datetime.now().replace(day=28) + timedelta(days=4)).replace(day=1)
                        dates = [mois_suiv.strftime('%Y-%m-01'), mois_suiv.strftime('%Y-%m-05'), mois_suiv.strftime('%Y-%m-10')]
                        for d in dates:
                            conn.execute("INSERT INTO echeances (user_id, service, date_limite, montant) VALUES (?, ?, ?, ?)", 
                                        (st.session_state['user_id'], f"Partiel: {serv}", d, montant/3))
                    
                    conn.commit()
                    conn.close()
                    st.balloons()
                    st.success(f"Paiement de {montant} GNF validé sur le {num_debit} !")
            else: st.warning("Veuillez remplir la référence et le numéro à débiter.")

    with t_hist:
        st.subheader("📜 Historique")
        conn = get_db_connection()
        hist = conn.execute("SELECT service, montant, date_paiement, moyen, reference, num_debit FROM historique WHERE user_id=? ORDER BY date_paiement DESC", (st.session_state['user_id'],)).fetchall()
        conn.close()
        for h in hist:
            st.markdown(f"<div style='border-bottom
