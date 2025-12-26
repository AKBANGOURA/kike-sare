import streamlit as st
import sqlite3
import random
import smtplib
import time
from email.message import EmailMessage

# --- 1. CONFIGURATION DE LA PAGE ---
logo_url = "https://raw.githubusercontent.com/AKBANGOURA/kike-sare/main/logo.png"

st.set_page_config(
    page_title="Kiké Saré",
    page_icon=logo_url,
    layout="centered" 
)

# --- 2. CSS AVANCÉ POUR LE CENTRAGE TOTAL ---
st.markdown(
    f"""
    <style>
        /* Centre le bloc principal sur l'écran */
        .main .block-container {{
            max-width: 600px;
            padding-top: 2rem;
            margin: auto;
            text-align: center;
        }}
        
        /* Centre les images */
        .stImage > img {{
            display: block;
            margin-left: auto;
            margin-right: auto;
        }}

        /* Centre les labels de texte (Email, Mot de passe) */
        .stTextInput label, .stSelectbox label, .stRadio label {{
            display: block;
            text-align: center;
            width: 100%;
        }}

        /* Centre les boutons et les arrondit */
        div.stButton > button {{
            width: 100%;
            border-radius: 10px;
            font-weight: bold;
            margin: auto;
            display: block;
        }}

        /* Masque les éléments inutiles */
        header {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        .stAppDeployButton {{display:none;}}

        /* Centre les boutons radio horizontalement */
        [data-testid="stMarkdownContainer"] p {{
            text-align: center;
        }}
        div[data-testid="stHorizontalBlock"] {{
            justify-content: center;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# --- 3. FONCTION D'AFFICHAGE DU LOGO ET TITRES (CENTRÉS) ---
def display_header():
    # Création de colonnes pour forcer le logo au milieu
    c1, c2, c3 = st.columns([1, 2, 1])
    with c2:
        st.image(logo_url, use_container_width=True)
    
    # Titre et Slogan avec centrage HTML forcé
    st.markdown(f"""
        <div style='text-align: center;'>
            <h1 style='color:#ce1126; margin-bottom: 5px;'>KIKÉ SARÉ</h1>
            <p style='color:#009460; font-weight:bold; font-size:20px; margin-bottom: 0;'>Payez vos mensualités en toute sécurité !</p>
            <p style='color:#666; font-style: italic; font-size:14px;'>La FinTech qui change votre monde</p>
            <hr style='border: 0.5px solid #eee; width: 80%; margin: 20px auto;'>
        </div>
    """, unsafe_allow_html=True)


# --- 1. CONFIGURATION MAIL ---
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
    
# --- 4. FONCTION D'AFFICHAGE DU LOGO (Celle qui manquait) ---
def display_header():
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    # On utilise votre image GitHub pour un rendu professionnel
    st.image(logo_url, width=150) 
    st.markdown(f"""
        <h1 style='color:#ce1126; margin-top:10px; margin-bottom:0;'>KikéSaré</h1>
        <p style='color:#009460; font-weight:bold; font-size:20px; margin-bottom:0;'>La FinTech qui change votre quotidien</p>
        <p style='color:#666; font-style: italic; font-size:14px;'>Payez vos mensualités en toute sécurité!</p>
        <hr style='border: 0.5px solid #eee; width: 80%; margin: 20px auto;'>
        </div>
    """, unsafe_allow_html=True)

# --- 5. LOGIQUE D'ACCÈS (CONNEXION & INSCRIPTION) ---
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
            u_role = st.radio("Vous souhaitez créer un compte :", ["Particulier", "Entrepreneur"], horizontal=True)
            with st.form("ins_form"):
                # CORRECTION DES CHAMPS SELON LE TYPE DE COMPTE
                if u_role == "Particulier":
                    prenom = st.text_input("Prénom")
                    nom = st.text_input("Nom")
                    nom_final = f"{prenom} {nom}"
                    siret_val = ""
                else:
                    nom_final = st.text_input("Nom de l'Etablissement / Entreprise")
                    siret_val = st.text_input("Numéro SIRET / RCCM")
                
                email_ins = st.text_input("Votre Email (pour validation)")
                p1 = st.text_input("Nouveau mot de passe", type="password")
                p2 = st.text_input("Confirmez le mot de passe", type="password")
                
                if st.form_submit_button("🚀 Recevoir mon code par mail"):
                    if p1 != p2: st.error("Les mots de passe ne correspondent pas.")
                    elif len(p1) < 6: st.error("Mot de passe trop court.")
                    elif not email_ins or not nom_final: st.error("Veuillez remplir tous les champs.")
                    else:
                        code = random.randint(100000, 999999)
                        if send_validation_mail(email_ins, code):
                            st.session_state.update({
                                'temp_id': email_ins, 'temp_pwd': p1, 'temp_name': nom_final, 
                                'temp_type': u_role, 'temp_siret': siret_val, 
                                'correct_code': code, 'verifying': True
                            })
                            st.rerun()
                        else: st.error("Erreur d'envoi du mail.")

# --- 6. ESPACES UTILISATEURS ---
else:
    with st.sidebar:
        st.markdown("<h2 style='text-align:center;'>☀️💸</h2>", unsafe_allow_html=True)
        st.write(f"### {st.session_state['user_name']}")
        st.caption(f"Profil : {st.session_state['user_type']}")
        if st.button("🔌 Déconnexion"): st.session_state['connected'] = False; st.rerun()

    if st.session_state['user_type'] == "Particulier":
        st.title("📱 Mon Portefeuille de Paiement")
        t_pay, t_hist = st.tabs(["💳 Effectuer un Règlement", "📜 Historique"])
        with t_pay:
            col_a, col_b = st.columns(2)
            with col_a:
                service = st.selectbox("Payer pour :", ["🎓 Frais de Scolarité", "🏠 Loyer", "💡 Facture EDG/SEG", "🛍️ Achat Commerçant"])
                ref = st.text_input("Référence (N° Facture / Étudiant)")
                montant = st.number_input("Montant (GNF)", min_value=1000)
            with col_b:
                moyen = st.radio("Moyen de paiement :", ["Orange Money", "MTN MoMo", "Carte Visa"], horizontal=True)
                if moyen == "Carte Visa":
                    st.text_input("💳 Numéro de la carte")
                    c1, c2 = st.columns(2)
                    c1.text_input("📅 Expiration (MM/AA)")
                    c2.text_input("🔒 CVV", type="password")
                else:
                    st.text_input("📱 Numéro à débiter", placeholder="622...")
                st.selectbox("Modalité", ["Comptant", "2 fois", "3 fois"])
            
            if st.button("💎 Valider le Règlement"):
                with st.spinner('Traitement en cours...'):
                    time.sleep(2)
                    st.balloons(); st.success(f"Paiement de {montant} GNF validé !")

    else:
        st.title(f"💼 Dashboard Business : {st.session_state['user_name']}")
        st.metric("Total encaissé", "0 GNF")
        st.info("Le graphique des revenus s'affichera ici dès la première transaction.")
