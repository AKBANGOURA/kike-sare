import streamlit as st
import sqlite3
import smtplib
from email.mime.text import MIMEText
import random
import time
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ET STYLE ---
st.set_page_config(page_title="Kiké Saré - Version Intégrale", layout="wide", page_icon="🇬🇳")

# --- 2. BASE DE DONNÉES (SQL AUTOMATISÉ) ---
# Cette fonction règle l'erreur sqlite3.OperationalError
def get_db_connection():
    conn = sqlite3.connect('kikesare.db', check_same_thread=False)
    return conn

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    # Table Utilisateurs
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (identifier TEXT PRIMARY KEY, password TEXT, full_name TEXT, type TEXT, verified INTEGER)''')
    # Table Rappels Échéances
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
    except Exception as e:
        st.error(f"Erreur d'envoi : {e}")
        return False

# --- 4. GESTION DE LA SESSION ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- 5. INTERFACE D'AUTHENTIFICATION ---
if not st.session_state['connected']:
    st.markdown("<h1 style='text-align: center;'>🇬🇳 Bienvenue sur Kiké Saré</h1>", unsafe_allow_html=True)
    
    if st.session_state['verifying']:
        st.info(f"📩 Code envoyé à : **{st.session_state['temp_id']}**")
        code_saisi = st.text_input("Entrez le code reçu")
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if st.button("✅ Valider mon compte", use_container_width=True):
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
        with col_v2:
            if st.button("🔄 Renvoyer le code", use_container_width=True):
                nouveau = random.randint(100000, 999999)
                if envoyer_code_validation(st.session_state['temp_id'], nouveau):
                    st.session_state['correct_code'] = nouveau
                    st.toast("Nouveau code envoyé !")

    else:
        tab1, tab2 = st.tabs(["🔐 Connexion", "📝 Créer un compte"])
        
        with tab1: # CONNEXION
            email_log = st.text_input("Identifiant (Email ou Téléphone)")
            pwd_log = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter", use_container_width=True):
                conn = get_db_connection()
                user = conn.execute("SELECT * FROM users WHERE identifier=? AND password=? AND verified=1", (email_log, pwd_log)).fetchone()
                conn.close()
                if user:
                    st.session_state.update({'connected': True, 'user_name': user[2], 'user_id': user[0]})
                    st.rerun()
                else:
                    st.error("Identifiants incorrects ou compte non vérifié.")

        with tab2: # INSCRIPTION COMPLÈTE
            with st.form("inscription_form"):
                st.write("Choisissez votre mode d'inscription")
                t_insc = st.radio("S'inscrire via :", ["Email", "Numéro de téléphone"])
                id_u = st.text_input("Votre Email ou Numéro (ex: 622...)")
                nom = st.text_input("Nom complet")
                p1 = st.text_input("Créer un mot de passe", type="password")
                p2 = st.text_input("Confirmez le mot de passe", type="password")
                
                if st.form_submit_button("🚀 S'inscrire"):
                    if p1 != p2: st.error("Les mots de passe ne correspondent pas.")
                    elif len(p1) < 6: st.error("Le mot de passe doit faire 6 caractères minimum.")
                    elif not id_u or not nom: st.error("Veuillez remplir tous les champs.")
                    else:
                        c_gen = random.randint(100000, 999999)
                        if envoyer_code_validation(id_u, c_gen):
                            st.session_state.update({'temp_id': id_u, 'temp_pwd': p1, 'temp_name': nom, 'temp_type': t_insc, 'correct_code': c_gen, 'verifying': True})
                            st.rerun()

# --- 6. INTERFACE PRINCIPALE (PAIEMENT ET RAPPELS) ---
else:
    st.sidebar.title("💳 Kiké Saré Pay")
    st.sidebar.success(f"Utilisateur : {st.session_state['user_name']}")
    
    # --- SECTION RAPPELS D'ÉCHÉANCES ---
    st.subheader("🔔 Mes Rappels d'échéances")
    conn = get_db_connection()
    echs = conn.execute("SELECT service, date_limite, montant FROM echeances WHERE user_id=?", (st.session_state['user_id'],)).fetchall()
    conn.close()

    if echs:
        for e in echs:
            d_lim = datetime.strptime(e[1], '%Y-%m-%d')
            diff = (d_lim - datetime.now()).days
            if diff <= 3: st.error(f"⚠️ **{e[0]}** : Payez {e[2]} GNF avant le {e[1]} (J-{diff})")
            else: st.warning(f"📅 **{e[0]}** : Échéance le {e[1]}")
    else: st.info("Aucun rappel. Payez une facture pour en activer un.")

    st.markdown("---")

    # --- SECTION PAIEMENT DYNAMIQUE ---
    st.title("💳 Effectuer un Paiement")
    cp1, cp2 = st.columns([2, 1])
    
    with cp1:
        st.subheader("Détails")
        serv = st.selectbox("Service :", ["Réabonnement Canal+", "Facture EDG", "Facture SEG", "Frais Scolaires", "Achat Crédit"])
        ref = st.text_input("Référence (Numéro de carte ou compteur)")
        mont = st.number_input("Montant (GNF)", min_value=5000, step=5000)

    with cp2:
        st.subheader("Paiement")
        m_pay = st.radio("Moyen :", ["📱 Orange Money", "📱 MTN MoMo", "💳 Carte Bancaire"])
        num_p = st.text_input("Numéro à débiter", placeholder="622...")
        rappel_on = st.checkbox("🔄 Me rappeler dans 1 mois")

    if st.button("💎 Confirmer le Paiement", use_container_width=True):
        if not ref: st.warning("Veuillez entrer une référence.")
        else:
            with st.spinner("Transaction en cours..."):
                time.sleep(2)
                if rappel_on:
                    prox = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                    conn = get_db_connection()
                    conn.execute("INSERT INTO echeances (user_id, service, date_limite, montant) VALUES (?, ?, ?, ?)", (st.session_state['user_id'], serv, prox, mont))
                    conn.commit()
                    conn.close()
                st.balloons()
                st.success(f"Paiement réussi pour {serv} !")

    if st.sidebar.button("🔌 Déconnexion"):
        st.session_state['connected'] = False
        st.rerun()
