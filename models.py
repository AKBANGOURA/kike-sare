from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from datetime import datetime

engine = create_engine('sqlite:///guineepay.db', connect_args={"check_same_thread": False})
Base = declarative_base()

class Utilisateur(Base):
    __tablename__ = 'utilisateurs'
    id = Column(Integer, primary_key=True)
    nom = Column(String)
    telephone = Column(String, unique=True)
    email = Column(String, unique=True)
    mot_de_passe = Column(String)
    score_confiance = Column(Integer, default=50)

class Transaction(Base):
    __tablename__ = 'transactions'
    id = Column(Integer, primary_key=True)
    id_user = Column(Integer, ForeignKey('utilisateurs.id'))
    montant_total = Column(Float)
    type_service = Column(String) 
    moyen_paiement = Column(String) 
    est_echelonne = Column(Boolean, default=False)
    date_creation = Column(DateTime, default=datetime.utcnow)

# --- CETTE LIGNE MANQUAIT PROBABLEMENT ---
Session = sessionmaker(bind=engine) 

if __name__ == "__main__":
    Base.metadata.create_all(engine)
    print("✅ Base de données initialisée.")