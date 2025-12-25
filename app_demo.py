import streamlit as st
import sqlite3
import random
import time
from datetime import datetime, timedelta
import base64

# --- 1. CONFIGURATION & LOGO ---
st.set_page_config(page_title="Kiké Saré - La Fintech Guinéenne", layout="wide", page_icon="🇬🇳")

# Fonction pour afficher le logo sans avoir besoin de fichier externe (Évite les erreurs)
def display_logo():
    st.markdown(
        f"""
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
    # Table Utilisateurs
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (identifier TEXT PRIMARY KEY, password TEXT, full_name TEXT, type TEXT, verified INTEGER)''')
    # Table Échéances (Paiement 3x - 1er, 5, 10 du mois)
    c.execute('''CREATE TABLE IF NOT EXISTS echeances 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, service TEXT, date_limite DATE, montant REAL)''')
    # Table Historique avec Numéro à débiter
    c.execute('''CREATE TABLE IF NOT EXISTS historique 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, service TEXT, montant REAL, 
                  date_paiement DATETIME, moyen TEXT, reference TEXT, num_debit TEXT)''')
    
    # CORRECTIF : Ajout de la colonne si absente pour stopper l'OperationalError
    try:
        c.execute("SELECT num_debit FROM historique LIMIT 1")
    except sqlite3.OperationalError:
        c.execute("ALTER TABLE historique ADD COLUMN num_debit TEXT")
    
    conn.commit()
    conn.close()

init_db()

# --- 3. AUTHENTIFICATION ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

if not st.session_state['connected']:
    display_logo() # Affichage du logo à l'accueil
    
    if st.session_state['verifying']:
        st.info(f"📩 Code de sécurité envoyé à : **{st.session_state['temp_id']}**")
        code_s = st.text_input("Entrez le code reçu")
        if st.button("✅ Valider l'inscription"):
            if code_s == str(st.session_state['correct_code']):
                conn = get_db_connection()
                conn.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, 1)", 
                            (st.session_state['temp_id'], st.session_state['temp_pwd'], 
                             st.session_state['temp_name'], st.session_state['temp_type']))
                conn.commit()
                conn.close()
                st.success("Compte activé ! Connectez-vous.")
                st.session_state['verifying'] = False
                st.rerun()
    else:
        t1, t2 = st.tabs(["🔐 Connexion", "📝 Inscription Business"])
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
                else: st.error("Accès refusé. Vérifiez vos identifiants.")
        with t2:
            with st.form("signup"):
                id_u = st.text_input("Email ou Téléphone")
                nom = st.text_input("Nom complet / Entreprise")
                p1 = st.text_input("Mot de passe", type="password")
                p2 = st.text_input("Confirmation", type="password")
                if st.form_submit_button("🚀 Créer mon compte Business"):
                    if p1 == p2 and len(p1) >= 6:
                        code = random.randint(100000, 999999)
                        st.session_state.update({'temp_id': id_u, 'temp_pwd': p1, 'temp_name': nom, 'temp_type': "Business", 'correct_code': code, 'verifying': True})
                        st.rerun()

# --- 4. DASHBOARD ENTREPRENEUR ---
else:
    st.sidebar.markdown(f"### 👤 {st.session_state['user_name']}")
    tabs = st.tabs(["📊 Mes Échéances", "💳 Nouveau Paiement", "📜 Historique Complet"])

    # TAB 1 : SUIVI COULEURS (Vert, Jaune, Rouge)
    with tabs[0]:
        st.subheader("🔔 Calendrier des paiements")
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
                    st.markdown(f"<div style='border-left:5px solid {color}; padding:10px; background:#f4f4f4; border-radius:5px;'><b>{e[0]}</b><br>{e[2]} GNF<br>Le {e[1]}</div>", unsafe_allow_html=True)
        else: st.info("Aucun paiement en attente.")

    # TAB 2 : PAIEMENT (LOGIQUE 3X + NUM DEBIT)
    with tabs[1]:
        st.subheader("Effectuer un règlement")
        c1, c2 = st.columns(2)
        with c1:
            serv_map = {"🏠 Frais de loyer": "Frais de loyer", "🛍️ Achat Commerçant": "Achat Commerçant", 
                        "📺 Réabonnement Canal+": "Réabonnement Canal+", "💡 Facture EDG": "Facture EDG"}
            serv_display = st.selectbox("Service", list(serv_map.keys()))
            serv_nom = serv_map[serv_display]
            ref = st.text_input("Référence (Facture/Propriétaire)")
            montant = st.number_input("Montant total (GNF)", min_value=5000)
        with c2:
            moyen = st.radio("Moyen de paiement", ["📱 Orange Money", "📱 MTN MoMo", "💳 Visa/Mastercard"])
            num_debit = st.text_input("📱 Numéro à débiter", placeholder="622 00 00 00")
            can_split = serv_nom in ["Achat Commerçant", "Frais de loyer", "Facture EDG"]
            mode = st.selectbox("Type de règlement", ["Paiement immédiat", "Paiement en 3x (1er, 5, 10 du mois)"] if can_split else ["Paiement immédiat"])
        
        if st.button("💎 Valider la transaction"):
            if ref and num_debit:
                conn = get_db_connection()
                now = datetime.now().strftime('%Y-%m-%d %H:%M')
                # Enregistrement historique immuable
                conn.execute("INSERT INTO historique (user_id, service, montant, date_paiement, moyen, reference, num_debit) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                            (st.session_state['user_id'], serv_nom, montant, now, moyen, ref, num_debit))
                
                if "3x" in mode:
                    m_suiv = (datetime.now().replace(day=28) + timedelta(days=4)).replace(day=1)
                    for d in ["01", "05", "10"]:
                        conn.execute("INSERT INTO echeances (user_id, service, date_limite, montant) VALUES (?, ?, ?, ?)", 
                                    (st.session_state['user_id'], f"Partiel: {serv_nom}", m_suiv.strftime(f'%Y-%m-{d}'), montant/3))
                conn.commit(); conn.close()
                st.balloons(); st.success("Paiement validé et enregistré.")
            else: st.warning("Veuillez remplir la référence et le numéro de téléphone.")

    # TAB 3 : HISTORIQUE (SÉCURISÉ CONTRE OPERATIONAL ERROR)
    with tabs[2]:
        st.subheader("📜 Historique de vos activités")
        conn = get_db_connection()
        try:
            hist = conn.execute("SELECT service, montant, date_paiement, reference, num_debit FROM historique WHERE user_id=? ORDER BY date_paiement DESC", (st.session_state['user_id'],)).fetchall()
            for h in hist:
                st.markdown(f"<div style='border-bottom:1px solid #eee; padding:10px;'><b>{h[2]}</b> | {h[0]} - {h[1]} GNF<br><small>Réf: {h[3]} | Débité de: {h[4]}</small></div>", unsafe_allow_html=True)
        except: st.error("Mise à jour de la base en cours...")
        conn.close()

    if st.sidebar.button("🔌 Déconnexion"):
        st.session_state['connected'] = False; st.rerun()
