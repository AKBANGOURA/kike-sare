import streamlit as st
import sqlite3
import random
import smtplib
from email.message import EmailMessage

# --- 1. CONFIGURATION MAIL (Paramètres à configurer) ---
EMAIL_SENDER = "votre-mail@gmail.com" 
EMAIL_PASSWORD = "votre-mot-de-passe-application" 

def send_validation_mail(receiver, code):
    msg = EmailMessage()
    msg.set_content(f"Bienvenue sur Kiké Saré ! Votre code de validation est : {code}")
    msg['Subject'] = "Validation de compte - Kiké Saré"
    msg['From'] = EMAIL_SENDER
    msg['To'] = receiver
    try:
        with smtplib.SMTP_SSL('smtp.gmail.com', 465) as smtp:
            smtp.login(EMAIL_SENDER, EMAIL_PASSWORD)
            smtp.send_message(msg)
        return True
    except Exception: return False

# --- 2. INITIALISATION ET RÉPARATION DE LA BASE DE DONNÉES ---
def init_db():
    conn = sqlite3.connect('kikesare.db', check_same_thread=False)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (id TEXT PRIMARY KEY, pwd TEXT, name TEXT, type TEXT, verified INT)''')
    # Ajout de la colonne siret si elle manque pour éviter l'OperationalError
    try:
        c.execute("ALTER TABLE users ADD COLUMN siret TEXT")
    except sqlite3.OperationalError: pass
    conn.commit()
    conn.close()

init_db()

# --- 3. ÉTAT DE LA SESSION ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- 4. ACCÈS : CONNEXION & INSCRIPTION ---
if not st.session_state['connected']:
    st.markdown("<h1 style='text-align:center; color:#ce1126;'>KIKÉ SARÉ</h1>", unsafe_allow_html=True)
    st.markdown("<p style='text-align:center; color:#009460; font-weight:bold;'>La Fintech Guinéenne</p>", unsafe_allow_html=True)

    if st.session_state['verifying']:
        # ÉCRAN DE VÉRIFICATION
        st.info(f"📩 Un code de validation a été envoyé à : **{st.session_state['temp_id']}**")
        code_s = st.text_input("Saisissez le code de validation")
        col_v1, col_v2 = st.columns(2)
        with col_v1:
            if st.button("✅ Valider l'inscription"):
                if code_s == str(st.session_state['correct_code']):
                    conn = sqlite3.connect('kikesare.db')
                    conn.execute("INSERT OR REPLACE INTO users (id, pwd, name, type, verified, siret) VALUES (?, ?, ?, ?, 1, ?)", 
                                (st.session_state['temp_id'], st.session_state['temp_pwd'], 
                                 st.session_state['temp_name'], st.session_state['temp_type'], st.session_state.get('temp_siret', '')))
                    conn.commit(); conn.close()
                    st.success("Compte activé ! Veuillez vous connecter."); st.session_state['verifying'] = False; st.rerun()
        with col_v2:
            if st.button("🔄 Renvoyer le code"):
                new_c = random.randint(100000, 999999)
                st.session_state['correct_code'] = new_c
                if send_validation_mail(st.session_state['temp_id'], new_c):
                    st.toast("Nouveau code envoyé par mail !")

    else:
        tab1, tab2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
        
        with tab1:
            e_log = st.text_input("Email", key="login_email")
            p_log = st.text_input("Mot de passe", type="password", key="login_pwd")
            if st.button("Se connecter"):
                conn = sqlite3.connect('kikesare.db')
                u = conn.execute("SELECT * FROM users WHERE id=? AND pwd=? AND verified=1", (e_log, p_log)).fetchone()
                conn.close()
                if u:
                    st.session_state.update({'connected': True, 'user_name': u[2], 'user_id': u[0], 'user_type': u[3]})
                    st.rerun()
                else: st.error("Identifiants incorrects ou compte non vérifié.")

        with tab2:
            # 1. LE CHOIX DU TYPE EN PREMIER
            u_role = st.radio("Vous souhaitez créer un compte :", ["Particulier", "Entrepreneur (Entreprise/Commerce)"], horizontal=True)
            
            with st.form("inscription_form"):
                # 2. CHAMPS CONDITIONNELS
                if u_role == "Particulier":
                    prenom = st.text_input("Prénom")
                    nom = st.text_input("Nom")
                    nom_final = f"{prenom} {nom}"
                    siret_val = ""
                else:
                    nom_final = st.text_input("Nom de l'Entreprise / Commerce")
                    siret_val = st.text_input("Numéro SIRET / RCCM")
                
                email_ins = st.text_input("Votre Email (pour validation)")
                
                # 3. DOUBLE MOT DE PASSE
                p1 = st.text_input("Mot de passe", type="password")
                p2 = st.text_input("Confirmez le mot de passe", type="password")
                
                if st.form_submit_button("🚀 Recevoir mon code par mail"):
                    if p1 != p2: st.error("Les mots de passe ne correspondent pas.")
                    elif len(p1) < 6: st.error("Le mot de passe est trop court (min 6 car.).")
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
                        else: st.error("Erreur d'envoi du mail. Vérifiez votre connexion ou paramètres SMTP.")

# --- 5. ESPACES UTILISATEURS ---
else:
    with st.sidebar:
        st.write(f"### {st.session_state['user_name']}")
        st.caption(f"Profil : {st.session_state['user_type']}")
        if st.button("🔌 Déconnexion"): st.session_state['connected'] = False; st.rerun()

    # --- ESPACE PARTICULIER : PAIEMENTS ---
    if st.session_state['user_type'] == "Particulier":
        st.title("📱 Mon Portefeuille de Paiement")
        t_pay, t_hist = st.tabs(["💳 Effectuer un Règlement", "📜 Historique"])
        with t_pay:
            st.subheader("Nouvelle transaction")
            col_a, col_b = st.columns(2)
            with col_a:
                service = st.selectbox("Payer pour :", ["🎓 Frais de Scolarité", "🏠 Loyer", "💡 Facture EDG/SEG", "🛍️ Achat Commerçant"])
                ref = st.text_input("Référence (N° Facture / Étudiant)")
                montant = st.number_input("Montant (GNF)", min_value=1000)
            with col_b:
                moyen = st.radio("Moyen de paiement :", ["Orange Money", "MTN MoMo", "Carte Visa"], horizontal=True)
                modalite = st.selectbox("Modalité", ["Comptant", "Échelonné (2 fois)", "Échelonné (3 fois)"])
            
            if st.button("💎 Valider le Règlement"):
                st.balloons(); st.success(f"Paiement de {montant} GNF validé pour {service} !")

    # --- ESPACE ENTREPRENEUR GÉNÉRIQUE ---
    else:
        st.title(f"💼 Dashboard Business : {st.session_state['user_name']}")
        t_stats, t_fond, t_clients = st.tabs(["📈 Mes Revenus", "💰 Réception des fonds", "👥 Liste des Clients"])
        
        with t_stats:
            st.subheader(f"Statistiques financières de {st.session_state['user_name']}")
            c1, c2, c3 = st.columns(3)
            # Valeurs simulées pour l'interface
            c1.metric("Total encaissé", "0 GNF", delta="Nouveau")
            c2.metric("Transactions", "0")
            c3.metric("Moyenne/Client", "0 GNF")
            st.info("Le graphique des revenus s'affichera ici dès la première transaction.")

        with t_fond:
            st.subheader("Configuration du compte de réception")
            st.write("Choisissez où vous souhaitez que Kiké Saré transfère l'argent collecté.")
            with st.form("config_recep"):
                m_recep = st.selectbox("Canal de réception", ["Orange Money Business", "MTN MoMo Business", "Compte Bancaire"])
                n_recep = st.text_input("Numéro ou RIB de réception")
                if st.form_submit_button("💾 Enregistrer les paramètres"):
                    st.success(f"Moyen de réception mis à jour pour {st.session_state['user_name']}.")
