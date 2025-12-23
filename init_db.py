from models import Session, Utilisateur, engine

# On crée une instance de la session
db = Session()

testeurs = [
    {"nom": "Alpha Diallo", "tel": "620000001", "email": "alpha@test.com", "pw": "pass123"},
    {"nom": "Mariama Barry", "tel": "620000002", "email": "mariama@test.com", "pw": "guinee2024"},
    # Ajoutez les autres ici...
]

try:
    for t in testeurs:
        # Vérifier si l'utilisateur existe déjà pour éviter les doublons
        exist = db.query(Utilisateur).filter(Utilisateur.telephone == t['tel']).first()
        if not exist:
            user = Utilisateur(
                nom=t['nom'], 
                telephone=t['tel'], 
                email=t['email'], 
                mot_de_passe=t['pw']
            )
            db.add(user)
    
    db.commit()
    print("✅ 7 testeurs inscrits avec succès !")
except Exception as e:
    print(f"❌ Erreur : {e}")
    db.rollback()
finally:
    db.close()