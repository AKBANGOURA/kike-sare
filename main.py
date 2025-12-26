import streamlit as st
import sqlite3
import random
import smtplib
import time
from email.message import EmailMessage

# --- 1. CONFIGURATION DE LA PAGE & ICONE NAVIGATEUR ---
st.set_page_config(
    page_title="KikéSaré",
    page_icon="logo.png", # Utilise le fichier local s'il est dans le dossier
    layout="centered"
)

# --- 2. LIEN DIRECT VERS VOTRE LOGO GITHUB (POUR MOBILE) ---
direct_url = "https://raw.githubusercontent.com/AKBANGOURA/kike-sare/main/logo.png"

# --- 3. PERSONNALISATION DE L'INTERFACE (CSS/HTML) ---
st.markdown(
    f"""
    <head>
        <link rel="apple-touch-icon" href="{direct_url}">
        <link rel="icon" href="{direct_url}">
        <meta name="apple-mobile-web-app-title" content="Kiké Saré">
        <meta name="apple-mobile-web-app-capable" content="yes">
    </head>
    <style>
        header {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        #MainMenu {{visibility: hidden;}}
        .stAppDeployButton {{display:none;}}
        .block-container {{ padding-top: 1rem; }}
    </style>
    """,
    unsafe_allow_html=True
)

# --- 4. CONFIGURATION MAIL ---
EMAIL_SENDER = "bangourakallaa@gmail.com" 
EMAIL_PASSWORD = "tyqlqacsgwpoeiin" 

def send_validation_mail(receiver, code):
    msg = EmailMessage()
    msg.set_content(f"Bienvenue sur KikéSaré ! Votre code de validation est : {code}")
    msg['Subject'] = "Validation de compte - KikéSaré"
    msg['From'] = EMAIL_SENDER
    msg['To'] = receiver
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception: return False

# --- 5. BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('kikesare.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id TEXT PRIMARY KEY, pwd TEXT, name TEXT, type TEXT, verified INT, siret TEXT)''')
    conn.commit(); conn.close()

init_db()

# --- 6. ÉTAT DE LA SESSION ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- 7. AFFICHAGE DE L'EN-TÊTE AVEC VOTRE LOGO GITHUB ---
def display_header():
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.image(direct_url, width=150) # Affiche votre logo GitHub
    st.markdown(f"""
        <h1 style='color:#ce1126; margin-top:0px; margin-bottom:0;'>KikéSaré</h1>
        <p style='color:#009460; font-weight:bold; font-size:20px; margin-bottom:0;'>L'argent au service de votre avenir</p>
        <p style='color:#666; font-style: italic;'>Payez vos mensualités en toute sécurité !</p>
        <hr style='border: 0.5px solid #eee; width: 80%; margin: 20px auto;'>
        </div>
    """, unsafe_allow_html=True)

# --- 8. LOGIQUE D'ACCÈS (CONNEXION & INSCRIPTION) ---
if not st.session_state['connected']:
    display_header()
    
    if st.session_state['verifying']:
        st.info(f"📩 Code envoyé à : **{st.session_state['temp_id']}**")
        code_s = st.text_input("Saisissez le code de validation reçu")
        if st.button("✅ Valider l'inscription"):
            if code_s == str(st.session_state['correct_code']):
                conn = sqlite3.connect('kikesare.db')
                conn.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, 1, ?)", 
                            (st.session_state['temp_id'], st.session_state['temp_pwd'], 
                             st.session_state['temp_name'], st.session_state['temp_type'], st.session_state.get('temp_siret', '')))
                conn.commit(); conn.close()
                st.success("Compte activé !"); st.session_state['verifying'] = False; st.rerun()
    else:
        tab1, tab2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
        with tab1:
            e_log = st.text_input("Email", key="l_email")
            p_log = st.text_input("Mot de passe", type="password", key="l_pwd")
            if st.button("Se connecter", use_container_width=True):
                conn = sqlite3.connect('kikesare.db')
                u = conn.execute("SELECT * FROM users WHERE id=? AND pwd=? AND verified=1", (e_log, p_log)).fetchone()
                conn.close()
                if u:
                    st.session_state.update({'connected': True, 'user_name': u[2], 'user_id': u[0], 'user_type': u[3]})
                    st.rerun()
                else: st.error("Identifiants incorrects.")

        with tab2:
            u_role = st.radio("Type de compte :", ["Particulier", "Entrepreneur"], horizontal=True)
            with st.form("ins_form"):
                if u_role == "Particulier":
                    pnom = st.text_input("Prénom")
                    nom = st.text_input("Nom")
                    nom_final = f"{pnom} {nom}"
                    siret_val = ""
                else:
                    nom_final = st.text_input("Nom de l'Etablissement / Entreprise")
                    siret_val = st.text_input("Numéro SIRET / RCCM")
                
                email_ins = st.text_input("Email")
                p1 = st.text_input("Mot de passe", type="password")
                p2 = st.text_input("Confirmez le mot de passe", type="password")
                
                if st.form_submit_button("🚀 Créer mon compte", use_container_width=True):
                    if p1 == p2 and len(p1) >= 6 and email_ins and nom_final:
                        code = random.randint(100000, 999999)
                        if send_validation_mail(email_ins, code):
                            st.session_state.update({'temp_id': email_ins, 'temp_pwd': p1, 'temp_name': nom_final, 'temp_type': u_role, 'temp_siret': siret_val, 'correct_code': code, 'verifying': True})
                            st.rerun()
                        else: st.error("Erreur d'envoi mail.")
                    else: st.warning("Vérifiez vos informations.")

# --- 9. ESPACES UTILISATEURS ---
else:
    with st.sidebar:
        st.image(direct_url, width=100)
        st.write(f"### {st.session_state['user_name']}")
        st.caption(f"Profil : {st.session_state['user_type']}")
        if st.button("🔌 Déconnexion"): st.session_state['connected'] = False; st.rerun()

    if st.session_state['user_type'] == "Particulier":
        st.title("📱 Mon Portefeuille")
        service = st.selectbox("Payer pour :", ["🎓 Frais de Scolarité", "🏠 Loyer", "💡 Facture EDG/SEG", "🛍️ Achat Commerçant"])
        montant = st.number_input("Montant (GNF)", min_value=1000)
        moyen = st.radio("Moyen de paiement :", ["Orange Money", "MTN MoMo", "Carte Visa"], horizontal=True)
        
        if moyen == "Carte Visa":
            st.text_input("💳 N° Carte")
            c1, c2 = st.columns(2)
            c1.text_input("📅 Expiration")
            c2.text_input("🔒 CVV", type="password")
        else:
            st.text_input("📱 Numéro à débiter")
            
        if st.button("💎 Valider le Règlement"):
            with st.spinner('Validation...'):
                time.sleep(2)
                st.balloons(); st.success("Paiement réussi !")
    else:
        st.title(f"💼 Business Dashboard")
        st.metric("Total encaissé", "0 GNF")
        st.info("Bienvenue dans votre espace professionnel.")
