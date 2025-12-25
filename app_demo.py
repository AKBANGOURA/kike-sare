import streamlit as st
import sqlite3
import random
from datetime import datetime, timedelta
import os

# --- 1. CONFIGURATION & DESIGN ---
st.set_page_config(page_title="Kiké Saré - Business Pro", layout="wide", page_icon="🇬🇳")

def display_logo():
    st.markdown(
        """
        <div style="text-align: center;">
            <h1 style="color: #ce1126; margin-bottom: 0;">KIKÉ SARÉ</h1>
            <p style="color: #009460; font-style: italic; font-weight: bold;">La Fintech Guinéenne</p>
            <hr style="border: 1px solid #fcd116; width: 50%;">
        </div>
        """, unsafe_allow_html=True
    )

# --- 2. BASE DE DONNÉES (LOGIQUE IMMUABLE + RÉPARATION AUTO) ---
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
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, service TEXT, montant REAL, 
                  date_paiement DATETIME, moyen TEXT, reference TEXT, num_debit TEXT)''')
    
    # CORRECTIF : Ajout automatique de num_debit pour stopper l'OperationalError
    try:
        c.execute("SELECT num_debit FROM historique LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE historique ADD COLUMN num_debit TEXT")
    
    conn.commit()
    conn.close()

init_db()

# --- 3. GESTION DES ÉTATS ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- 4. ACCÈS ---
if not st.session_state['connected']:
    display_logo()
    if st.session_state['verifying']:
        st.info(f"📩 Code envoyé à : **{st.session_state['temp_id']}**")
        code_s = st.text_input("Code de validation")
        if st.button("✅ Valider"):
            if code_s == str(st.session_state['correct_code']):
                conn = get_db_connection()
                conn.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, 1)", 
                            (st.session_state['temp_id'], st.session_state['temp_pwd'], 
                             st.session_state['temp_name'], st.session_state['temp_type']))
                conn.commit(); conn.close()
                st.success("Compte activé !"); st.session_state['verifying'] = False; st.rerun()
    else:
        t1, t2 = st.tabs(["🔐 Connexion", "📝 Inscription Business"])
        with t1:
            e = st.text_input("Identifiant")
            p = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter"):
                conn = get_db_connection()
                user = conn.execute("SELECT * FROM users WHERE identifier=? AND password=? AND verified=1", (e, p)).fetchone()
                conn.close()
                if user:
                    st.session_state.update({'connected': True, 'user_name': user[2], 'user_id': user[0]})
                    st.rerun()
                else: st.error("Erreur d'authentification.")
        with t2:
            with st.form("signup"):
                id_u = st.text_input("Email/Tél")
                nom = st.text_input("Nom Entreprise")
                p1 = st.text_input("Pass", type="password")
                p2 = st.text_input("Confirm", type="password")
                if st.form_submit_button("🚀 Créer mon compte"):
                    if p1 == p2:
                        code = random.randint(100000, 999999)
                        st.session_state.update({'temp_id': id_u, 'temp_pwd': p1, 'temp_name': nom, 'temp_type': "Business", 'correct_code': code, 'verifying': True})
                        st.rerun()

# --- 5. INTERFACE ENTREPRENEUR ---
else:
    st.sidebar.write(f"👤 {st.session_state['user_name']}")
    tabs = st.tabs(["📊 Échéances", "💳 Paiement", "📜 Historique"])

    with tabs[0]: # Dashboard visuel
        st.subheader("🔔 Suivi des paiements échelonnés")
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
        else: st.info("Aucun paiement futur.")

    with tabs[1]: # LOGIQUE DE PAIEMENT MISE À JOUR
        st.subheader("Nouvelle transaction")
        c1, c2 = st.columns(2)
        with c1:
            serv_map = {
                "🎓 Frais de scolarité": "Frais de scolarité",
                "🏠 Frais de loyer": "Frais de loyer", 
                "🛍️ Achat Commerçant": "Achat Commerçant", 
                "💡 Facture EDG": "Facture EDG",
                "📺 Canal+": "Canal+"
            }
            serv_nom = serv_map[st.selectbox("Service", list(serv_map.keys()))]
            ref = st.text_input("Référence (N° Facture/Étudiant)")
            montant = st.number_input("Montant (GNF)", min_value=5000)
        with c2:
            moyen = st.radio("Moyen", ["📱 Orange Money", "📱 MTN MoMo", "💳 Carte Visa"])
            num_debit = st.text_input("📱 Numéro à débiter", placeholder="622...")
            # Éligibilité au paiement échelonné (Scolarité rajoutée)
            can_split = serv_nom in ["Frais de scolarité", "Achat Commerçant", "Frais de loyer", "Facture EDG"]
            mode = st.selectbox("Modalité", ["Comptant", "2 fois (5 et 20 du mois)", "3 fois (5, 15, 25 du mois)"] if can_split else ["Comptant"])
        
        if st.button("💎 Valider le Règlement"):
            if ref and num_debit:
                conn = get_db_connection()
                now = datetime.now().strftime('%Y-%m-%d %H:%M')
                conn.execute("INSERT INTO historique (user_id, service, montant, date_paiement, moyen, reference, num_debit) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                            (st.session_state['user_id'], serv_nom, montant, now, moyen, ref, num_debit))
                
                # NOUVELLE LOGIQUE DE DATES
                if "fois" in mode:
                    m_suiv = (datetime.now().replace(day=28) + timedelta(days=4)).replace(day=1)
                    dates_e = ["05", "15", "25"] if "3" in mode else ["05", "20"]
                    div = 3 if "3" in mode else 2
                    for d in dates_e:
                        conn.execute("INSERT INTO echeances (user_id, service, date_limite, montant) VALUES (?, ?, ?, ?)", 
                                    (st.session_state['user_id'], f"Partiel: {serv_nom}", m_suiv.strftime(f'%Y-%m-{d}'), montant/div))
                
                conn.commit(); conn.close()
                st.balloons(); st.success("Transaction validée !")
            else: st.warning("Champs obligatoires : Référence et Numéro.")

    with tabs[2]: # Historique (Correctif)
        st.subheader("📜 Historique")
        conn = get_db_connection()
        try:
            hist = conn.execute("SELECT service, montant, date_paiement, reference, num_debit FROM historique WHERE user_id=? ORDER BY date_paiement DESC", (st.session_state['user_id'],)).fetchall()
            for h in hist:
                st.markdown(f"<div style='border-bottom:1px solid #eee; padding:10px;'><b>{h[2]}</b> | {h[0]} : {h[1]} GNF<br><small>Réf : {h[3]} | Débit : {h[4]}</small></div>", unsafe_allow_html=True)
        except: st.error("Base en cours de mise à jour...")
        conn.close()

    if st.sidebar.button("🔌 Déconnexion"):
        st.session_state['connected'] = False; st.rerun()
