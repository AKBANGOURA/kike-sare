import streamlit as st
import sqlite3
import random
import smtplib
from email.message import EmailMessage

# --- CONFIGURATION DE LA PAGE (Icône du navigateur) ---
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

# --- 2. INITIALISATION ET RÉPARATION DE LA BASE ---
def init_db():
    conn = sqlite3.connect('kikesare.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id TEXT PRIMARY KEY, pwd TEXT, name TEXT, type TEXT, verified INT)''')
    try:
        c.execute("ALTER TABLE users ADD COLUMN siret TEXT")
    except sqlite3.OperationalError: pass
    conn.commit()
    conn.close()

init_db()

# --- 3. ÉTAT DE LA SESSION ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- 4. AFFICHAGE DU LOGO ET TITRE ---
def display_header():
    # Simulation visuelle du logo Soleil + Billets avec du HTML/CSS
    st.markdown("""
        <div style='text-align: center;'>
            <div style='font-size: 70px;'>☀️💸</div>
            <h1 style='color:#ce1126; margin-bottom:0;'>KIKÉ SARÉ</h1>
            <p style='color:#009460; font-weight:bold; font-size:18px;'>Payez vos mensualités en toute sécurité !</p>
        </div>
    """, unsafe_allow_html=True)

# --- 5. ACCÈS : CONNEXION & INSCRIPTION ---
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
            e_log = st.text_input("Email", key="login_email")
            p_log = st.text_input("Mot de passe", type="password", key="login_pwd")
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
            with st.form("inscription_form"):
                if u_role == "Particulier":
                    nom_f = f"{st.text_input('Prénom')} {st.text_input('Nom')}"
                    siret_val = ""
                else:
                    nom_f = st.text_input("Nom de l'Etablissement / Entreprise")
                    siret_val = st.text_input("Numéro SIRET / RCCM")
                
                email_ins = st.text_input("Email")
                p1 = st.text_input("Mot de passe", type="password")
                p2 = st.text_input("Confirmez le mot de passe", type="password")
                
                if st.form_submit_button("🚀 Recevoir le code"):
                    if p1 == p2 and len(p1) >= 6 and email_ins:
                        code = random.randint(100000, 999999)
                        if send_validation_mail(email_ins, code):
                            st.session_state.update({'temp_id': email_ins, 'temp_pwd': p1, 'temp_name': nom_f, 'temp_type': u_role, 'temp_siret': siret_val, 'correct_code': code, 'verifying': True})
                            st.rerun()
                        else: st.error("Erreur d'envoi mail.")

# --- 6. ESPACES UTILISATEURS ---
else:
    with st.sidebar:
        st.markdown("<h2 style='text-align:center;'>☀️💸</h2>", unsafe_allow_html=True)
        st.write(f"### {st.session_state['user_name']}")
        if st.button("🔌 Déconnexion"): st.session_state['connected'] = False; st.rerun()

    if st.session_state['user_type'] == "Particulier":
        st.title("📱 Mon Portefeuille")
        t_pay, t_hist = st.tabs(["💳 Règlement", "📜 Historique"])
        with t_pay:
            col_a, col_b = st.columns(2)
            with col_a:
                service = st.selectbox("Service", ["🎓 Scolarité", "🏠 Loyer", "💡 Facture", "🛍️ Achat"])
                ref = st.text_input("Référence")
                montant = st.number_input("Montant (GNF)", min_value=1000)
            with col_b:
                moyen = st.radio("Moyen", ["Orange Money", "MTN MoMo", "Carte Visa"], horizontal=True)
                if moyen == "Carte Visa":
                    st.text_input("💳 N° Carte")
                    c1, c2 = st.columns(2)
                    c1.text_input("📅 MM/AA")
                    c2.text_input("🔒 CVV", type="password")
                else:
                    st.text_input("📱 Numéro", placeholder="622...")
                modalite = st.selectbox("Modalité", ["Comptant", "2 fois", "3 fois"])
            if st.button("💎 Valider"):
                st.balloons(); st.success("Paiement validé !")

    else:
        st.title(f"💼 Dashboard : {st.session_state['user_name']}")
        t1, t2 = st.tabs(["📈 Revenus", "💰 Réception"])
        with t1:
            st.metric("Total encaissé", "0 GNF")
            st.info("Aucune transaction pour le moment.")
        with t2:
            with st.form("rec"):
                st.selectbox("Canal", ["Orange Money Business", "MTN MoMo Business", "Banque"])
                st.text_input("Numéro/RIB")
                if st.form_submit_button("💾 Enregistrer"): st.success("Mis à jour.")
