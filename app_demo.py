import streamlit as st
import sqlite3
import random
import smtplib
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
                 (id TEXT PRIMARY KEY, pwd TEXT, name TEXT, type TEXT, verified INT)''')
    try:
        c.execute("ALTER TABLE users ADD COLUMN siret TEXT")
    except sqlite3.OperationalError: pass
    conn.commit(); conn.close()

init_db()

# --- 3. ÉTAT DE LA SESSION ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- 4. AFFICHAGE DU LOGO RÉEL ---
def display_header():
    # URL d'un logo illustratif (Soleil + Argent) - Vous pourrez la remplacer par votre propre lien GitHub
    logo_url = "https://img.icons8.com/external-flatart-icons-flat-flatarticons/128/external-sun-energy-flatart-icons-flat-flatarticons.png"
    
    st.markdown(f"""
        <div style='text-align: center;'>
            <img src='{logo_url}' width='120'>
            <h1 style='color:#ce1126; margin-top:10px; margin-bottom:0;'>KIKÉ SARÉ</h1>
            <p style='color:#009460; font-weight:bold; font-size:18px;'>Payez vos mensualités en toute sécurité !</p>
            <hr style='border: 1px solid #f0f2f6;'>
        </div>
    """, unsafe_allow_html=True)

# --- 5. LOGIQUE D'ACCÈS ---
if not st.session_state['connected']:
    display_header()
    
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
                    st.success("Compte activé !"); st.session_state['verifying'] = False; st.rerun()
        with col_v2:
            if st.button("🔄 Renvoyer le code"):
                new_c = random.randint(100000, 999999)
                st.session_state['correct_code'] = new_c
                send_validation_mail(st.session_state['temp_id'], new_c)
                st.toast("Nouveau code envoyé !")

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
                if u_role == "Particulier":
                    nom_f = f"{st.text_input('Prénom')} {st.text_input('Nom')}"
                    s_v = ""
                else:
                    nom_f = st.text_input("Nom de l'Etablissement")
                    s_v = st.text_input("N° SIRET / RCCM")
                
                em = st.text_input("Email de validation")
                p1 = st.text_input("Mot de passe", type="password")
                p2 = st.text_input("Confirmez", type="password")
                
                if st.form_submit_button("🚀 Recevoir le code"):
                    if p1 == p2 and len(p1) >= 6 and em:
                        code = random.randint(100000, 999999)
                        if send_validation_mail(em, code):
                            st.session_state.update({'temp_id': em, 'temp_pwd': p1, 'temp_name': nom_f, 'temp_type': u_role, 'temp_siret': s_v, 'correct_code': code, 'verifying': True})
                            st.rerun()
                        else: st.error("Erreur SMTP.")

# --- 6. ESPACES UTILISATEURS ---
else:
    with st.sidebar:
        st.image("https://img.icons8.com/external-flatart-icons-flat-flatarticons/64/external-sun-energy-flatart-icons-flat-flatarticons.png")
        st.write(f"### {st.session_state['user_name']}")
        if st.button("🔌 Déconnexion"): st.session_state['connected'] = False; st.rerun()

    if st.session_state['user_type'] == "Particulier":
        st.title("📱 Mon Portefeuille")
        t_pay, t_hist = st.tabs(["💳 Règlement", "📜 Historique"])
        with t_pay:
            col_a, col_b = st.columns(2)
            with col_a:
                service = st.selectbox("Payer pour :", ["🎓 Scolarité", "🏠 Loyer", "💡 Facture", "🛍️ Achat"])
                ref = st.text_input("Référence")
                montant = st.number_input("Montant (GNF)", min_value=1000)
            with col_b:
                moyen = st.radio("Moyen", ["Orange Money", "MTN MoMo", "Carte Visa"], horizontal=True)
                if moyen == "Carte Visa":
                    st.text_input("💳 N° Carte")
                    c1, c2 = st.columns(2)
                    c1.text_input("📅 Expiration")
                    c2.text_input("🔒 CVV", type="password")
                else:
                    st.text_input("📱 Numéro", placeholder="622...")
                st.selectbox("Modalité", ["Comptant", "2 fois", "3 fois"])
            if st.button("💎 Valider"):
                st.balloons(); st.success("Paiement validé !")
    else:
        st.title(f"💼 Dashboard : {st.session_state['user_name']}")
        st.metric("Total encaissé", "0 GNF")
