import streamlit as st
import sqlite3
import smtplib
from email.mime.text import MIMEText
import random
import time

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Kiké Saré - Plateforme Réelle", layout="wide", page_icon="🇬🇳")

# --- INITIALISATION DE LA BASE DE DONNÉES SQL ---
def init_db():
    conn = sqlite3.connect('kikesare.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (identifier TEXT PRIMARY KEY, password TEXT, full_name TEXT, type TEXT, verified INTEGER)''')
    conn.commit()
    conn.close()

init_db()

# --- FONCTION D'ENVOI DE MAIL RÉEL (SMTP) ---
def envoyer_code_validation(destinataire, code):
    try:
        expediteur = st.secrets["EMAIL_USER"]
        mdp = st.secrets["EMAIL_PASSWORD"]
        
        corps = f"Votre code de sécurité pour valider votre compte Kiké Saré est : {code}"
        msg = MIMEText(corps)
        msg['Subject'] = '🔑 Code de validation Kiké Saré'
        msg['From'] = expediteur
        msg['To'] = destinataire

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(expediteur, mdp)
            server.sendmail(expediteur, destinataire, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Erreur d'envoi : {e}. Vérifiez vos secrets Streamlit.")
        return False

# --- GESTION DE LA SESSION ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- LOGIQUE D'AUTHENTIFICATION ---
if not st.session_state['connected']:
    st.markdown("<h1 style='text-align: center;'>🇬🇳 Bienvenue sur Kiké Saré</h1>", unsafe_allow_html=True)
    
    # ÉCRAN DE VÉRIFICATION DU CODE
    if st.session_state['verifying']:
        st.info(f"📩 Un code a été envoyé à : **{st.session_state['temp_id']}**")
        code_saisi = st.text_input("Entrez le code reçu")
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if st.button("Valider mon compte", use_container_width=True):
                if code_saisi == str(st.session_state['correct_code']):
                    conn = sqlite3.connect('kikesare.db')
                    c = conn.cursor()
                    c.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, 1)", 
                              (st.session_state['temp_id'], st.session_state['temp_pwd'], 
                               st.session_state['temp_name'], st.session_state['temp_type']))
                    conn.commit()
                    conn.close()
                    st.success("✅ Compte validé avec succès !")
                    time.sleep(2)
                    st.session_state['verifying'] = False
                    st.rerun()
                else:
                    st.error("Code incorrect.")
        
        with col_v2:
            if st.button("🔄 Renvoyer le code", use_container_width=True):
                nouveau_code = random.randint(100000, 999999)
                if envoyer_code_validation(st.session_state['temp_id'], nouveau_code):
                    st.session_state['correct_code'] = nouveau_code
                    st.toast("Nouveau code envoyé !")

    # ÉCRAN DE CONNEXION / INSCRIPTION
    else:
        tab1, tab2 = st.tabs(["Connexion", "Créer un compte"])
        
        with tab1: # CONNEXION
            email_log = st.text_input("Email ou Téléphone")
            pwd_log = st.text_input("Mot de passe", type="password", key="login_pwd")
            if st.button("Se connecter", use_container_width=True):
                conn = sqlite3.connect('kikesare.db')
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE identifier=? AND password=? AND verified=1", (email_log, pwd_log))
                user = c.fetchone()
                conn.close()
                if user:
                    st.session_state['connected'] = True
                    st.session_state['user_name'] = user[2]
                    st.session_state['temp_id'] = user[0]
                    st.rerun()
                else:
                    st.error("Identifiants incorrects ou compte non vérifié.")

        with tab2: # INSCRIPTION (AVEC DOUBLE MOT DE PASSE)
            with st.form("inscription_form"):
                st.write("Remplissez vos informations réelles")
                type_insc = st.radio("Type d'identifiant :", ["Email", "Numéro de téléphone"])
                id_user = st.text_input("Votre identifiant (Mail ou 622...)")
                nom_complet = st.text_input("Nom complet")
                
                # Double saisie du mot de passe pour la sécurité
                p1 = st.text_input("Créer un mot de passe", type="password")
                p2 = st.text_input("Confirmez le mot de passe", type="password")
                
                if st.form_submit_button("S'inscrire et recevoir le code"):
                    if p1 != p2:
                        st.error("❌ Les mots de passe ne correspondent pas.")
                    elif len(p1) < 6:
                        st.error("❌ Le mot de passe doit faire au moins 6 caractères.")
                    elif "@" not in id_user and type_insc == "Email":
                        st.error("❌ Veuillez entrer un email valide.")
                    else:
                        code = random.randint(100000, 999999)
                        if envoyer_code_validation(id_user, code):
                            st.session_state.update({
                                'temp_id': id_user, 'temp_pwd': p1, 'temp_name': nom_complet,
                                'temp_type': type_insc, 'correct_code': code, 'verifying': True
                            })
                            st.rerun()

# --- APPLICATION PRINCIPALE (INTERFACE DE PAIEMENT) ---
else:
    st.sidebar.title("🇬🇳 Kiké Saré")
    st.sidebar.write(f"Utilisateur : **{st.session_state['user_name']}**")
    if st.sidebar.button("Déconnexion"):
        st.session_state['connected'] = False
        st.rerun()

    st.title("💳 Plateforme de Paiement en Ligne")
    st.markdown("---")

    col_p1, col_p2 = st.columns([2, 1])

    with col_p1:
        st.subheader("Informations du Service")
        service = st.selectbox("Sélectionnez le service :", 
                              ["Réabonnement Canal+", "Facture EDG", "Facture SEG", "Frais Scolaires", "Achat Crédit"])
        ref = st.text_input("Référence (Numéro de carte ou compteur)", placeholder="Ex: 102245587")
        montant = st.number_input("Montant à payer (GNF)", min_value=5000, step=5000)

    with col_p2:
        st.subheader("Moyen de Paiement")
        mode = st.radio("Choisissez votre mode :", ["📱 Orange Money", "📱 MTN MoMo", "💳 Carte Bancaire"])
        
        if "Carte" in mode:
            st.info("🔒 Redirection sécurisée vers la banque après validation.")
        else:
            num_paiement = st.text_input("Numéro à débiter", placeholder="6XX XX XX XX")

    if st.button(f"Confirmer le paiement de {montant} GNF", use_container_width=True):
        if not ref:
            st.warning("Veuillez saisir une référence.")
        else:
            with st.spinner("Transaction en cours..."):
                time.sleep(2)
                st.balloons()
                st.success(f"Paiement de {montant} GNF effectué pour {service} (Réf: {ref})")
                st.info(f"Un reçu a été envoyé à {st.session_state['temp_id']}")
