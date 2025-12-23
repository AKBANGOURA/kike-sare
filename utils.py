from datetime import datetime

def obtenir_statut_rappel():
    jour_du_mois = datetime.now().day
    
    if 1 <= jour_du_mois < 5:
        return {
            "couleur": "#d4edda", # Vert clair
            "texte": "🟢 Rappel : Votre loyer est disponible au paiement. Merci de votre fidélité.",
            "niveau": "Information"
        }
    elif 5 <= jour_du_mois < 10:
        return {
            "couleur": "#fff3cd", # Jaune/Orange clair
            "texte": "🟡 Rappel : Votre loyer n'a pas encore été réglé. Veuillez régulariser votre situation.",
            "niveau": "Avertissement"
        }
    else:
        return {
            "couleur": "#f8d7da", # Rouge clair
            "texte": "🔴 ALERTE : Paiement en retard. Merci de procéder au règlement immédiat pour éviter des frais.",
            "niveau": "Urgent"
        }

from reportlab.lib.pagesizes import A5
from reportlab.pdfgen import canvas
from reportlab.lib.units import cm
from datetime import datetime
import io

def generer_recu_pdf(transaction_id, nom_client, service, montant, mode):
    # On utilise un buffer mémoire pour que Streamlit puisse le télécharger directement
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=A5)
    width, height = A5

    # --- Design du Reçu ---
    c.setFont("Helvetica-Bold", 16)
    c.drawCentredString(width/2, height - 2*cm, "GUINÉE PAY - REÇU OFFICIEL")
    
    c.setFont("Helvetica", 10)
    c.drawCentredString(width/2, height - 2.5*cm, "Preuve de paiement numérique")
    c.line(1*cm, height - 3*cm, width - 1*cm, height - 3*cm)

    # --- Détails ---
    c.setFont("Helvetica", 11)
    y_position = height - 4.5*cm
    details = [
        f"Référence : {transaction_id}",
        f"Date : {datetime.now().strftime('%d/%m/%Y %H:%M')}",
        f"Client : {nom_client}",
        f"Service : {service}",
        f"Mode : {mode}"
    ]
    
    for detail in details:
        c.drawString(1.5*cm, y_position, detail)
        y_position -= 0.8*cm

    # --- Encadré Montant ---
    c.setFillColorRGB(0, 0.4, 0) # Vert foncé
    c.rect(1.5*cm, y_position - 1*cm, width - 3*cm, 1.2*cm, fill=1)
    c.setFillColorRGB(1, 1, 1) # Blanc
    c.setFont("Helvetica-Bold", 14)
    c.drawCentredString(width/2, y_position - 0.3*cm, f"TOTAL : {montant:,.0f} GNF")

    c.showPage()
    c.save()
    
    buffer.seek(0)
    return buffer