import sqlite3
from datetime import datetime
import time

def envoyer_notification(nom, telephone, email, type_rappel, couleur):
    """Simule l'envoi d'un SMS et d'un Email"""
    print(f"\n--- ENVOI DE NOTIFICATION ({couleur}) ---")
    print(f"Vers : {nom} ({telephone} | {email})")
    if couleur == "VERT":
        msg = "Bonjour, c'est le 1er du mois. Votre loyer/scolarité est prêt."
    elif couleur == "JAUNE":
        msg = "Attention, nous sommes le 5. Merci de régulariser votre paiement."
    else:
        msg = "URGENT : Retard constaté. Merci de payer immédiatement."
    
    print(f"Message envoyé : {msg}")
    # En production, on utiliserait ici : requests.post("API_SMS_URL", data=...)

def verifier_et_relancer():
    conn = sqlite3.connect('guineepay.db')
    cursor = conn.cursor()
    
    jour_actuel = datetime.now().day
    
    # On cherche les utilisateurs qui n'ont pas de transaction "Payé" ce mois-ci
    # (Logique simplifiée pour le prototype)
    cursor.execute("SELECT nom, telephone, id FROM utilisateurs")
    utilisateurs = cursor.fetchall()
    
    for user in utilisateurs:
        nom, tel, user_id = user
        email = f"{nom.lower().replace(' ', '.')}@example.com"
        
        if 1 <= jour_actuel < 5:
            envoyer_notification(nom, tel, email, "Rappel Doux", "VERT")
        elif 5 <= jour_actuel < 10:
            envoyer_notification(nom, tel, email, "Avertissement", "JAUNE")
        elif jour_actuel >= 10:
            envoyer_notification(nom, tel, email, "Urgence", "ROUGE")
            
    conn.close()

if __name__ == "__main__":
    print("🚀 Script de rappel automatique démarré...")
    verifier_et_relancer()