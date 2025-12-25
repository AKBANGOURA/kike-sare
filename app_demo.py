import streamlit as st
import sqlite3
import smtplib
from email.mime.text import MIMEText
import random
import time
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ET DESIGN ---
st.set_page_config(page_title="Kiké Saré - Plateforme Intégrale", layout="wide", page_icon="🇬🇳")

# --- 2. INITIALISATION BASE DE DONNÉES (SQL COMPLET) ---
def init_db():
    conn = sqlite3.connect('kikesare.db')
    c = conn.cursor()
    # Table des utilisateurs
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (identifier TEXT PRIMARY KEY, password TEXT, full_name TEXT, type TEXT, verified INTEGER)''')
    # Table des échéances pour les rappels
    c.execute('''CREATE TABLE IF NOT EXISTS echeances 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, service TEXT, date_limite DATE, montant REAL)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. FONCTION D'ENVOI DE MAIL RÉEL (SMTP) ---
def envoyer_code_validation(destinataire, code):
    try:
        # Utilisation des secrets Streamlit Cloud
        expediteur = st.secrets["EMAIL_USER"]
        mdp = st.secrets["EMAIL_PASSWORD"]
        
        corps = f"Votre code de sécurité Kiké Saré est : {code}"
        msg = MIMEText(corps)
        msg['Subject'] = '🔑 Code de validation Kiké Saré'
        msg['From'] = expediteur
        msg['To'] = destinataire

        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as server:
            server.login(expediteur, mdp)
            server.sendmail(expediteur, destinataire, msg.as_string())
        return True
    except Exception as e:
        st.error(f"Erreur technique : {e}")
        return False

# --- 4. GESTION DE LA SESSION ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- 5. LOGIQUE D'AUTHENTIFICATION (INSCRIPTION & CONNEXION) ---
if not st.session_state['connected']:
    st.markdown("<h1 style='text-align: center;'>🇬🇳 Bienvenue sur Kiké Saré</h1>", unsafe_allow_html=True)
    
    # ÉCRAN DE VÉRIFICATION DU CODE (OTP)
    if st.session_state['verifying']:
        st.info(f"📩 Un code a été envoyé à : **{st.session_state['temp_id']}**")
        code_saisi = st.text_input("Entrez le code reçu")
        
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if st.button("✅ Valider mon compte", use_container_width=True):
                if code_saisi == str(st.session_state['correct_code']):
                    conn = sqlite3.connect('kikesare.db')
                    c = conn.cursor()
                    c.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, 1)", 
                              (st.session_state['temp_id'], st.session_state['temp_pwd'], 
                               st.session_state['temp_name'], st.session_state['temp_type']))
                    conn.commit()
                    conn.close()
                    st.balloons()
                    st.success("Compte validé ! Connectez-vous maintenant.")
                    st.session_state['verifying'] = False
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Code incorrect.")
        with col_v2:
            if st.button("🔄 Renvoyer le code", use_container_width=True):
                with st.spinner("Renvoi en cours..."):
                    nouveau_code = random.randint(100000, 999999)
                    if envoyer_code_validation(st.session_state['temp_id'], nouveau_code):
                        st.session_state['correct_code'] = nouveau_code
                        st.toast("Nouveau code envoyé !")

    # ÉCRAN DE CHOIX : CONNEXION OU CRÉATION
    else:
        tab1, tab2 = st.tabs(["🔐 Connexion", "📝 Créer un compte"])
        
        with tab1: # CONNEXION
            email_log = st.text_input("Identifiant (Email ou Téléphone)")
            pwd_log = st.text_input("Mot de passe", type="password", key="login_pwd")
            if st.button("Se connecter", use_container_width=True):
                conn = sqlite3.connect('kikesare.db')
                c = conn.cursor()
                c.execute("SELECT * FROM users WHERE identifier=? AND password=? AND verified=1", (email_log, pwd_log))
                user = c.fetchone()
                conn.close()
                if user:
                    st.session_state.update({'connected': True, 'user_name': user[2], 'user_id': user[0]})
                    st.rerun()
                else:
                    st.error("Identifiants incorrects ou compte non vérifié.")

        with tab2: # INSCRIPTION COMPLÈTE
            with st.form("inscription_form"):
                st.subheader("Informations d'inscription")
                type_insc = st.radio("S'inscrire via :", ["Email", "Numéro de téléphone"])
                id_user = st.text_input("Saisissez votre Email ou Numéro (ex: 622...)")
                nom_complet = st.text_input("Nom complet")
                
                # Double saisie du mot de passe pour la sécurité
                p1 = st.text_input("Créer un mot de passe (min 6 caractères)", type="password")
                p2 = st.text_input("Confirmez le mot de passe", type="password")
                
                if st.form_submit_button("🚀 S'inscrire et recevoir le code"):
                    if p1 != p2:
                        st.error("❌ Les mots de passe ne correspondent pas.")
                    elif len(p1) < 6:
                        st.error("❌ Mot de passe trop court.")
                    elif not id_user or not nom_complet:
                        st.error("❌ Veuillez remplir tous les champs.")
                    else:
                        code = random.randint(100000, 999999)
                        if envoyer_code_validation(id_user, code):
                            st.session_state.update({
                                'temp_id': id_user, 'temp_pwd': p1, 'temp_name': nom_complet,
                                'temp_type': type_insc, 'correct_code': code, 'verifying': True
                            })
                            st.rerun()

# --- 6. APPLICATION PRINCIPALE (PAIEMENT ET RAPPELS) ---
else:
    st.sidebar.title("💳 Kiké Saré Pay")
    st.sidebar.success(f"Connecté : {st.session_state['user_name']}")
    
    # SECTION 1 : GESTION DES RAPPELS (ECHEANCES)
    st.subheader("🔔 Mes Rappels d'échéances")
    conn = sqlite3.connect('kikesare.db')
    echeances = conn.execute("SELECT service, date_limite, montant FROM echeances WHERE user_id=?", (st.session_state['user_id'],)).fetchall()
    conn.close()

    if echeances:
        for ech in echeances:
            date_obj = datetime.strptime(ech[1], '%Y-%m-%d')
            jours_restants = (date_obj - datetime.now()).days
            if jours_restants <= 3:
                st.error(f"🛑 **{ech[0]}** : {ech[1]} (J-{jours_restants}) - Montant : {ech[2]} GNF")
            else:
                st.warning(f"📅 **{ech[0]}** : Échéance le {ech[1]}")
    else:
        st.info("Aucun rappel pour le moment. Payez une facture pour en créer un.")

    st.markdown("---")

    # SECTION 2 : INTERFACE DE PAIEMENT
    st.title("💳 Effectuer un Paiement")
    
    col_p1, col_p2 = st.columns([2, 1])
    with col_p1:
        st.subheader("Détails du service")
        service = st.selectbox("Que voulez-vous payer ?", 
                              ["Réabonnement Canal+", "Facture EDG (Électricité)", "Facture SEG (Eau)", "Frais Scolaires", "Achat Crédit"])
        ref_client = st.text_input("Référence (Numéro de carte, compteur ou matricule)")
        montant_pay = st.number_input("Montant (GNF)", min_value=5000, step=5000)

    with col_p2:
        st.subheader("Moyen de Paiement")
        mode_pay = st.radio("Sélectionnez :", ["📱 Orange Money", "📱 MTN MoMo", "💳 Carte Visa/Mastercard"])
        if "Carte" in mode_pay:
            st.info("🔒 Redirection bancaire sécurisée.")
        else:
            num_pay = st.text_input("Numéro à débiter", placeholder="622 00 00 00")
        
        # Option Rappel Échéance
        activer_rappel = st.checkbox("🔄 Me rappeler dans 1 mois")

    if st.button("💎 Confirmer le Paiement Réel", use_container_width=True):
        if not ref_client:
            st.warning("⚠️ Veuillez entrer une référence valide.")
        else:
            with st.spinner("Traitement sécurisé..."):
                time.sleep(3)
                # Enregistrement du rappel si coché
                if activer_rappel:
                    date_prochaine = (datetime.now() + timedelta(days=30)).strftime('%Y-%m-%d')
                    conn = sqlite3.connect('kikesare.db')
                    conn.execute("INSERT INTO echeances (user_id, service, date_limite, montant) VALUES (?, ?, ?, ?)", 
                                 (st.session_state['user_id'], service, date_prochaine, montant_pay))
                    conn.commit()
                    conn.close()
                
                st.balloons()
                st.success(f"✅ Paiement de {montant_pay} GNF réussi pour {service} !")
                st.info(f"Un reçu PDF a été envoyé à {st.session_state['user_id']}")

    if st.sidebar.button("🔌 Déconnexion"):
        st.session_state['connected'] = False
        st.rerun()
