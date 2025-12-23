import streamlit as st
import pandas as pd
import re
import random
from datetime import datetime
from sqlalchemy.orm import sessionmaker
from models import engine, Transaction, Utilisateur
from utils import generer_recu_pdf, obtenir_statut_rappel

# Initialisation de la base de données
Session = sessionmaker(bind=engine)
db = Session()

st.set_page_config(page_title="Kiké Saré", page_icon="🇬🇳", layout="wide")

# --- FONCTIONS DE SÉCURITÉ ---
def est_mot_de_passe_robuste(password):
    if len(password) < 8:
        return False, "8 caractères minimum."
    if not re.search("[a-z]", password) or not re.search("[A-Z]", password):
        return False, "Il faut des majuscules et minuscules."
    if not re.search("[0-9]", password):
        return False, "Il faut au moins un chiffre."
    if not re.search("[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "Il faut un caractère spécial."
    return True, "OK"

# --- GESTION DE LA SESSION ---
if "user_id" not in st.session_state:
    st.session_state["user_id"] = None
if "verif_code" not in st.session_state:
    st.session_state["verif_code"] = None
if "temp_user" not in st.session_state:
    st.session_state["temp_user"] = None

# --- ECRAN D'ACCÈS (AUTHENTIFICATION) ---
if st.session_state["user_id"] is None:
    st.title("🇬🇳 Kiké Saré")
    st.write("Le paiement du mois en toute simplicité.")

    # Si un code de validation est en attente
    if st.session_state["verif_code"]:
        st.info(f"Code envoyé à {st.session_state['temp_user']['email']}")
        with st.form("form_verif"):
            code_input = st.text_input("Entrez le code à 4 chiffres")
            if st.form_submit_button("Activer mon compte"):
                if code_input == str(st.session_state["verif_code"]):
                    u = st.session_state["temp_user"]
                    nouveau = Utilisateur(nom=u['nom'], telephone=u['tel'], email=u['email'], mot_de_passe=u['pw'])
                    db.add(nouveau)
                    db.commit()
                    st.success("✅ Compte activé ! Connectez-vous.")
                    st.session_state["verif_code"] = None
                else:
                    st.error("Code incorrect.")
    
    else:
        tab1, tab2 = st.tabs(["Connexion", "Création de compte"])
        
        with tab1:
            with st.form("login_form"):
                identifiant = st.text_input("Email ou Téléphone")
                mdp = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("Se connecter"):
                    user = db.query(Utilisateur).filter(
                        ((Utilisateur.telephone == identifiant) | (Utilisateur.email == identifiant)) & 
                        (Utilisateur.mot_de_passe == mdp)
                    ).first()
                    if user:
                        st.session_state["user_id"] = user.id
                        st.session_state["user_nom"] = user.nom
                        st.rerun()
                    else:
                        st.error("Identifiants incorrects.")

        with tab2:
            with st.form("signup_form"):
                nom = st.text_input("Nom complet")
                tel = st.text_input("Numéro de téléphone")
                email = st.text_input("Email")
                pw = st.text_input("Mot de passe", type="password")
                cpw = st.text_input("Confirmer le mot de passe", type="password")
                if st.form_submit_button("S'inscrire"):
                    robuste, msg = est_mot_de_passe_robuste(pw)
                    if not (nom and tel and email and pw):
                        st.warning("Veuillez remplir tous les champs.")
                    elif not robuste:
                        st.error(f"Sécurité : {msg}")
                    elif pw != cpw:
                        st.error("Les mots de passe ne correspondent pas.")
                    else:
                        code = random.randint(1000, 9999)
                        st.session_state["verif_code"] = code
                        st.session_state["temp_user"] = {'nom':nom, 'tel':tel, 'email':email, 'pw':pw}
                        st.toast(f"CODE DE TEST : {code}") # Affiche le code en bas à droite
                        st.rerun()
    st.stop()

# --- INTERFACE PRINCIPALE (APRES CONNEXION) ---
with st.sidebar:
    st.title("Kiké Saré")
    st.write(f"Connecté : **{st.session_state['user_nom']}**")
    page = st.radio("Menu", ["📱 Mon Portail", "💼 Admin"])
    if st.button("Déconnexion"):
        st.session_state["user_id"] = None
        st.rerun()

if page == "📱 Mon Portail":
    st.header("Effectuer un paiement")
    # ... reste de votre code de paiement ici ...
else:
    st.title("Administration")
    # ... code admin ...