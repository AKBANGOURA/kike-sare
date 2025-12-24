import streamlit as st
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io
import os

# --- CONFIGURATION ---
st.set_page_config(page_title="Kiké Saré - Officiel", layout="wide", page_icon="🇬🇳")

# --- GESTION AUTOMATIQUE DE LA BASE DE DONNÉES ---
USER_DB = "users_db.csv"

def initialiser_db():
    if os.path.exists(USER_DB):
        try:
            df_temp = pd.read_csv(USER_DB)
            if "identifier" not in df_temp.columns:
                os.remove(USER_DB)
        except Exception:
            os.remove(USER_DB)
    if not os.path.exists(USER_DB):
        df_init = pd.DataFrame(columns=["identifier", "password", "full_name", "verified"])
        df_init.to_csv(USER_DB, index=False)

initialiser_db()

# --- FONCTIONS UTILES ---
def create_account(identifier, pwd, name):
    df = pd.read_csv(USER_DB)
    if identifier in df['identifier'].values:
        return False
    new_user = pd.DataFrame([[identifier, pwd, name, False]], columns=["identifier", "password", "full_name", "verified"])
    new_user.to_csv(USER_DB, mode='a', header=False, index=False)
    return True

def verify_login(identifier, pwd):
    df = pd.read_csv(USER_DB)
    user_data = df[(df['identifier'] == identifier) & (df['password'] == pwd)]
    return user_data if not user_data.empty else None

def generer_pdf(nom, nature, montant, ref):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(300, 750, "REÇU DE PAIEMENT - KIKÉ SARÉ")
    c.line(100, 740, 500, 740)
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.drawString(100, 680, f"Client : {nom}")
    c.drawString(100, 660, f"Nature : {nature}")
    c.drawString(100, 640, f"Montant : {montant:,} GNF")
    c.drawString(100, 620, f"Référence : {ref}")
    c.save()
    buf.seek(0)
    return buf

# --- GESTION DES SESSIONS ---
if 'connected' not in st.session_state:
    st.session_state['connected'] = False
if 'verifying' not in st.session_state:
    st.session_state['verifying'] = False

# --- INTERFACE ---
if not st.session_state['connected']:
    # --- MODIFICATION ICI : TITRE AVEC DRAPEAU GUINÉEN ---
    st.markdown("<h1 style='text-align: center;'>🇬🇳 Bienvenue sur Kiké Saré</h1>", unsafe_allow_html=True)
    
    if st.session_state['verifying']:
        st.info(f"📩 Code de validation envoyé à : {st.session_state.get('temp_user', 'votre contact')}")
        st.write("*(Simulation : Utilisez le code **123456**)*")
        input_code = st.text_input("Entrez le code")
        if st.button("Valider mon compte"):
            if input_code == "123456":
                st.success("Compte validé ! Connectez-vous.")
                st.session_state['verifying'] = False
    else:
        choice = st.tabs(["Se connecter", "Créer un compte"])
        
        with choice[0]:
            with st.form("login"):
                u = st.text_input("Email ou Numéro")
                p = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("Connexion"):
                    user_row = verify_login(u, p)
                    if user_row is not None:
                        st.session_state['connected'] = True
                        st.session_state['user_info'] = user_row.iloc[0].to_dict()
                        st.rerun()
                    else:
                        st.error("Identifiants incorrects.")

        with choice[1]:
            with st.form("signup"):
                new_u = st.text_input("Email ou Numéro (Identifiant)")
                new_n = st.text_input("Nom complet")
                new_p1 = st.text_input("Mot de passe", type="password")
                new_p2 = st.text_input("Confirmez le mot de passe", type="password")
                if st.form_submit_button("S'inscrire"):
                    if new_p1 == new_p2 and new_u and new_n:
                        if create_account(new_u, new_p1, new_n):
                            st.session_state['verifying'] = True
                            st.session_state['temp_user'] = new_u
                            st.rerun()
                        else:
                            st.error("Identifiant déjà utilisé.")
                    else:
                        st.error("Erreur : Mots de passe différents ou champs vides.")

else:
    # --- APPLICATION CONNECTÉE ---
    with st.sidebar:
        st.title("🇬🇳 Kiké Saré")
        st.write(f"Utilisateur : **{st.session_state['user_info']['full_name']}**")
        if st.button("Déconnexion"):
            st.session_state['connected'] = False
            st.rerun()

    st.header("Effectuer un paiement")
    
    with st.form("pay"):
        nat = st.selectbox("Nature", ["Loyer", "Scolarité", "EDG/SEG"])
        mt = st.number_input("Montant (GNF)", min_value=0)
        ref = st.text_input("Référence")
        submit = st.form_submit_button("Valider")

    if submit:
        if mt > 0 and ref:
            st.success("✅ Paiement validé !")
            pdf = generer_pdf(st.session_state['user_info']['full_name'], nat, mt, ref)
            st.download_button("📥 Télécharger le Reçu", pdf, f"recu_{ref}.pdf", "application/pdf")
            st.balloons()
        else:
            st.error("Veuillez remplir tous les champs correctement.")
