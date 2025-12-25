import streamlit as st
import sqlite3
import random
from datetime import datetime, timedelta

# --- 1. CONFIGURATION ---
st.set_page_config(page_title="Kiké Saré - Fintech", layout="wide", page_icon="🇬🇳")

def display_logo():
    st.markdown("""
        <div style="text-align: center;">
            <h1 style="color: #ce1126; margin-bottom: 0;">KIKÉ SARÉ</h1>
            <p style="color: #009460; font-style: italic; font-weight: bold;">La Fintech Guinéenne</p>
            <hr style="border: 1px solid #fcd116; width: 50%;">
        </div>
        """, unsafe_allow_html=True)

# --- 2. BASE DE DONNÉES ---
def get_db_connection():
    return sqlite3.connect('kikesare.db', check_same_thread=False)

def init_db():
    conn = get_db_connection()
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users 
                 (identifier TEXT PRIMARY KEY, password TEXT, full_name TEXT, type TEXT, 
                  verified INTEGER, profile_pic BLOB, siret TEXT, methode_reception TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS historique 
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id TEXT, service TEXT, montant REAL, 
                  date_paiement DATETIME, moyen TEXT, reference TEXT, entrepreneur_id TEXT)''')
    conn.commit()
    conn.close()

init_db()

# --- 3. SESSION STATE ---
if 'connected' not in st.session_state: st.session_state['connected'] = False
if 'verifying' not in st.session_state: st.session_state['verifying'] = False

# --- 4. ACCÈS (LOGIN/SIGNUP) ---
if not st.session_state['connected']:
    display_logo()
    if st.session_state['verifying']:
        st.info(f"📩 Code envoyé à : **{st.session_state['temp_id']}**")
        code_s = st.text_input("Code de validation")
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Valider"):
                if code_s == str(st.session_state['correct_code']):
                    conn = get_db_connection()
                    conn.execute("INSERT OR REPLACE INTO users (identifier, password, full_name, type, verified, siret) VALUES (?, ?, ?, ?, 1, ?)", 
                                (st.session_state['temp_id'], st.session_state['temp_pwd'], st.session_state['temp_name'], st.session_state['temp_type'], st.session_state.get('temp_siret', '')))
                    conn.commit(); conn.close()
                    st.success("Compte activé !"); st.session_state['verifying'] = False; st.rerun()
        with col2:
            if st.button("🔄 Renvoyer le code"):
                st.session_state['correct_code'] = random.randint(100000, 999999)
                st.toast(f"Nouveau code : {st.session_state['correct_code']}")
    else:
        t1, t2 = st.tabs(["🔐 Connexion", "📝 Inscription"])
        with t1:
            e_log = st.text_input("Identifiant")
            p_log = st.text_input("Mot de passe", type="password")
            if st.button("Se connecter"):
                conn = get_db_connection()
                user = conn.execute("SELECT * FROM users WHERE identifier=? AND password=? AND verified=1", (e_log, p_log)).fetchone()
                conn.close()
                if user:
                    st.session_state.update({'connected': True, 'user_name': user[2], 'user_id': user[0], 'user_type': user[3]})
                    st.rerun()
        with t2:
            u_role = st.radio("Vous êtes :", ["Particulier", "Entrepreneur (Entreprise)"], horizontal=True)
            with st.form("inscription"):
                if u_role == "Particulier":
                    nom_f = f"{st.text_input('Prénom')} {st.text_input('Nom')}"
                    siret = ""
                else:
                    nom_f = st.text_input("Nom de l'entreprise (ex: Groupe AKB)")
                    siret = st.text_input("N° SIRET / RCCM")
                ident = st.text_input("Email ou Téléphone")
                pwd = st.text_input("Mot de passe", type="password")
                if st.form_submit_button("🚀 Suivant"):
                    code = random.randint(100000, 999999)
                    st.session_state.update({'temp_id': ident, 'temp_pwd': pwd, 'temp_name': nom_f, 'temp_type': u_role, 'temp_siret': siret, 'correct_code': code, 'verifying': True})
                    st.rerun()

# --- 5. LOGIQUE DES ESPACES ---
else:
    with st.sidebar:
        st.write(f"### {st.session_state['user_name']}")
        st.caption(f"Compte {st.session_state['user_type']}")
        if st.button("🔌 Déconnexion"):
            st.session_state['connected'] = False; st.rerun()

    # ESPACE ENTREPRENEUR (GROUPE AKB)
    if st.session_state['user_type'] != "Particulier":
        st.title("💼 Dashboard de Gestion Business")
        tab_b1, tab_b2, tab_b3 = st.tabs(["📈 Revenus & Statistiques", "💰 Mode de Réception", "📑 Historique Clients"])
        
        with tab_b1:
            st.subheader("Aperçu financier")
            c1, c2, c3 = st.columns(3)
            # Données simulées pour la démonstration
            c1.metric("🏠 Loyers Encaissés", "12.500.000 GNF", "+5%")
            c2.metric("🎓 Frais de Scolarité", "8.200.000 GNF", "+12%")
            c3.metric("🛍️ Ventes Marchandises", "4.150.000 GNF")
            
            st.markdown("---")
            st.write("### 📊 Évolution des encaissements")
            st.bar_chart({"Loyers": [10, 12, 11, 12.5], "Scolarité": [5, 7, 6, 8.2]})

        with tab_b2:
            st.subheader("Où souhaitez-vous recevoir vos fonds ?")
            with st.form("reception_config"):
                methode = st.selectbox("Choisir un compte de réception", ["Orange Money Business", "MTN MoMo Business", "Compte Bancaire (Virement)"])
                num_compte = st.text_input("Numéro de compte ou téléphone de réception", placeholder="Ex: 622 00 00 00")
                banque = st.text_input("Nom de la Banque (si virement)")
                if st.form_submit_button("💾 Enregistrer la méthode"):
                    st.success(f"Vos fonds seront désormais transférés vers : {methode} ({num_compte})")

        with tab_b3:
            st.subheader("Paiements reçus")
            st.info("La liste détaillée des clients (Nom, Service, Date, Montant) s'affichera ici.")

    # ESPACE PARTICULIER
    else:
        st.title("📱 Mon Portefeuille")
        # Logique de paiement (Frais scolarité, loyer, etc.)
        st.write("Bienvenue dans votre espace de paiement simplifié.")
