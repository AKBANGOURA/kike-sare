import streamlit as st
import pandas as pd
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
import io

# --- FONCTION GÉNÉRATION PDF ---
def generer_pdf(nom, nature, montant, ref):
    buf = io.BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(100, 750, "REÇU DE PAIEMENT - KIKÉ SARÉ")
    c.line(100, 745, 500, 745)
    
    c.setFont("Helvetica", 12)
    c.drawString(100, 710, f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    c.drawString(100, 690, f"Client : {nom}")
    c.drawString(100, 670, f"Nature : {nature}")
    c.drawString(100, 650, f"Montant : {montant:,} GNF")
    c.drawString(100, 630, f"Référence : {ref}")
    
    c.setFont("Helvetica-Oblique", 10)
    c.drawString(100, 580, "Merci pour votre confiance. Document généré numériquement.")
    c.showPage()
    c.save()
    buf.seek(0)
    return buf

# --- CONFIGURATION PAGE ---
st.set_page_config(page_title="Kiké Saré", layout="wide")

# --- INTERFACE ---
with st.sidebar:
    st.title("🇬🇳 Kiké Saré")
    user_nom = "Almamy BANGOURA"
    st.write(f"**Connecté :** {user_nom}")
    page = st.radio("Menu", ["📱 Mon Portail", "📊 Admin"])

if page == "📱 Mon Portail":
    st.header("Effectuer un paiement")
    
    with st.form("form_paiement", clear_on_submit=False):
        nature = st.selectbox("Nature", ["Loyer", "Scolarité", "Facture", "Autre"])
        montant = st.number_input("Montant (GNF)", min_value=0)
        ref = st.text_input("Référence")
        valider = st.form_submit_button("Confirmer le paiement")

    if valider:
        if montant > 0 and ref:
            st.success("✅ Transaction enregistrée !")
            
            # Génération du fichier PDF
            pdf_file = generer_pdf(user_nom, nature, montant, ref)
            
            # BOUTON DE TÉLÉCHARGEMENT
            st.download_button(
                label="📥 Télécharger mon reçu PDF",
                data=pdf_file,
                file_name=f"recu_{ref}.pdf",
                mime="application/pdf"
            )
        else:
            st.error("Veuillez remplir tous les champs.")
