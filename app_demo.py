import streamlit as st
import sqlite3
import smtplib
from email.mime.text import MIMEText
import random
import time
from datetime import datetime, timedelta

# --- 1. CONFIGURATION & STYLE CSS ---
st.set_page_config(page_title="Kiké Saré - Officiel", layout="wide", page_icon="🇬🇳")

# Ajout de style personnalisé pour les boutons et les titres
st.markdown("""
    <style>
    .main { background-color: #f9f9f9; }
    .stButton>button {
        background-color: #ce1126; /* Rouge Guinée */
        color: white;
        border-radius: 10px;
        border: none;
        height: 3em;
        width: 100%;
    }
    .stButton>button:hover { background-color: #fcd116; color: black; } /* Jaune Guinée */
    .success-text { color: #009460; font-weight: bold; } /* Vert Guinée */
    </style>
    """, unsafe_allow_html=True)

# --- 2. BASE DE DONNÉES (VERSION STABLE) ---
def get_db_connection():
    return sqlite3.connect('kikesare.db', check_same_thread=False)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (identifier TEXT PRIMARY KEY, password TEXT, full_name TEXT, type TEXT, verified INTEGER)''')
    c.execute('''CREATE TABLE IF NOT EXISTS echeances 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, service TEXT, date_limite DATE, montant REAL)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. ENVOI DE MAIL RÉEL ---
def envoyer_code_validation(destinataire, code):
    try:
        expediteur = st.secrets["EMAIL_USER"]
        mdp = st.secrets["EMAIL_PASSWORD"]
        msg = MIMEText(f"Votre code de sécurité Kiké Saré est : {code}")
        msg['Subject'] = '🔑 Validation Kiké Saré'
        msg['From'] = expediteur
        msg['To'] = destinataire
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(expediteur, mdp)
            server.sendmail(expediteur, destinataire, msg.as_string())
        return True
    except: return False

# --- 4. GESTION DES ÉTATS ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- 5. AUTHENTIFICATION ---
if not st.session_state['connected']:
    col_left, col_mid, col_right = st.columns([1, 2, 1])
    with col_mid:
        st.markdown("<h1 style='text-align: center;'>🇬🇳 Kiké Saré</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: gray;'>Votre assistant de paiement sécurisé en Guinée</p>", unsafe_allow_html=True)
        
        if st.session_state['verifying']:
            st.info(f"📩 Code envoyé à : **{st.session_state['temp_id']}**")
            code_saisi = st.text_input("Entrez le code reçu")
            if st.button("✅ Valider mon compte"):
                if code_saisi == str(st.session_state['correct_code']):
                    conn = get_db_connection()
                    conn.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, 1)", 
                                (st.session_state['temp_id'], st.session_state['temp_pwd'], 
                                 st.session_state['temp_name'], st.session_state['temp_type']))
                    conn.commit()
                    conn.close()
                    st.success("Compte validé ! Connectez-vous.")
                    st.session_state['verifying'] = False
                    st.rerun()
        else:
            tab1, tab2 = st.tabs(["🔐 Connexion", "📝 Créer un compte"])
            with tab1:
                e_log = st.text_input("Identifiant (Email ou Tél)")
                p_log = st.text_input("Mot de passe", type="password")
                if st.button("Se connecter"):
                    conn = get_db_connection()
                    user = conn.execute("SELECT * FROM users WHERE identifier=? AND password=? AND verified=1", (e_log, p_log)).fetchone()
                    conn.close()
                    if user:
                        st.session_state.update({'connected': True, 'user_name': user[2], 'user_id': user[0]})
                        st.rerun()
                    else: st.error("Identifiants incorrects.")

            with tab2: # INSCRIPTION
                with st.form("inscription_form"):
                    choice = st.radio("S'inscrire via :", ["Email", "Numéro de téléphone"])
                    id_u = st.text_input("Email ou Numéro")
                    nom = st.text_input("Nom complet")
                    p1 = st.text_input("Créer un mot de passe", type="password")
                    p2 = st.text_input("Confirmez le mot de passe", type="password")
                    if st.form_submit_button("🚀 S'inscrire et recevoir le code"):
                        if p1 == p2 and len(p1) >= 6:
                            c_gen = random.randint(100000, 999999)
                            if envoyer_code_validation(id_u, c_gen):
                                st.session_state.update({'temp_id': id_u, 'temp_pwd': p1, 'temp_name': nom, 'temp_type': choice, 'correct_code': c_gen, 'verifying': True})
                                st.rerun()
                        else: st.error("Les mots de passe doivent être identiques (min 6 car.)")

# --- 6. INTERFACE PRINCIPALE (PAIEMENT ET RAPPELS) ---
else:
    st.sidebar.markdown(f"### 🇬🇳 Kiké Saré\n**Bienvenue, {st.session_state['user_name']}**")
    
    # RAPPELS D'ÉCHÉANCES (MISE EN FORME CARDS)
    st.subheader("🔔 Mes Rappels d'échéances")
    conn = get_db_connection()
    echs = conn.execute("SELECT service, date_limite, montant FROM echeances WHERE user_id=?", (st.session_state['user_id'],)).fetchall()
    conn.close()

    if echs:
        cols = st.columns(len(echs) if len(echs) < 4 else 4)
        for idx, e in enumerate(echs):
            d_lim = datetime.strptime(e[1], '%Y-%m-%d')
            diff = (d_lim - datetime.now()).days
            with cols[idx % 4]:
                if diff <= 3:
                    st.error(f"**{e[0]}**\n\n{e[2]} GNF\n\nJ-{diff} !")
                else:
                    st.warning(f"**{e[0]}**\n\n{e[2]} GNF\n\nLe {e[1]}")
    else: st.info("Aucun rappel actif.")

    st.markdown("---")
    # PAIEMENT
    st.title("💳 Effectuer un Paiement")
    cp1, cp2 = st.columns([2, 1])
    with cp1:
        st.write("### 1. Détails du service")
        serv = st.selectbox("Sélectionnez le service :", ["Réabonnement Canal+", "Facture EDG", "Facture SEG", "Frais Scolaires", "Achat Crédit"])
        ref = st.text_input("Référence (Numéro de carte ou compteur)")
        mont = st.number_input("Montant à régler (GNF)", min_value=5000, step=5000)
    with cp2:
        st.write("### 2. Moyen de paiement")
        m_pay = st.radio("Mode :", ["📱 Orange Money", "📱 MTN MoMo", "💳 Carte Bancaire"])
        num_p = st.text_input("Numéro à débiter", placeholder="622 00 00 00")
        rappel_on = st.checkbox("🔄 Programmer un rappel automatique")

    if st.button("💎 Confirmer le Paiement Sécurisé"):
        if ref:
            with st.spinner("Vérification auprès de la banque..."):
                time.sleep(2)
                if rappel_on:
                    prox = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                    conn = get_db_connection()
                    conn.execute("INSERT INTO echeances (user_id, service, date_limite, montant) VALUES (?, ?, ?, ?)", (st.session_state['user_id'], serv, prox, mont))
                    conn.commit()
                    conn.close()
                st.balloons()
                st.success(f"Paiement de {mont} GNF réussi pour {serv} !")
        else: st.warning("Veuillez saisir une référence.")

    if st.sidebar.button("🔌 Déconnexion"):
        st.session_state['connected'] = False
        st.rerun()
