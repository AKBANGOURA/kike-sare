import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURATION DE LA PAGE ---
st.set_page_config(page_title="Kiké Saré - Gestion de Paiements", layout="wide")

# --- STYLE PERSONNALISÉ ---
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .stButton>button { width: 100%; border-radius: 5px; height: 3em; background-color: #007bff; color: white; }
    .stHeader { color: #1E3A8A; }
    </style>
    """, unsafe_allow_html=True)

# --- SIMULATION DE BASE DE DONNÉES (Session State) ---
if 'transactions' not in st.session_state:
    st.session_state['transactions'] = []

# --- BARRE LATÉRALE (SIDEBAR) ---
with st.sidebar:
    st.title("🇬🇳 Kiké Saré")
    st.write(f"**Connecté :** Almamy BANGOURA")
    st.divider()
    page = st.radio("Menu", ["📱 Mon Portail", "📊 Admin", "⚙️ Paramètres"])
    st.divider()
    if st.button("Déconnexion"):
        st.info("Déconnexion réussie")

# --- LOGIQUE DES PAGES ---

# PAGE 1 : PORTAIL UTILISATEUR
if page == "📱 Mon Portail":
    st.title("Effectuer un paiement")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        with st.form("form_paiement", clear_on_submit=True):
            st.subheader("Nouveau Règlement")
            nature = st.selectbox("Nature du paiement", 
                                ["Loyer Mensuel", "Frais de Scolarité", "Facture EDG/SEG", "Transport", "Autre"])
            montant = st.number_input("Montant (GNF)", min_value=0, step=5000)
            reference = st.text_input("Référence de la transaction (ex: N° Reçu)")
            commentaire = st.text_area("Notes additionnelles")
            
            submit = st.form_submit_button("Confirmer le paiement")
            
            if submit:
                if montant > 0 and reference:
                    # Enregistrement de la transaction
                    nouvelle_trans = {
                        "Date": datetime.now().strftime("%d/%m/%Y %H:%M"),
                        "Nature": nature,
                        "Montant": montant,
                        "Réf": reference,
                        "Statut": "Validé"
                    }
                    st.session_state['transactions'].append(nouvelle_trans)
                    st.success(f"✅ Paiement de {montant:,} GNF enregistré avec succès !")
                    st.balloons()
                else:
                    st.error("Veuillez remplir le montant et la référence.")

    with col2:
        st.subheader("Dernière activité")
        if st.session_state['transactions']:
            df = pd.DataFrame(st.session_state['transactions']).tail(3)
            st.table(df[['Date', 'Nature', 'Montant']])
        else:
            st.info("Aucune transaction récente.")

# PAGE 2 : ADMINISTRATION
elif page == "📊 Admin":
    st.title("Tableau de Bord Admin")
    
    if not st.session_state['transactions']:
        st.warning("Aucune donnée disponible pour le moment.")
    else:
        df_all = pd.DataFrame(st.session_state['transactions'])
        
        # Statistiques rapides
        total_gnf = df_all['Montant'].sum()
        st.metric("Total Collecté", f"{total_gnf:,} GNF")
        
        st.subheader("Historique Complet")
        st.dataframe(df_all, use_container_width=True)
        
        # Bouton export
        csv = df_all.to_csv(index=False).encode('utf-8')
        st.download_button("Télécharger l'historique (CSV)", csv, "export_kike_sare.csv", "text/csv")

# PAGE 3 : PARAMÈTRES
else:
    st.title("Paramètres du compte")
    st.write("Gérez vos notifications et vos préférences de sécurité.")
    st.checkbox("Recevoir un rappel par SMS avant l'échéance")
    st.checkbox("Générer automatiquement un reçu PDF")
