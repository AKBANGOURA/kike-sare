import streamlit as st
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Kiké Saré - Inscription Ouverte", layout="wide", page_icon="🇬🇳")

# --- GESTION DE LA BASE DE DONNÉES UTILISATEURS (Simulée par un fichier CSV) ---
USER_DB = "users_db.csv"
if not os.path.exists(USER_DB):
    df_init = pd.DataFrame(columns=["username", "password", "full_name"])
    df_init.to_csv(USER_DB, index=False)

def create_account(user, pwd, name):
    df = pd.read_csv(USER_DB)
    if user in df['username'].values:
        return False
    new_user = pd.DataFrame([[user, pwd, name]], columns=["username", "password", "full_name"])
    new_user.to_csv(USER_DB, mode='a', header=False, index=False)
    return True

def verify_login(user, pwd):
    df = pd.read_csv(USER_DB)
    user_data = df[(df['username'] == user) & (df['password'] == pwd)]
    return user_data if not user_data.empty else None

# --- INITIALISATION SESSION ---
if 'connected' not in st.session_state:
    st.session_state['connected'] = False
if 'user_info' not in st.session_state:
    st.session_state['user_info'] = None

# --- FONCTION PDF ---
def generer_pdf(nom, nature, montant, ref):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(300, 750, "REÇU OFFICIEL - KIKÉ SARÉ")
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, f"Date : {datetime.now().strftime('%d/%m/%Y')}")
    c.drawString(100, 680, f"Client : {nom}")
    c.drawString(100, 660, f"Nature : {nature}")
    c.drawString(100, 640, f"Montant : {montant:,} GNF")
    c.save()
    buf.seek(0)
    return buf

# --- INTERFACE AUTHENTIFICATION (LOGIN / SIGNUP) ---
def auth_page():
    st.markdown("<h1 style='text-align: center;'>🇬🇳 Bienvenue sur Kiké Saré</h1>", unsafe_allow_html=True)
    
    choice = st.tabs(["Se connecter", "Créer un compte"])
    
    with choice[0]: # LOGIN
        with st.form("login"):
            u = st.text_input("Identifiant")
            p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Connexion"):
                user_row = verify_login(u, p)
                if user_row is not None:
                    st.session_state['connected'] = True
                    st.session_state['user_info'] = user_row.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Identifiant ou mot de passe incorrect.")

    with choice[1]: # SIGNUP
        with st.form("signup"):
            new_u = st.text_input("Choisissez un identifiant")
            new_n = st.text_input("Nom complet")
            new_p = st.text_input("Choisissez un mot de passe", type="password")
            if st.form_submit_button("S'inscrire"):
                if new_u and new_p and new_n:
                    if create_account(new_u, new_p, new_n):
                        st.success("Compte créé ! Connectez-vous maintenant.")
                    else:
                        st.error("Cet identifiant existe déjà.")
                else:
                    st.warning("Veuillez remplir tous les champs.")

# --- APPLICATION PRINCIPALE ---
def main_app():
    with st.sidebar:
        st.title("Kiké Saré")
        st.write(f"👤 {st.session_state['user_info']['full_name']}")
        if st.button("Déconnexion"):
            st.session_state['connected'] = False
            st.rerun()
    
    st.header("Effectuer un paiement")
    with st.form("pay"):
        nat = st.selectbox("Nature", ["Loyer", "Scolarité", "EDG/SEG"])
        mt = st.number_input("Montant (GNF)", min_value=0)
        ref = st.text_input("Référence")
        if st.form_submit_button("Valider"):
            st.success("Paiement validé !")
            pdf = generer_pdf(st.session_state['user_info']['full_name'], nat, mt, ref)
            st.download_button("📥 Télécharger le Reçu", pdf, f"recu_{ref}.pdf", "application/pdf")

# --- LANCEMENT ---
if not st.session_state['connected']:
    auth_page()
else:
    main_app()
