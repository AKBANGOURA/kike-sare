import streamlit as st
import sqlite3
import random
from datetime import datetime, timedelta
import os

# --- 1. CONFIGURATION & LOGO ---
st.set_page_config(page_title="Kiké Saré - Business Pro", layout="wide", page_icon="🇬🇳")

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
    c.execute('''CREATE TABLE IF NOT EXISTS users (identifier TEXT PRIMARY KEY, password TEXT, full_name TEXT, type TEXT, verified INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS echeances (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, service TEXT, date_limite DATE, montant REAL)''')
    c.execute('''CREATE TABLE IF NOT EXISTS historique (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, service TEXT, montant REAL, date_paiement DATETIME, moyen TEXT, reference TEXT, num_debit TEXT)''')
    conn.commit()
    conn.close()

init_db()

if 'connected' not in st.session_state: st.session_state['connected'] = False

# --- 3. ACCÈS ---
if not st.session_state['connected']:
    display_logo()
    t1, t2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
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

# --- 4. INTERFACE PRINCIPALE ---
else:
    st.sidebar.write(f"👤 {st.session_state['user_name']}")
    tabs = st.tabs(["📊 Échéances", "💳 Paiement", "📜 Historique"])

    with tabs[1]:
        st.subheader("Nouvelle transaction")
        
        # Structure en colonnes pour le formulaire
        c1, c2 = st.columns(2)
        
        with c1:
            serv_list = ["🎓 Frais de scolarité", "🏠 Frais de loyer", "🛍️ Achat Commerçant", "💡 Facture EDG", "📺 Canal+"]
            serv_display = st.selectbox("Service", serv_list)
            ref = st.text_input("Référence (N° Facture/Étudiant)")
            montant = st.number_input("Montant (GNF)", min_value=5000)
            
            # Gestion des modalités (2x, 3x)
            can_split = any(x in serv_display for x in ["scolarité", "loyer", "Commerçant", "EDG"])
            mode = st.selectbox("Modalité", ["Comptant", "2 fois (5 et 20)", "3 fois (5, 15, 25)"] if can_split else ["Comptant"])

        with c2:
            # Sélection du moyen de paiement
            moyen = st.radio("Moyen de paiement", ["📱 Orange Money", "📱 MTN MoMo", "💳 Carte Visa"])
            
            # --- LOGIQUE DYNAMIQUE DES CHAMPS ---
            info_final = ""
            if moyen == "💳 Carte Visa":
                st.info("💳 Renseignez les détails de votre carte")
                num_card = st.text_input("Numéro de carte", placeholder="4000 1234 5678 9010")
                nom_card = st.text_input("Nom sur la carte")
                cv1, cv2 = st.columns(2)
                exp_card = cv1.text_input("Expiration (MM/AA)")
                cvv_card = cv2.text_input("CVV", type="password", help="3 chiffres au dos")
                # On stocke une version masquée pour l'historique
                if num_card: info_final = f"Visa: ****{num_card[-4:]}"
            else:
                # Champs pour Mobile Money (Orange/MTN)
                num_momo = st.text_input("📱 Numéro à débiter", placeholder="622 00 00 00")
                info_final = num_momo

        st.markdown("---")
        if st.button("💎 Valider le Règlement"):
            if ref and info_final:
                conn = get_db_connection()
                now = datetime.now().strftime('%Y-%m-%d %H:%M')
                
                # Sauvegarde historique
                conn.execute("INSERT INTO historique (user_id, service, montant, date_paiement, moyen, reference, num_debit) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                            (st.session_state['user_id'], serv_display, montant, now, moyen, ref, info_final))
                
                # Logique des dates (5, 15, 25 ou 5, 20)
                if "fois" in mode:
                    m_suiv = (datetime.now().replace(day=28) + timedelta(days=4)).replace(day=1)
                    dates_list = ["05", "15", "25"] if "3" in mode else ["05", "20"]
                    div = 3 if "3" in mode else 2
                    for d in dates_list:
                        conn.execute("INSERT INTO echeances (user_id, service, date_limite, montant) VALUES (?, ?, ?, ?)", 
                                    (st.session_state['user_id'], f"Partiel: {serv_display}", m_suiv.strftime(f'%Y-%m-{d}'), montant/div))
                
                conn.commit(); conn.close()
                st.balloons(); st.success("Transaction effectuée avec succès !")
            else:
                st.error("❌ Erreur : Veuillez remplir les informations de paiement (Numéro ou détails Carte).")

    # Onglets Échéances et Historique (Conservés sans changement)
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
                    st.markdown(f"<div style='border-left:5px solid {color}; padding:10px; background:#f9f9f9; border-radius:5px;'><b>{e[0]}</b><br>{e[2]} GNF<br>Le {e[1]}</div>", unsafe_allow_html=True)

    with tabs[2]:
        st.subheader("📜 Historique")
        conn = get_db_connection()
        hist = conn.execute("SELECT service, montant, date_paiement, reference, num_debit FROM historique WHERE user_id=? ORDER BY date_paiement DESC", (st.session_state['user_id'],)).fetchall()
        conn.close()
        for h in hist:
            st.markdown(f"<div style='border-bottom:1px solid #eee; padding:10px;'><b>{h[2]}</b> | {h[0]} : {h[1]} GNF<br><small>Réf : {h[3]} | Source : {h[4]}</small></div>", unsafe_allow_html=True)

    if st.sidebar.button("🔌 Déconnexion"):
        st.session_state['connected'] = False; st.rerun()
