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

# --- 4. AFFICHAGE DU LOGO DEMANDÉ (SOLEIL + ARGENT) ---
def display_header():
    # Utilisation d'icônes stables pour garantir l'affichage du soleil et des billets
    st.markdown("""
        <div style='text-align: center;'>
            <div style='font-size: 80px; line-height: 1;'>☀️</div>
            <div style='font-size: 40px; margin-top: -50px; margin-left: 20px;'>💸</div>
            <h1 style='color:#ce1126; margin-top:10px; margin-bottom:0;'>KIKÉ SARÉ</h1>
            <p style='color:#009460; font-weight:bold; font-size:18px;'>L'argent au service de votre avenir</p>
            <p style='color:#666; font-style: italic;'>Payez vos mensualités en toute sécurité !</p>
            <hr style='border: 0.5px solid #eee; width: 80%; margin: 20px auto;'>
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
        st.markdown("<h2 style='text-align:center;'>☀️💸</h2>", unsafe_allow_html=True)
        st.write(f"### {st.session_state['user_name']}")
        if st.button("🔌 Déconnexion"): st.session_state['connected'] = False; st.rerun()

    if st.session_state['user_type'] == "Particulier":
        st.title("📱 Mon Portefeuille de Paiement")
        t_pay, t_hist = st.tabs(["💳 Effectuer un Règlement", "📜 Historique"])
        with t_pay:
            st.subheader("Nouvelle transaction")
            col_a, col_b = st.columns(2)
            with col_a:
                service = st.selectbox("Payer pour :", ["🎓 Frais de Scolarité", "🏠 Loyer", "💡 Facture EDG/SEG", "🛍️ Achat Commerçant"])
                ref = st.text_input("Référence (N° Facture / Étudiant)")
                montant = st.number_input("Montant (GNF)", min_value=1000)
            with col_b:
                moyen = st.radio("Moyen de paiement :", ["Orange Money", "MTN MoMo", "Carte Visa"], horizontal=True)
                if moyen == "Carte Visa":
                    st.text_input("💳 N° de la carte")
                    c_col1, c_col2 = st.columns(2)
                    c_col1.text_input("📅 Expiration (MM/AA)")
                    c_col2.text_input("🔒 CVV", type="password")
                else:
                    st.text_input("📱 Numéro à débiter", placeholder="622...")
                modalite = st.selectbox("Modalité", ["Comptant", "Échelonné (2 fois)", "Échelonné (3 fois)"])
            
            if st.button("💎 Valider le Règlement"):
                with st.spinner('Traitement en cours...'):
                    time.sleep(2)
                    st.balloons(); st.success(f"Paiement de {montant} GNF validé !")

    else:
        st.title(f"💼 Dashboard Business : {st.session_state['user_name']}")
        t_stats, t_fond = st.tabs(["📈 Mes Revenus", "💰 Réception des fonds"])
        with t_stats:
            st.metric("Total encaissé", "0 GNF")
            st.info("Le graphique des revenus s'affichera ici dès la première transaction.")
        with t_fond:
            with st.form("config_recep"):
                st.selectbox("Canal de réception", ["Orange Money Business", "MTN MoMo Business", "Compte Bancaire"])
                st.text_input("Numéro ou RIB de réception")
                if st.form_submit_button("💾 Enregistrer"): st.success("Paramètres mis à jour.")
