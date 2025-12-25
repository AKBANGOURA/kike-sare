import streamlit as st
import sqlite3
import random
import smtplib
from email.message import EmailMessage

# --- 1. CONFIGURATION MAIL (Utilisez un mot de passe d'application Gmail) ---
EMAIL_SENDER = "votre-mail@gmail.com" 
EMAIL_PASSWORD = "votre-mot-de-passe-application" 

def send_validation_mail(receiver, code):
    msg = EmailMessage()
    msg.set_content(f"Bienvenue sur Kiké Saré ! Votre code de validation est : {code}")
    msg['Subject'] = "Validation de votre compte Kiké Saré"
    msg['From'] = EMAIL_SENDER
    msg['To'] = receiver
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception: return False

# --- 2. INITIALISATION ET RÉPARATION AUTOMATIQUE DB ---
def init_db():
    conn = sqlite3.connect('kikesare.db', check_same_thread=False)
    c = conn.cursor()
    # Création de base si la table n'existe pas
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id TEXT PRIMARY KEY, pwd TEXT, name TEXT, type TEXT, verified INT)''')
    
    # RÉPARATION : Ajout dynamique de la colonne siret si elle manque
    try:
        c.execute("ALTER TABLE users ADD COLUMN siret TEXT")
    except sqlite3.OperationalError:
        pass # La colonne existe déjà
        
    conn.commit()
    conn.close()

init_db()

# --- 3. GESTION DES ÉTATS ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- 4. TUNNEL D'ACCÈS (RESTAURATION CONNEXION/INSCRIPTION) ---
if not st.session_state['connected']:
    st.markdown("<h1 style='text-align:center; color:#ce1126;'>KIKÉ SARÉ</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; font-style:italic;'>La Fintech Guinéenne</p>", unsafe_allow_html=True)
    
    if st.session_state['verifying']:
        st.info(f"📩 Code envoyé à : **{st.session_state['temp_id']}**")
        code_s = st.text_input("Saisissez le code de validation")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if st.button("✅ Valider l'inscription"):
                if code_s == str(st.session_state['correct_code']):
                    conn = sqlite3.connect('kikesare.db')
                    conn.execute("INSERT OR REPLACE INTO users (id, pwd, name, type, verified, siret) VALUES (?, ?, ?, ?, 1, ?)", 
                                (st.session_state['temp_id'], st.session_state['temp_pwd'], 
                                 st.session_state['temp_name'], st.session_state['temp_type'], st.session_state.get('temp_siret', '')))
                    conn.commit(); conn.close()
                    st.success("Compte activé ! Connectez-vous."); st.session_state['verifying'] = False; st.rerun()
        with col_v2:
            if st.button("🔄 Renvoyer le code"):
                new_c = random.randint(100000, 999999)
                st.session_state['correct_code'] = new_c
                send_validation_mail(st.session_state['temp_id'], new_c)
                st.toast("Nouveau code envoyé par mail !")

    else:
        # Restauration visuelle des onglets
        tab1, tab2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
        
        with tab1:
            e_log = st.text_input("Identifiant (Email)")
            p_log = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter"):
                conn = sqlite3.connect('kikesare.db')
                u = conn.execute("SELECT * FROM users WHERE id=? AND pwd=? AND verified=1", (e_log, p_log)).fetchone()
                conn.close()
                if u:
                    st.session_state.update({'connected': True, 'user_name': u[2], 'user_id': u[0], 'user_type': u[3]})
                    st.rerun()
                else: 
                    st.error("Identifiants incorrects ou compte non vérifié")

        with tab2:
            u_role = st.radio("Type de compte :", ["Particulier", "Entrepreneur"], horizontal=True)
            with st.form("inscription_form"):
                if u_role == "Particulier":
                    nom_final = f"{st.text_input('Prénom')} {st.text_input('Nom')}"
                    siret_val = ""
                else:
                    nom_final = st.text_input("Nom de l'Entreprise")
                    siret_val = st.text_input("N° SIRET / RCCM")
                
                email_ins = st.text_input("Email de contact")
                p1 = st.text_input("Créer un mot de passe", type="password")
                p2 = st.text_input("Confirmer le mot de passe", type="password")
                
                if st.form_submit_button("🚀 Recevoir le code par mail"):
                    if p1 == p2 and len(p1) >= 6 and email_ins:
                        code = random.randint(100000, 999999)
                        if send_validation_mail(email_ins, code):
                            st.session_state.update({'temp_id': email_ins, 'temp_pwd': p1, 'temp_name': nom_final, 'temp_type': u_role, 'temp_siret': siret_val, 'correct_code': code, 'verifying': True})
                            st.rerun()
                        else: st.error("Échec de l'envoi. Vérifiez vos paramètres SMTP.")

# --- 5. INTERFACES CONNECTÉES ---
else:
    st.sidebar.write(f"### {st.session_state['user_name']}")
    if st.sidebar.button("🔌 Déconnexion"): st.session_state['
