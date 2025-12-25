import streamlit as st
import sqlite3
import random
from datetime import datetime, timedelta
import os

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
    # Table utilisateurs avec type de compte et photo
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

# --- 4. ACCÈS & INSCRIPTION ---
if not st.session_state['connected']:
    display_logo()
    
    if st.session_state['verifying']:
        st.info(f"📩 Code envoyé à : **{st.session_state['temp_id']}**")
        code_s = st.text_input("Code de validation")
        if st.button("✅ Valider mon compte"):
            if code_s == str(st.session_state['correct_code']):
                conn = get_db_connection()
                conn.execute("INSERT OR REPLACE INTO users (identifier, password, full_name, type, verified) VALUES (?, ?, ?, ?, 1)", 
                            (st.session_state['temp_id'], st.session_state['temp_pwd'], 
                             st.session_state['temp_name'], st.session_state['temp_type']))
                conn.commit(); conn.close()
                st.success("Compte validé ! Connectez-vous.")
                st.session_state['verifying'] = False; st.rerun()
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
                # CHOIX DU PROFIL [Action demandée]
                u_type = st.radio("Type de compte :", ["Particulier", "Entrepreneur (École, Loyer, Commerce)"])
                p1 = st.text_input("Mot de passe", type="password")
                p2 = st.text_input("Confirmer le mot de passe", type="password")
                
                if st.form_submit_button("🚀 S'inscrire"):
                    if p1 == p2 and len(p1) >= 6:
                        code = random.randint(100000, 999999)
                        st.session_state.update({'temp_id': new_id, 'temp_pwd': p1, 'temp_name': new_name, 'temp_type': u_type, 'correct_code': code, 'verifying': True})
                        st.rerun()
                    else: st.error("Erreur : Mots de passe non identiques ou trop courts.")

# --- 5. ESPACES UTILISATEURS ---
else:
    # Barre latérale commune avec photo de profil
    with st.sidebar:
        conn = get_db_connection()
        user_pic = conn.execute("SELECT profile_pic FROM users WHERE identifier=?", (st.session_state['user_id'],)).fetchone()
        conn.close()
        if user_pic and user_pic[0]: st.image(user_pic[0], width=100)
        else: st.image("https://www.w3schools.com/howto/img_avatar.png", width=100)
        
        st.write(f"### {st.session_state['user_name']}")
        st.info(f"Rôle : {st.session_state['user_type']}")
        
        new_pic = st.file_uploader("Changer ma photo", type=['png', 'jpg'])
        if new_pic:
            conn = get_db_connection()
            conn.execute("UPDATE users SET profile_pic=? WHERE identifier=?", (new_pic.getvalue(), st.session_state['user_id']))
            conn.commit(); conn.close(); st.rerun()

        if st.button("🔌 Déconnexion"):
            st.session_state['connected'] = False; st.rerun()

    # --- ESPACE PARTICULIER ---
    if st.session_state['user_type'] == "Particulier":
        t_ech, t_pay, t_hist = st.tabs(["📊 Mes Échéances", "💳 Payer un Service", "📜 Historique"])
        
        with t_pay:
            st.subheader("Nouveau paiement")
            col1, col2 = st.columns(2)
            with col1:
                serv = st.selectbox("Service", ["🎓 Frais de scolarité", "🏠 Frais de loyer", "🛍️ Achat Commerçant", "💡 Facture EDG"])
                ref = st.text_input("Référence (N° Facture/Étudiant)")
                montant = st.number_input("Montant (GNF)", min_value=5000)
                mode = st.selectbox("Modalité", ["Comptant", "2 fois (5 et 20)", "3 fois (5, 15, 25)"])
            with col2:
                moyen = st.radio("Moyen de paiement", ["📱 Orange Money", "📱 MTN MoMo", "💳 Carte Visa"])
                info_p = ""
                if moyen == "💳 Carte Visa":
                    nc = st.text_input("N° de Carte")
                    nomc = st.text_input("Nom sur la carte")
                    cv = st.columns(2)
                    cv[0].text_input("Exp (MM/AA)")
                    cv[1].text_input("CVV", type="password")
                    if nc: info_p = f"Visa: ****{nc[-4:]}"
                else:
                    info_p = st.text_input("📱 Numéro à débiter")
            
            if st.button("💎 Valider le paiement"):
                if ref and info_p:
                    conn = get_db_connection()
                    now = datetime.now().strftime('%Y-%m-%d %H:%M')
                    conn.execute("INSERT INTO historique (user_id, service, montant, date_paiement, moyen, reference, num_debit) VALUES (?, ?, ?, ?, ?, ?, ?)", 
                                (st.session_state['user_id'], serv, montant, now, moyen, ref, info_p))
                    # Logique échéances (5, 15, 25 ou 5, 20)
                    if "fois" in mode:
                        m_suiv = (datetime.now().replace(day=28) + timedelta(days=4)).replace(day=1)
                        dates = ["05", "15", "25"] if "3" in mode else ["05", "20"]
                        for d in dates:
                            conn.execute("INSERT INTO echeances (user_id, service, date_limite, montant) VALUES (?, ?, ?, ?)", 
                                        (st.session_state['user_id'], f"Echéance {serv}", m_suiv.strftime(f'%Y-%m-{d}'), montant/(3 if "3" in mode else 2)))
                    conn.commit(); conn.close(); st.balloons(); st.success("Paiement enregistré !")

    # --- ESPACE ENTREPRENEUR ---
    else:
        st.title("💼 Espace Gestion Entrepreneur")
        tb1, tb2 = st.tabs(["📈 Tableau de bord", "👥 Suivi Clients"])
        
        with tb1:
            st.subheader("Vos Statistiques d'encaissements")
            c_ent1, c_ent2 = st.columns(2)
            c_ent1.metric("Volume de transactions", "0 GNF")
            c_ent2.metric("Paiements prévus (Échéances)", "0 GNF")
            
            st.info("Ici vous verrez l'évolution de vos revenus mensuels.")

        with tb2:
            st.subheader("Liste des paiements reçus par vos clients")
            st.write("Aucune donnée disponible pour le moment.")
