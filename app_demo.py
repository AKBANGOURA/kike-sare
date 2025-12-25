import streamlit as st
import sqlite3
import os
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Kiké Saré - Business", layout="wide", page_icon="🇬🇳")

# --- 2. GESTION DE LA BASE DE DONNÉES (CORRECTIF) ---
def get_db_connection():
    return sqlite3.connect('kikesare.db', check_same_thread=False)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # Création des tables de base
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (identifier TEXT PRIMARY KEY, password TEXT, full_name TEXT, type TEXT, verified INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS echeances 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, service TEXT, date_limite DATE, montant REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS historique 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, service TEXT, montant REAL, date_paiement DATETIME, moyen TEXT, reference TEXT, num_debit TEXT)''')
    
    # --- RÉPARATION : Vérifier si la colonne num_debit existe (évite OperationalError) ---
    try:
        c.execute("SELECT num_debit FROM historique LIMIT 1")
    except sqlite3.OperationalError:
        st.warning("Mise à jour de la base de données...")
        c.execute("ALTER TABLE historique ADD COLUMN num_debit TEXT")
    
    conn.commit()
    conn.close()

init_db()

# --- 3. AUTHENTIFICATION (BASE IMMUABLE) ---
if 'connected' not in st.session_state: st.session_state['connected'] = False

if not st.session_state['connected']:
    st.markdown("<h1 style='color: #ce1126; text-align: center;'>KIKÉ SARÉ</h1>", unsafe_allow_html=True)
    tab1, tab2 = st.tabs(["Connexion", "Inscription"])
    
    with tab1:
        e_log = st.text_input("Identifiant")
        p_log = st.text_input("Mot de passe", type="password")
        if st.button("Se connecter"):
            conn = get_db_connection()
            user = conn.execute("SELECT * FROM users WHERE identifier=? AND password=? AND verified=1", (e_log, p_log)).fetchone()
            conn.close()
            if user:
                st.session_state.update({'connected': True, 'user_name': user[2], 'user_id': user[0]})
                st.rerun()
            else: st.error("Identifiants incorrects.")

# --- 4. INTERFACE PRINCIPALE ---
else:
    st.sidebar.write(f"Utilisateur : {st.session_state['user_name']}")
    t_dash, t_pay, t_hist = st.tabs(["📊 Échéances", "💳 Paiement", "📜 Historique"])

    with t_pay:
        st.subheader("Nouveau Paiement")
        serv = st.selectbox("Service", ["🏠 Frais de loyer", "🛍️ Achat Commerçant", "💡 Facture EDG", "💧 Facture SEG"])
        ref = st.text_input("Référence")
        montant = st.number_input("Montant (GNF)", min_value=5000)
        num_debit = st.text_input("📱 Numéro à débiter (OM/MoMo)") # RÉTABLI
        
        if st.button("Valider le paiement"):
            if ref and num_debit:
                conn = get_db_connection()
                now = datetime.now().strftime('%Y-%m-%d %H:%M')
                # Insertion avec num_debit
                conn.execute("INSERT INTO historique (user_id, service, montant, date_paiement, moyen, reference, num_debit) VALUES (?, ?, ?, ?, ?, ?, ?)",
                            (st.session_state['user_id'], serv, montant, now, "Mobile Money", ref, num_debit))
                conn.commit()
                conn.close()
                st.success("Paiement enregistré !")
            else: st.warning("Champs manquants.")

    with t_hist:
        st.subheader("Historique des transactions")
        conn = get_db_connection()
        # La requête qui crashait est maintenant sécurisée
        try:
            hist = conn.execute("SELECT service, montant, date_paiement, moyen, reference, num_debit FROM historique WHERE user_id=? ORDER BY date_paiement DESC", (st.session_state['user_id'],)).fetchall()
            for h in hist:
                st.write(f"📅 {h[2]} | **{h[0]}** | {h[1]} GNF | Réf: {h[4]} (Débit: {h[5]})")
        except Exception as e:
            st.error(f"Erreur d'affichage : {e}")
        conn.close()

    if st.sidebar.button("Déconnexion"):
        st.session_state['connected'] = False
        st.rerun()
