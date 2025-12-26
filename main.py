import streamlit as st

# 1. CONFIGURATION DE LA PAGE
st.set_page_config(
    page_title="Kiké Saré",
    page_icon="logo.png",
    layout="centered"
)

# 2. LIEN DIRECT VERS VOTRE LOGO (RAW)
direct_url = "https://raw.githubusercontent.com/AKBANGOURA/kike-sare/main/logo.png"

# 3. PERSONNALISATION DE L'INTERFACE (CSS/HTML)
st.markdown(
    f"""
    <head>
        <link rel="apple-touch-icon" href="{direct_url}">
        <link rel="icon" href="{direct_url}">
        <meta name="apple-mobile-web-app-title" content="Kiké Saré">
        <meta name="apple-mobile-web-app-capable" content="yes">
    </head>
    <style>
        /* Masquer les éléments Streamlit et GitHub */
        header {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        #MainMenu {{visibility: hidden;}}
        .stAppDeployButton {{display:none;}}
        
        /* Ajustement optionnel du haut de page */
        .block-container {{
            padding-top: 2rem;
        }}
    </style>
    """,
    unsafe_allow_html=True
)

# 4. LE CONTENU DE VOTRE APPLICATION
# (Remettez ici votre logique métier : formulaires, calculs, etc.)
st.image("logo.png", width=150)
st.title("KikéSaré")
st.subheader("Payez vos mensualités en toute sécurité !")

# Exemple de formulaire (à adapter avec votre ancien code)
col1, col2 = st.columns(2)
with col1:
    st.button("Connexion", use_container_width=True)
with col2:
    st.button("Inscription", use_container_width=True)

st.write("---")
st.write("Bienvenue dans la FinTech qui change votre monde.")
