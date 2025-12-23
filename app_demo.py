import streamlit as st
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Kiké Saré - Officiel", layout="wide", page_icon="🇬🇳")

# --- INITIALISATION DES VARIABLES DE SESSION ---
if 'connected' not in st.session_state:
    st.session_state['connected'] = False
if 'transactions' not in st.session_state:
    st.session_state['transactions'] = []

# --- FONCTION GÉNÉRATION PDF ---
def generer_pdf(nom, nature, montant, ref):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    # Entête
    c.setFont("Helvetica-Bold", 18)
    c.drawCentredString(300, 750, "REÇU DE PAIEMENT - KIKÉ SARÉ")
    c.line(100, 740, 500, 740)
    
    # Détails
    c.setFont("Helvetica", 12)
    c.drawString(100, 700, f"Date et Heure : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.drawString(100, 680, f"Bénéficiaire : {nom}")
    c.drawString(100, 660, f"Nature du règlement : {nature}")
    c.setFont("Helvetica-Bold", 12)
    c.drawString(100, 640, f"Montant payé : {montant:,} GNF")
    c.setFont("Helvetica", 12)
    c.drawString(100, 620, f"Référence de transaction : {ref}")
    
    # Pied de page
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(100, 550, "Ce document fait office de preuve de paiement officielle via la plateforme Kiké Saré.")
    c.showPage()
    c.save()
    buf.seek(0)
    return buf

# --- SYSTÈME D'AUTHENTIFICATION ---
def login_page():
    st.markdown("<h1 style='text-align: center;'>🔐 Connexion Kiké Saré</h1>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        with st.form("login_form"):
            user = st.text_input("Identifiant (Prénom)")
            password = st.text_input("Mot de passe", type="password")
            submit_login = st.form_submit_button("Se connecter")
            
            if submit_login:
                if user.lower() == "almamy" and password == "Guinee2025":
                    st.session_state['connected'] = True
                    st.session_state['user_full_name'] = "Almamy BANGOURA"
                    st.rerun()
                else:
                    st.error("Identifiants incorrects. Veuillez réessayer.")

# --- APPLICATION PRINCIPALE ---
def main_app():
    # Barre latérale
    with st.sidebar:
        st.title("🇬🇳 Kiké Saré")
        st.write(f"👤 **{st.session_state['user_full_name']}**")
        st.divider()
        menu = st.radio("Navigation", ["📱 Effectuer un paiement", "📊 Historique & Admin"])
        st.divider()
        if st.button("🚪 Déconnexion"):
            st.session_state['connected'] = False
            st.rerun()

    # Page de Paiement
    if menu == "📱 Effectuer un paiement":
        st.title("Effectuer un paiement")
        
        col_form, col_info = st.columns([2, 1])
        
        with col_form:
            with st.form("pay_form", clear_on_submit=False):
                nature = st.selectbox("Type de paiement", ["Loyer", "Scolarité", "Facture EDG/SEG", "Autre"])
                montant = st.number_input("Montant (GNF)", min_value=1000, step=5000)
                ref = st.text_input("Référence du paiement (ex: Mois ou N° Facture)")
                valider = st.form_submit_button("Valider la transaction")

            if valider:
                if ref:
                    # Sauvegarde locale
                    nouvelle_trans = {
                        "Date": datetime.now().strftime("%d/%m/%Y"),
                        "Nature": nature,
                        "Montant": montant,
                        "Référence": ref
                    }
                    st.session_state['transactions'].append(nouvelle_trans)
                    
                    st.success("✅ Paiement enregistré !")
                    
                    # Préparation du Reçu
                    pdf = generer_pdf(st.session_state['user_full_name'], nature, montant, ref)
                    st.download_button(
                        label="📥 Télécharger mon reçu PDF",
                        data=pdf,
                        file_name=f"recu_kikesare_{ref}.pdf",
                        mime="application/pdf"
                    )
                    st.balloons()
                else:
                    st.warning("Veuillez saisir une référence.")

        with col_info:
            st.info("""
            **Note aux testeurs :** Chaque transaction génère un reçu unique. Assurez-vous de télécharger votre reçu immédiatement après la validation.
            """)

    # Page Admin / Historique
    elif menu == "📊 Historique & Admin":
        st.title("Tableau de bord")
        if not st.session_state['transactions']:
            st.write("Aucune transaction effectuée pour le moment.")
        else:
            df = pd.DataFrame(st.session_state['transactions'])
            st.metric("Total des encaissements", f"{df['Montant'].sum():,} GNF")
            st.dataframe(df, use_container_width=True)

# --- LANCEMENT ---
if not st.session_state['connected']:
    login_page()
else:
    main_app()
