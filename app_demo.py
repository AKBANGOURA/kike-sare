import streamlit as st
import sqlite3
import smtplib
from email.mime.text import MIMEText
import random
import time
from datetime import datetime, timedelta

# --- CONFIGURATION ---
st.set_page_config(page_title="Kiké Saré - Gestion & Rappels", layout="wide", page_icon="🇬🇳")

# --- INITIALISATION SQL (AVEC TABLE ÉCHÉANCES) ---
def init_db():
    conn = sqlite3.connect('kikesare.db')
    c = conn.cursor()
    # Table Utilisateurs
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (identifier TEXT PRIMARY KEY, password TEXT, full_name TEXT, type TEXT, verified INTEGER)''')
    # Table Échéances (Nouveau)
    c.execute('''CREATE TABLE IF NOT EXISTS echeances 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, service TEXT, date_limite DATE, montant REAL)''')
    conn.commit()
    conn.close()

init_db()

# --- FONCTION D'ENVOI DE MAIL ---
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

# --- LOGIQUE DE SESSION ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- PARTIE 1 : AUTHENTIFICATION ---
if not st.session_state['connected']:
    st.markdown("<h1 style='text-align: center;'>🇬🇳 Bienvenue sur Kiké Saré</h1>", unsafe_allow_html=True)
    
    if st.session_state['verifying']:
        st.info(f"📩 Code envoyé à : **{st.session_state['temp_id']}**")
        code_saisi = st.text_input("Entrez le code")
        if st.button("Valider"):
            if code_saisi == str(st.session_state['correct_code']):
                conn = sqlite3.connect('kikesare.db')
                c = conn.cursor()
                c.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, 1)", 
                          (st.session_state['temp_id'], st.session_state['temp_pwd'], 
                           st.session_state['temp_name'], st.session_state['temp_type']))
                conn.commit()
                conn.close()
                st.success("Compte validé !")
                st.session_state['verifying'] = False
                st.rerun()
    else:
        t1, t2 = st.tabs(["Connexion", "Créer un compte"])
        with t2:
            with st.form("inscription"):
                id_u = st.text_input("Email ou Téléphone")
                nom = st.text_input("Nom complet")
                p1 = st.text_input("Mot de passe", type="password")
                p2 = st.text_input("Confirmez", type="password")
                if st.form_submit_button("S'inscrire"):
                    if p1 == p2 and len(p1) >= 6:
                        code = random.randint(100000, 999999)
                        if envoyer_code_validation(id_u, code):
                            st.session_state.update({'temp_id': id_u, 'temp_pwd': p1, 'temp_name': nom, 'temp_type': "Email", 'correct_code': code, 'verifying': True})
                            st.rerun()
        with t1:
            email_log = st.text_input("Identifiant")
            pass_log = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter"):
                conn = sqlite3.connect('kikesare.db')
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE identifier=? AND password=? AND verified=1", (email_log, pass_log))
                user = c.fetchone()
                conn.close()
                if user:
                    st.session_state['connected'] = True
                    st.session_state['user_name'] = user[2]
                    st.session_state['user_id'] = user[0]
                    st.rerun()

# --- PARTIE 2 : INTERFACE PRINCIPALE + ÉCHÉANCES ---
else:
    st.sidebar.title("🇬🇳 Kiké Saré")
    st.sidebar.write(f"Utilisateur : **{st.session_state['user_name']}**")
    
    # 1. RÉSUMÉ DES ÉCHÉANCES (RAPPEL)
    st.subheader("🔔 Mes Rappels d'échéances")
    conn = sqlite3.connect('kikesare.db')
    echeances = conn.execute("SELECT service, date_limite, montant FROM echeances WHERE user_id=?", (st.session_state['user_id'],)).fetchall()
    conn.close()

    if echeances:
        for ech in echeances:
            date_obj = datetime.strptime(ech[1], '%Y-%m-%d')
            jours_restants = (date_obj - datetime.now()).days
            if jours_restants <= 3:
                st.error(f"⚠️ **{ech[0]}** : {ech[2]} GNF à payer avant le {ech[1]} (J-{jours_restants}) !")
            else:
                st.warning(f"📅 **{ech[0]}** : Échéance le {ech[1]}")
    else:
        st.info("Aucune échéance enregistrée pour le moment.")

    st.markdown("---")

    # 2. INTERFACE DE PAIEMENT
    st.title("💳 Effectuer un Paiement")
    col1, col2 = st.columns(2)
    with col1:
        serv = st.selectbox("Service", ["Canal+", "EDG", "SEG", "Scolarité"])
        ref = st.text_input("Référence client")
        mont = st.number_input("Montant (GNF)", min_value=1000)
    with col2:
        mode = st.radio("Moyen", ["Orange Money", "MTN MoMo", "Carte"])
        rappel = st.checkbox("M'ajouter un rappel pour le mois prochain ?")

    if st.button("Confirmer le paiement", use_container_width=True):
        with st.spinner("Paiement en cours..."):
            time.sleep(2)
            # Si l'utilisateur a coché le rappel, on l'ajoute en base
            if rappel:
                prochaine_date = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                conn = sqlite3.connect('kikesare.db')
                conn.execute("INSERT INTO echeances (user_id, service, date_limite, montant) VALUES (?, ?, ?, ?)", 
                             (st.session_state['user_id'], serv, prochaine_date, mont))
                conn.commit()
                conn.close()
            st.balloons()
            st.success("Paiement validé et rappel enregistré !")
