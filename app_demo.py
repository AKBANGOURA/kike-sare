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

# --- 4. AFFICHAGE DU LOGO (Soleil + Argent) ---
def display_header():
    # URL d'une image correspondant à votre logo (Soleil et Argent)
    logo_url = "https://cdn-icons-png.flaticon.com/512/3931/3931365.png" # Icône Soleil/Économie
    
    st.markdown(f"""
        <div style='text-align: center;'>
            <img src='{logo_url}' width='150' style='margin-bottom: 10px;'>
            <h1 style='color:#ce1126; margin-top:0; margin-bottom:0;'>KIKÉ SARÉ</h1>
            <p style='color:#009460; font-weight:bold; font-size:20px;'>L'argent au service de votre avenir</p>
            <p style='color:#666; font-style: italic;'>Payez vos mensualités en toute sécurité !</p>
            <hr style='border: 1px solid #f0f2f6; width: 50%; margin: auto; margin-bottom: 20px;'>
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
                else: st.error("Identifiants incorrects.")

        with tab2:
            u_role = st.radio("Type de compte :", ["Particulier", "Entrepreneur"], horizontal=True)
            with st.form("ins_form"):
                nom_f = st.text_input("Prénom & Nom / Nom Entreprise")
                s_v = st.text_input("N° SIRET / RCCM") if u_role == "Entrepreneur" else ""
                em = st.text_input("Votre Email")
                p1 = st.text_input("Nouveau mot de passe", type="password")
                p2 = st.text_input("Confirmez le mot de passe", type="password")
                if st.form_submit_button("🚀 Créer mon compte"):
                    if p1 == p2 and len(p1) >= 6 and em:
                        code = random.randint(100000, 999999)
                        if send_validation_mail(em, code):
                            st.session_state.update({'temp_id': em, 'temp_pwd': p1, 'temp_name': nom_f, 'temp_type': u_role, 'temp_siret': s_v, 'correct_code': code, 'verifying': True})
                            st.rerun()

# --- 6. ESPACES UTILISATEURS ---
else:
    with st.sidebar:
        # Mini logo dans la barre latérale
        st.markdown("<div style='text-align:center;'><img src='https://cdn-icons-png.flaticon.com/512/3931/3931365.png' width='80'></div>", unsafe_allow_html=True)
        st.write(f"### {st.session_state['user_name']}")
        if st.button("🔌 Déconnexion"): st.session_state['connected'] = False; st.rerun()

    if st.session_state['user_type'] == "Particulier":
        st.title("💳 Effectuer un Règlement")
        col_a, col_b = st.columns(2)
        with col_a:
            service = st.selectbox("Payer pour :", ["🎓 Frais de Scolarité", "🏠 Loyer", "💡 Facture EDG/SEG", "🛍️ Achat Commerçant"])
            montant = st.number_input("Montant (GNF)", min_value=1000)
        with col_b:
            moyen = st.radio("Moyen de paiement :", ["Orange Money", "MTN MoMo", "Carte Visa"], horizontal=True)
            if moyen == "Carte Visa":
                st.text_input("💳 N° de Carte")
                st.text_input("🔒 CVV", type="password")
            else:
                st.text_input("📱 Numéro de téléphone", placeholder="622...")
        
        if st.button("💎 Valider le Paiement"):
            with st.spinner('Validation en cours...'):
                time.sleep(2)
                st.balloons(); st.success(f"Paiement de {montant} GNF validé !")

    else:
        st.title(f"💼 Business : {st.session_state['user_name']}")
        st.metric("Total des revenus collectés", "0 GNF")
