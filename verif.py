from models import Session, Utilisateur
db = Session()
users = db.query(Utilisateur).all()
for u in users:
    print(f"Nom: {u.nom} | Email: {u.email} | Pass: {u.mot_de_passe}")