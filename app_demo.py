import streamlit as st
import sqlite3
import smtplib
from email.mime.text import MIMEText
import random
import time

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Kiké Saré - Production", layout="wide", page_icon="🇬🇳")

# --- INITIALISATION BASE DE DONNÉES (SQL REAL) ---
def init_db():
    conn = sqlite3.connect('kikesare.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (email TEXT PRIMARY KEY, password TEXT, full_name TEXT, verified INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- FONCTION D'ENVOI DE MAIL RÉEL ---
def envoyer_mail_validation(destinataire, code):
    try:
        # Récupération sécurisée depuis les Secrets configurés sur Streamlit Cloud
        expediteur = st.secrets["EMAIL_USER"] 
        mot_de_passe = st.secrets["EMAIL_PASSWORD"] 
        
        msg = MIMEText(f"Votre code de validation Kiké Saré est : {code}")
        msg['Subject'] = '🔑 Code de sécurité Kiké Saré'
        msg['From'] = expediteur
        msg['To'] = destinataire

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(expediteur, mot_de_passe)
            server.sendmail(expediteur, destinataire, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Erreur d'envoi : {e}")
        return False

# --- GESTION DE LA SESSION ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- INTERFACE UTILISATEUR ---
if not st.session_state['connected']:
    st.markdown("<h1 style='text-align: center;'>🇬🇳 Bienvenue sur Kiké Saré</h1>", unsafe_allow_html=True)
    
    # ÉCRAN DE VÉRIFICATION DU CODE
    if st.session_state['verifying']:
        st.info(f"📩 Un code a été envoyé à : **{st.session_state['temp_email']}**")
        
        code_saisi = st.text_input("Entrez le code reçu par mail", placeholder="Ex: 123456")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("Valider mon compte"):
                if code_saisi == str(st.session_state['correct_code']):
                    # Enregistrement final en base de données
                    conn = sqlite3.connect('kikesare.db')
                    c = conn.cursor()
                    c.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, 1)", 
                              (st.session_state['temp_email'], st.session_state['temp_pwd'], st.session_state['temp_name']))
                    conn.commit()
                    conn.close()
                    st.success("Compte validé ! Vous pouvez vous connecter.")
                    st.session_state['verifying'] = False
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Code incorrect.")
        
        with col2:
            if st.button("🔄 Renvoyer le code"):
                nouveau_code = random.randint(100000, 999999)
                if envoyer_mail_validation(st.session_state['temp_email'], nouveau_code):
                    st.session_state['correct_code'] = nouveau_code
                    st.toast("Un nouveau code a été envoyé !")
                else:
                    st.error("Échec du renvoi.")

    # ÉCRAN D'INSCRIPTION / CONNEXION
    else:
        tab1, tab2 = st.tabs(["Connexion", "Créer un compte"])
        
        with tab2:
            with st.form("form_inscription"):
                new_email = st.text_input("Email (Saisissez votre vrai mail)")
                new_name = st.text_input("Nom complet")
                new_pwd = st.text_input("Mot de passe", type="password")
                submit = st.form_submit_button("S'inscrire")
                
                if submit:
                    if "@" in new_email and len(new_pwd) > 4:
                        code_genere = random.randint(100000, 999999)
                        if envoyer_mail_validation(new_email, code_genere):
                            st.session_state['temp_email'] = new_email
                            st.session_state['temp_name'] = new_name
                            st.session_state['temp_pwd'] = new_pwd
                            st.session_state['correct_code'] = code_genere
                            st.session_state['verifying'] = True
                            st.rerun()
                    else:
                        st.warning("Veuillez entrer un email valide et un mot de passe de plus de 4 caractères.")

        with tab1:
            # Code de connexion simplifié pour la démo
            email_log = st.text_input("Email")
            pwd_log = st.text_input("Mot de passe", type="password", key="login_pwd")
            if st.button("Se connecter"):
                conn = sqlite3.connect('kikesare.db')
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE email=? AND password=? AND verified=1", (email_log, pwd_log))
                user = c.fetchone()
                conn.close()
                if user:
                    st.session_state['connected'] = True
                    st.session_state['user_name'] = user[2]
                    st.rerun()
                else:
                    st.error("Identifiants incorrects ou compte non vérifié.")

# APPLICATION PRINCIPALE (APPRÈS CONNEXION)
else:
    st.sidebar.success(f"Connecté : {st.session_state['user_name']}")
    if st.sidebar.button("Déconnexion"):
        st.session_state['connected'] = False
        st.rerun()
        
    st.title("💳 Plateforme de Paiement Kiké Saré")
    # Ajoutez ici votre formulaire de paiement réel
