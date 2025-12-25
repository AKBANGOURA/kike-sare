import streamlit as st
import sqlite3
import random
import smtplib
import time
from email.message import EmailMessage

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Kiké Saré", page_icon="☀️", layout="centered")

# --- 1. CONFIGURATION MAIL ---
EMAIL_SENDER = "bangourakallaa@gmail.com" 
EMAIL_PASSWORD = "tyqlqacsgwpoeiin" 

def send_validation_mail(receiver, code):
    msg = EmailMessage()
    msg.set_content(f"Bienvenue sur Kiké Saré ! Votre code de validation est : {code}")
    msg['Subject'] = "Validation de compte - Kiké Saré"
    msg['From'] = EMAIL_SENDER
    msg['To'] = receiver
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception: return False

# --- 2. BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('kikesare.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id TEXT PRIMARY KEY, pwd TEXT, name TEXT, type TEXT, verified INT, siret TEXT)''')
    conn.commit(); conn.close()

init_db()

# --- 3. ÉTAT DE LA SESSION ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- 4. AFFICHAGE DU LOGO ---
def display_header():
    # Logo Soleil Jaune + Argent Vert (Hébergé pour l'application)
    logo_url = "https://img.icons8.com/emoji/120/sun-emoji.png" # Soleil
    money_url = "https://img.icons8.com/color/48/money-bag.png" # Argent
    
    st.markdown(f"""
        <div style='text-align: center;'>
            <div style='position: relative; display: inline-block;'>
                <img src='{logo_url}' width='120'>
                <img src='{money_url}' width='50' style='position: absolute; top: 35px; left: 35px;'>
            </div>
            <h1 style='color:#ce1126; margin-top:10px; margin-bottom:0;'>KIKÉ SARÉ</h1>
            <p style='color:#009460; font-weight:bold; font-size:18px;'>L'argent au service de votre avenir</p>
            <hr style='border: 1px solid #f0f2f6;'>
        </div>
    """, unsafe_allow_html=True)

# --- 5. LOGIQUE D'ACCÈS ---
if not st.session_state['connected']:
    display_header()
    
    if st.session_state['verifying']:
        st.info(f"📩 Code envoyé à : **{st.session_state['temp_id']}**")
        code_s = st.text_input("Saisissez le code de validation")
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
            if st.button("Se connecter"):
                conn = sqlite3.connect('kikesare.db')
                u = conn.execute("SELECT * FROM users WHERE id=? AND pwd=? AND verified=1", (e_log, p_log)).fetchone()
                conn.close()
                if u:
                    st.session_state.update({'connected': True, 'user_name': u[2], 'user_id': u[0], 'user_type': u[3]})
                    st.rerun()
                else: st.error("Échec de connexion.")

        with tab2:
            u_role = st.radio("Type :", ["Particulier", "Entrepreneur"], horizontal=True)
            with st.form("ins_form"):
                nom_f = st.text_input("Nom complet / Entreprise")
                s_v = st.text_input("SIRET / RCCM (si Pro)") if u_role == "Entrepreneur" else ""
                em = st.text_input("Email")
                p1 = st.text_input("Mot de passe", type="password")
                p2 = st.text_input("Confirmez", type="password")
                if st.form_submit_button("🚀 S'inscrire"):
                    if p1 == p2 and len(p1) >= 6:
                        code = random.randint(100000, 999999)
                        if send_validation_mail(em, code):
                            st.session_state.update({'temp_id': em, 'temp_pwd': p1, 'temp_name': nom_f, 'temp_type': u_role, 'temp_siret': s_v, 'correct_code': code, 'verifying': True})
                            st.rerun()

# --- 6. ESPACES UTILISATEURS ---
else:
    with st.sidebar:
        st.markdown("<h2 style='text-align:center;'>☀️💰</h2>", unsafe_allow_html=True)
        st.write(f"**Connecté :** {st.session_state['user_name']}")
        if st.button("🔌 Déconnexion"): st.session_state['connected'] = False; st.rerun()

    if st.session_state['user_type'] == "Particulier":
        st.title("💳 Espace de Règlement")
        col_a, col_b = st.columns(2)
        with col_a:
            service = st.selectbox("Type de frais", ["Scolarité", "Loyer", "EDG/SEG", "Commerçant"])
            montant = st.number_input("Montant à payer (GNF)", min_value=1000, step=500)
        with col_b:
            moyen = st.radio("Moyen de paiement", ["Orange Money", "MTN MoMo", "Carte Visa"], horizontal=True)
            if moyen == "Carte Visa":
                st.text_input("💳 N° de Carte")
                st.text_input("🔒 CVV", type="password")
            else:
                st.text_input("📱 Numéro de téléphone", placeholder="622...")

        if st.button("💎 Payer maintenant"):
            with st.spinner('Traitement sécurisé en cours...'):
                time.sleep(2) # Simulation de la passerelle
                st.success(f"Paiement de {montant} GNF réussi pour {service} !")
                st.balloons()
                st.download_button("📥 Télécharger le reçu (PDF)", "Reçu de paiement Kiké Saré", file_name="recu_kikesare.txt")

    else:
        st.title(f"📈 Dashboard : {st.session_state['user_name']}")
        st.metric("Balance disponible", "0 GNF")
        st.info("Les fonds collectés sont transférés vers votre compte de réception sous 24h.")
