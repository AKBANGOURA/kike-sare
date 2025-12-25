import streamlit as st
import sqlite3
import random
import smtplib
from email.message import EmailMessage

# --- 1. CONFIGURATION MAIL ---
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

# --- 2. INITIALISATION ET RÉPARATION DB ---
def init_db():
    conn = sqlite3.connect('kikesare.db', check_same_thread=False)
    c = conn.cursor()
    # Suppression de l'ancienne table si elle cause une erreur de structure (OperationalError)
    # À ne faire qu'une fois pour mettre à jour la structure
    # c.execute("DROP TABLE IF EXISTS users") 
    
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id TEXT PRIMARY KEY, pwd TEXT, name TEXT, type TEXT, verified INT, siret TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS historique 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, service TEXT, montant REAL, date TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. GESTION DES ÉTATS ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- 4. ACCÈS (INSCRIPTION ET VÉRIFICATION) ---
if not st.session_state['connected']:
    st.markdown("<h1 style='text-align:center; color:#ce1126;'>KIKÉ SARÉ</h1>", unsafe_allow_html=True)
    
    if st.session_state['verifying']:
        st.info(f"📩 Code envoyé à : {st.session_state['temp_id']}")
        code_s = st.text_input("Saisissez le code reçu par mail")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if st.button("✅ Valider l'inscription"):
                if code_s == str(st.session_state['correct_code']):
                    conn = sqlite3.connect('kikesare.db')
                    # Correction de la requête pour correspondre EXACTEMENT aux colonnes de la DB
                    conn.execute("INSERT OR REPLACE INTO users (id, pwd, name, type, verified, siret) VALUES (?, ?, ?, ?, ?, ?)", 
                                (st.session_state['temp_id'], st.session_state['temp_pwd'], 
                                 st.session_state['temp_name'], st.session_state['temp_type'], 1, st.session_state.get('temp_siret', '')))
                    conn.commit(); conn.close()
                    st.success("Compte validé ! Connectez-vous."); st.session_state['verifying'] = False; st.rerun()
        with col_v2:
            if st.button("🔄 Renvoyer le code"):
                new_c = random.randint(100000, 999999)
                st.session_state['correct_code'] = new_c
                send_validation_mail(st.session_state['temp_id'], new_c)
                st.toast("Nouveau code envoyé !")

    else:
        tab1, tab2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
        with tab1:
            e_log = st.text_input("Email")
            p_log = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter"):
                conn = sqlite3.connect('kikesare.db')
                u = conn.execute("SELECT * FROM users WHERE id=? AND pwd=? AND verified=1", (e_log, p_log)).fetchone()
                conn.close()
                if u:
                    st.session_state.update({'connected': True, 'user_name': u[2], 'user_id': u[0], 'user_type': u[3]})
                    st.rerun()
                else: st.error("Identifiants incorrects ou compte non vérifié.")

        with tab2:
            u_role = st.radio("Type de compte", ["Particulier", "Entrepreneur (Entreprise/Commerce)"], horizontal=True)
            with st.form("inscription_complete"):
                if u_role == "Particulier":
                    nom_f = f"{st.text_input('Prénom')} {st.text_input('Nom')}"
                    siret_f = ""
                else:
                    nom_f = st.text_input("Nom de l'Entreprise")
                    siret_f = st.text_input("N° SIRET / RCCM")
                
                email_f = st.text_input("Email de validation")
                p1 = st.text_input("Mot de passe", type="password")
                p2 = st.text_input("Confirmer le mot de passe", type="password")
                
                if st.form_submit_button("🚀 Recevoir le code"):
                    if p1 == p2 and len(p1) >= 6 and email_f:
                        code = random.randint(100000, 999999)
                        if send_validation_mail(email_f, code):
                            st.session_state.update({'temp_id': email_f, 'temp_pwd': p1, 'temp_name': nom_f, 'temp_type': u_role, 'temp_siret': siret_f, 'correct_code': code, 'verifying': True})
                            st.rerun()

# --- 5. LOGIQUE DES ESPACES ---
else:
    st.sidebar.write(f"### {st.session_state['user_name']}")
    if st.sidebar.button("🔌 Déconnexion"): st.session_state['connected'] = False; st.rerun()

    # ESPACE PARTICULIER (Paiement)
    if st.session_state['user_type'] == "Particulier":
        st.title("💳 Espace de Paiement Particulier")
        serv = st.selectbox("Choisir un service", ["🎓 Frais de Scolarité", "🏠 Loyer", "💡 Facture EDG", "🛒 Achat Commerçant"])
        montant = st.number_input("Montant (GNF)", min_value=5000)
        moyen = st.radio("Moyen de paiement", ["Orange Money", "MTN MoMo", "Carte Visa"])
        if st.button("Valider le Règlement"):
            st.success(f"Paiement de {montant} GNF pour {serv} validé !")

    # ESPACE ENTREPRENEUR DYNAMIQUE
    else:
        st.title(f"💼 Dashboard : {st.session_state['user_name']}")
        t_rev, t_param = st.tabs(["📈 Mes Revenus", "⚙️ Paramètres de réception"])
        with t_rev:
            c1, c2 = st.columns(2)
            c1.metric("Total encaissé", "0 GNF")
            c2.metric("Nouveaux clients", "0")
            st.info(f"Les paiements vers {st.session_state['user_name']} s'afficheront ici.")
