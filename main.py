import streamlit as st
import sqlite3
import random
import smtplib
import time
from email.message import EmailMessage

import streamlit as st

# --- 1. CONFIGURATION DE LA PAGE ---
# L'ajout de ?v=2 force le navigateur à mettre à jour l'icône immédiatement
logo_url = "https://raw.githubusercontent.com/AKBANGOURA/kike-sare/main/logo.png?v=2"

st.set_page_config(
    page_title="KikéSaré", # Nom affiché sous l'icône sur le téléphone
    page_icon=logo_url,      # Favicon pour le navigateur
    layout="centered"
)

# --- 2. INJECTION DES METADONNÉES MOBILES & CSS ---
st.markdown("""
    <style>
        /* Masquage agressif des éléments Streamlit */
        #MainMenu, header, footer, .stDeployButton, .stActionButton {
            display: none !important;
            visibility: hidden !important;
        }

        /* Supprime l'espace blanc en haut de la page */
        .stApp {
            margin-top: -60px;
        }

        /* Supprime les ancres de lien sur tous les titres */
        [data-testid="stHeaderActionElements"] {
            display: none !important;
        }

        /* Masque le bouton de déploiement en bas à droite (votre photo) */
        button[data-testid="stAppDeployButton"] {
            display: none !important;
        }
    </style>
""", unsafe_allow_html=True)

st.markdown(f"""
    <head>
        <link rel="apple-touch-icon" href="{logo_url}">
        <link rel="icon" type="image/png" href="{logo_url}">
        <meta name="apple-mobile-web-app-title" content="KikéSaré">
        <meta name="apple-mobile-web-app-capable" content="yes">
        <meta name="apple-mobile-web-app-status-bar-style" content="default">
    </head>
    <style>
        /* Masquage des éléments Streamlit pour un look App Native */
        header {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        #MainMenu {{visibility: hidden;}}
        .stAppDeployButton {{display:none;}}

        /* Conteneur principal centré */
        .main .block-container {{
            max-width: 650px;
            padding-top: 2rem;
            margin: auto;
        }}
        
        /* Taille du logo fixée à 40px et centré */
        .stImage > img {{
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 40px; 
        }}

        /* Style des boutons alignés à gauche */
        div.stButton > button {{
            border-radius: 10px;
            font-weight: bold;
            padding-left: 25px;
            padding-right: 25px;
            width: auto;
        }}
    </style>
""", unsafe_allow_html=True)

# --- 3. FONCTION D'AFFICHAGE DE L'EN-TÊTE ---
def display_header():
    # Colonnes pour stabiliser le logo au milieu
    c1, c2, c3 = st.columns([2, 1, 2])
    with c2:
        st.image(logo_url) 
    
    st.markdown(f"""
        <div style='text-align: center;'>
        # À la place de st.title("KikéSaré") ou st.header("KikéSaré")
            st.write(f"<h1 style='text-align: center; color:#ce1126; margin:0;'>KikéSaré</h1>", unsafe_allow_html=True)
            <p style='color:#009460; font-weight:bold; font-size:18px; margin-bottom: 0px;'>La FinTech qui change tout</p>
            <p style='color:#666; font-style: italic; font-size: 13px;'>Payez vos mensualités en toute sécurité !</p>
            <hr style='border: 0.5px solid #eee; width: 100%; margin: 15px auto;'>
        </div>
    """, unsafe_allow_html=True)

# Appel de l'en-tête
display_header()
# --- 2. CSS PERSONNALISÉ NETTOYÉ ---
st.markdown(
    f"""
    <head>
        <meta name="apple-mobile-web-app-title" content="KikéSaré">
        <link rel="apple-touch-icon" href="{logo_url}">
        <meta name="apple-mobile-web-app-capable" content="yes">
    </head>
    <style>
        /* 1. Masquer les éléments de navigation Streamlit (icône lien et barre de déploiement) */
        /* Cible l'icône "chaîne" à côté du titre et le bouton en bas à droite */
        [data-testid="stHeaderActionElements"], .stAppDeployButton, .stActionButton {{
            display: none !important;
        }}
        
        /* Masquer le header et le footer natifs */
        header, footer {{
            visibility: hidden;
            display: none;
        }}

        /* 2. Conteneur principal */
        .main .block-container {{
            max-width: 650px;
            padding-top: 1rem;
            margin: auto;
        }}
        
        /* 3. Taille du logo fixée à 80px (ou 40px selon votre préférence) */
        .stImage > img {{
            display: block;
            margin-left: auto;
            margin-right: auto;
            width: 80px; 
        }}

        /* 4. Style des boutons pour éviter qu'ils ne prennent toute la largeur sur mobile */
        div.stButton > button {{
            border-radius: 10px;
            font-weight: bold;
            width: auto;
            min-width: 150px;
        }}
    </style>
    """,
    unsafe_allow_html=True
)
# --- 3. CONFIGURATION MAIL ---
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

# --- 4. BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('kikesare.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id TEXT PRIMARY KEY, pwd TEXT, name TEXT, type TEXT, verified INT, siret TEXT)''')
    conn.commit(); conn.close()

init_db()

# --- 5 bis. NOTIFICATION D'INSTALLATION MOBILE ---
def show_install_promotion():
    # On vérifie si on a déjà montré la notification dans cette session
    if 'promo_shown' not in st.session_state:
        st.session_state['promo_shown'] = True
        
        with st.expander("📲 Installer Kiké Saré sur votre téléphone", expanded=True):
            st.markdown("""
                <div style='text-align: left; font-size: 14px;'>
                    <strong>Pour une meilleure expérience :</strong><br>
                    1. Cliquez sur l'icône de partage (iOS) ou les 3 points (Android).<br>
                    2. Sélectionnez <b>'Sur l'écran d'accueil'</b> ou <b>'Installer'</b>.<br>
                    ✨ L'icône Kiké Saré apparaîtra parmi vos applications !
                </div>
            """, unsafe_allow_html=True)
            if st.button("J'ai compris"):
                st.rerun()

# --- MODIFICATION DE LA LOGIQUE D'ACCÈS ---
if not st.session_state['connected']:
    display_header()
    show_install_promotion() # Appelez la fonction ici
    
    # ... reste de votre code de connexion/inscription

# --- 6. ÉTAT DE LA SESSION ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- 7. EN-TÊTE AVEC VOTRE LOGO GITHUB ---
def display_header():
    st.markdown("<div style='text-align: center;'>", unsafe_allow_html=True)
    st.image(logo_url, width=150) 
    st.markdown(f"""
        <h1 style='color:#ce1126; margin-top:10px; margin-bottom:0;'>KikéSaré</h1>
        <p style='color:#009460; font-weight:bold; font-size:20px; margin-bottom:0;'>Payez vos mensualités en toute sécurité !</p>
        <p style='color:#666; font-style: italic; font-size:14px;'>La FinTech qui change votre monde</p>
        <hr style='border: 0.5px solid #eee; width: 80%; margin: 20px auto;'>
        </div>
    """, unsafe_allow_html=True)

# --- 8. CONNEXION ET INSCRIPTION ---
if not st.session_state['connected']:
    display_header()
    
    if st.session_state['verifying']:
        st.info(f"📩 Code envoyé à : **{st.session_state['temp_id']}**")
        code_s = st.text_input("Code de validation")
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
                if u_role == "Particulier":
                    prenom = st.text_input("Prénom")
                    nom = st.text_input("Nom")
                    nom_final = f"{prenom} {nom}"
                    siret_val = ""
                else:
                    nom_final = st.text_input("Nom de l'Etablissement / Entreprise")
                    siret_val = st.text_input("N° SIRET / RCCM")
                
                email_ins = st.text_input("Votre Email")
                p1 = st.text_input("Mot de passe", type="password")
                p2 = st.text_input("Confirmez le mot de passe", type="password")
                
                if st.form_submit_button("🚀 Recevoir le code"):
                    if p1 == p2 and len(p1) >= 6 and email_ins and nom_final:
                        code = random.randint(100000, 999999)
                        if send_validation_mail(email_ins, code):
                            st.session_state.update({'temp_id': email_ins, 'temp_pwd': p1, 'temp_name': nom_final, 'temp_type': u_role, 'temp_siret': siret_val, 'correct_code': code, 'verifying': True})
                            st.rerun()
                        else: st.error("Erreur mail.")

# --- 9. ESPACE APRÈS CONNEXION ---
else:
    with st.sidebar:
        st.image(logo_url, width=100)
        st.write(f"### {st.session_state['user_name']}")
        if st.button("🔌 Déconnexion"): st.session_state['connected'] = False; st.rerun()

    if st.session_state['user_type'] == "Particulier":
        st.title("💳 Effectuer un Règlement")
        col_a, col_b = st.columns(2)
        with col_a:
            service = st.selectbox("Payer pour :", ["🎓 Frais de Scolarité", "🏠 Loyer", "💡 Facture EDG/SEG", "🛍️ Achat Commerçant"])
            montant = st.number_input("Montant (GNF)", min_value=1000)
        with col_b:
            moyen = st.radio("Moyen :", ["Orange Money", "MTN MoMo", "Carte Visa"], horizontal=True)
            if moyen == "Carte Visa":
                st.text_input("💳 N° Carte")
                st.text_input("📅 Exp (MM/AA)")
                st.text_input("🔒 CVV", type="password")
            else:
                st.text_input("📱 Numéro")
        
        if st.button("💎 Confirmer le Paiement"):
            with st.spinner('Validation...'):
                time.sleep(2)
                st.balloons(); st.success(f"Paiement de {montant} GNF réussi !")
    else:
        st.title(f"💼 Dashboard : {st.session_state['user_name']}")
        st.metric("Total encaissé", "0 GNF")










