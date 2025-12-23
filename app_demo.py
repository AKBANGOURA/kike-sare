import streamlit as st
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import os
import random

# --- CONFIGURATION ---
st.set_page_config(page_title="Kiké Saré - Sécurisé", layout="wide", page_icon="🇬🇳")

# --- BASE DE DONNÉES UTILISATEURS ---
USER_DB = "users_db.csv"
if not os.path.exists(USER_DB):
    df_init = pd.DataFrame(columns=["identifier", "password", "full_name", "verified"])
    df_init.to_csv(USER_DB, index=False)

def create_account(identifier, pwd, name):
    df = pd.read_csv(USER_DB)
    if identifier in df['identifier'].values:
        return False
    # On crée le compte avec 'verified' à False par défaut
    new_user = pd.DataFrame([[identifier, pwd, name, False]], columns=["identifier", "password", "full_name", "verified"])
    new_user.to_csv(USER_DB, mode='a', header=False, index=False)
    return True

def verify_login(identifier, pwd):
    df = pd.read_csv(USER_DB)
    user_data = df[(df['identifier'] == identifier) & (df['password'] == pwd)]
    return user_data if not user_data.empty else None

# --- INITIALISATION SESSION ---
if 'connected' not in st.session_state:
    st.session_state['connected'] = False
if 'verifying' not in st.session_state:
    st.session_state['verifying'] = False
if 'temp_user' not in st.session_state:
    st.session_state['temp_user'] = None

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

# --- INTERFACE AUTHENTIFICATION ---
def auth_page():
    st.markdown("<h1 style='text-align: center;'>🇬🇳 Bienvenue sur Kiké Saré</h1>", unsafe_allow_html=True)
    
    # Étape de vérification par code (Simulation SMS/Mail)
    if st.session_state['verifying']:
        st.info(f"📩 Un code de validation a été envoyé à : {st.session_state['temp_user']}")
        code_simule = "123456" # Dans un vrai système, ce code serait généré aléatoirement
        st.write(f"*(Simulation : Le code reçu est {code_simule})*")
        
        input_code = st.text_input("Entrez le code de validation")
        if st.button("Valider mon compte"):
            if input_code == code_simule:
                st.success("Compte validé avec succès ! Vous pouvez maintenant vous connecter.")
                st.session_state['verifying'] = False
            else:
                st.error("Code incorrect.")
        return

    choice = st.tabs(["Se connecter", "Créer un compte"])
    
    with choice[0]: # CONNEXION
        with st.form("login"):
            u = st.text_input("Email ou Numéro de téléphone")
            p = st.text_input("Mot de passe", type="password")
            if st.form_submit_button("Connexion"):
                user_row = verify_login(u, p)
                if user_row is not None:
                    st.session_state['connected'] = True
                    st.session_state['user_info'] = user_row.iloc[0].to_dict()
                    st.rerun()
                else:
                    st.error("Identifiants incorrects.")

    with choice[1]: # INSCRIPTION
        with st.form("signup"):
            new_u = st.text_input("Email ou Numéro (Identifiant)")
            new_n = st.text_input("Nom complet")
            new_p1 = st.text_input("Mot de passe", type="password")
            new_p2 = st.text_input("Confirmez le mot de passe", type="password")
            
            if st.form_submit_button("S'inscrire"):
                if new_u and new_n and new_p1:
                    if new_p1 != new_p2:
                        st.error("Les mots de passe ne correspondent pas.")
                    elif create_account(new_u, new_p1, new_n):
                        st.session_state['verifying'] = True
                        st.session_state['temp_user'] = new_u
                        st.rerun()
                    else:
                        st.error("Cet identifiant est déjà utilisé.")
                else:
                    st.warning("Veuillez remplir tous les champs.")

# --- APPLICATION PRINCIPALE ---
def main_app():
    with st.sidebar:
        st.title("🇬🇳 Kiké Saré")
        st.write(f"Bienvenue, \n**{st.session_state['user_info']['full_name']}**")
        if st.button("Déconnexion"):
            st.session_state['connected'] = False
            st.rerun()
    
st.header("Effectuer un paiement")

with st.form("pay"):
    nat = st.selectbox("Nature", ["Loyer", "Scolarité", "EDG/SEG"])
    mt = st.number_input("Montant (GNF)", min_value=0)
    ref = st.text_input("Référence")
    submit = st.form_submit_button("Valider")

# On gère l'action APRÈS le formulaire pour que le bouton de téléchargement reste visible
if submit:
    if mt > 0 and ref:
        st.success("✅ Paiement validé !")
        
        # Génération du PDF
        pdf = generer_pdf(st.session_state['user_info']['full_name'], nat, mt, ref)
        
        # Affichage du bouton de téléchargement
        st.download_button(
            label="📥 Télécharger le Reçu",
            data=pdf,
            file_name=f"recu_{ref}.pdf",
            mime="application/pdf"
        )
        st.balloons()
    else:
        st.error("Veuillez entrer un montant supérieur à 0 et une référence.")

# --- LANCEMENT ---
if not st.session_state['connected']:
    auth_page()
else:
    main_app()
