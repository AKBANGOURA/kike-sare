import streamlit as st
import sqlite3
import random
import smtplib
from email.message import EmailMessage

# --- 1. CONFIGURATION MAIL (À REMPLIR) ---
# Pour que l'envoi fonctionne, utilisez un "Mot de passe d'application" Gmail
EMAIL_SENDER = "bangourakallaa@gmail.com" 
EMAIL_PASSWORD = "tyqlqacsgwpoeiin" 

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
    except Exception:
        return False

# --- 2. INITIALISATION ---
st.set_page_config(page_title="Kiké Saré", layout="wide")

def init_db():
    conn = sqlite3.connect('kikesare.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id TEXT PRIMARY KEY, pwd TEXT, name TEXT, type TEXT, verified INT, siret TEXT)''')
    conn.commit()
    conn.close()

init_db()

if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- 3. ACCÈS & INSCRIPTION ---
if not st.session_state['connected']:
    st.markdown("<h1 style='text-align:center; color:#ce1126;'>KIKÉ SARÉ</h1>", unsafe_allow_html=True)
    
    if st.session_state['verifying']:
        st.info(f"📩 Code envoyé à : {st.session_state['temp_id']}")
        code_s = st.text_input("Saisissez le code reçu par mail")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if st.button("✅ Valider"):
                if code_s == str(st.session_state['correct_code']):
                    conn = sqlite3.connect('kikesare.db')
                    conn.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, 1, ?)", 
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
        with tab2:
            u_role = st.radio("Type de compte", ["Particulier", "Entrepreneur"], horizontal=True)
            with st.form("inscription"):
                nom = st.text_input("Nom / Entreprise")
                email = st.text_input("Email")
                p1 = st.text_input("Mot de passe", type="password")
                p2 = st.text_input("Confirmer le mot de passe", type="password")
                siret = st.text_input("SIRET (si Business)") if u_role == "Entrepreneur" else ""
                if st.form_submit_button("🚀 S'inscrire"):
                    if p1 == p2 and email:
                        code = random.randint(100000, 999999)
                        if send_validation_mail(email, code):
                            st.session_state.update({'temp_id':email, 'temp_pwd':p1, 'temp_name':nom, 'temp_type':u_role, 'temp_siret':siret, 'correct_code':code, 'verifying':True})
                            st.rerun()
                        else: st.error("Erreur d'envoi du mail. Vérifiez vos réglages SMTP.")

# --- 4. INTERFACES CONNECTÉES ---
else:
    st.sidebar.title(f"👤 {st.session_state['user_name']}")
    if st.sidebar.button("Déconnexion"): st.session_state['connected'] = False; st.rerun()

    if st.session_state['user_type'] == "Particulier":
        # ESPACE PARTICULIER : PAIEMENTS
        st.title("📱 Mes Paiements")
        t_p1, t_p2 = st.tabs(["💳 Effectuer un Paiement", "📜 Historique"])
        with t_p1:
            with st.form("pay"):
                service = st.selectbox("Service", ["Loyer", "Frais de scolarité", "Vente marchandise"])
                moyen = st.radio("Moyen", ["Orange Money", "MTN MoMo", "Carte Visa"], horizontal=True)
                montant = st.number_input("Montant (GNF)", min_value=100)
                if st.form_submit_button("Valider le Règlement"):
                    st.success(f"Paiement de {montant} GNF effectué pour : {service}")
    else:
        # ESPACE BUSINESS : GROUPE AKB
        st.title("💼 Dashboard Business")
        st.subheader("Suivi des encaissements")
        c1, c2 = st.columns(2)
        c1.metric("Total Reçu", "25.000.000 GNF")
        st.bar_chart({"Loyer": 15, "Scolarité": 10})
