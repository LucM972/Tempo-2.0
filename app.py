import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import calendar

st.set_page_config(
    page_title="Simulateur AFD",
    page_icon="🧬",
    layout="wide"
)

st.markdown("""
    <style>
    body {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .main {
        background-color: #0d1117;
        color: #c9d1d9;
        font-family: 'Segoe UI', sans-serif;
    }
    .stButton>button, .stDownloadButton>button {
        background-color: #238636;
        color: white;
        border: none;
        border-radius: 6px;
        padding: 0.5em 1em;
        font-weight: bold;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: #2ea043;
    }
    .stNumberInput>div>div>input, .stTextInput>div>div>input, .stDateInput>div>div>input {
        background-color: #161b22;
        color: #ffffff;
        border: 1px solid #30363d;
    }
    .stDataFrame, .stDataTable {
        background-color: #0d1117;
        color: #c9d1d9;
    }
    .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #58a6ff;
    }
    </style>
""", unsafe_allow_html=True)


def parse_date(date_str):
    if isinstance(date_str, datetime):
        return date_str
    elif isinstance(date_str, date):
        return datetime.combine(date_str, datetime.min.time())
    try:
        return datetime.strptime(date_str, "%d/%m/%Y")
    except ValueError:
        return datetime.strptime(date_str, "%Y-%m-%d")

def days_between(d1, d2):
    return (d2 - d1).days

def format_euro(val):
    return f"{val:,.2f} €".replace(",", "X").replace(".", ",").replace("X", " ")

def format_date_fr(dt):
    return dt.strftime("%d/%m/%Y")

def dernier_jour_mois_6_mois_apres(date_depart):
    mois = date_depart.month + 6
    annee = date_depart.year + (mois - 1) // 12
    mois = (mois - 1) % 12 + 1
    dernier_jour = calendar.monthrange(annee, mois)[1]
    return datetime(annee, mois, dernier_jour)

def generer_periodes_afd(date_debut_periode1, date_fin_periode1, nb_periodes):
    periodes = []
    debut = date_debut_periode1
    fin = date_fin_periode1

    for i in range(nb_periodes):
        periodes.append({
            "n°": i + 1,
            "debut": debut,
            "fin": fin,
            "taux": 0.0
        })
        debut = fin + timedelta(days=1)
        fin = dernier_jour_mois_6_mois_apres(debut)

    return periodes

st.sidebar.header("📌 Informations sur le prêt")
nom_collectivite = st.sidebar.text_input("Nom de la collectivité")
montant_initial = st.sidebar.number_input("Montant initial du prêt (€)", min_value=0.0, step=1000.0, format="%.2f")

col1, col2 = st.sidebar.columns(2)
with col1:
    date_debut_str = st.text_input("Début de la 1ère période (jj/mm/aaaa)", "29/02/2024")
with col2:
    date_fin_str = st.text_input("Fin de la 1ère période (jj/mm/aaaa)", "31/08/2024")

try:
    date_debut_periode = parse_date(date_debut_str)
    date_fin_periode = parse_date(date_fin_str)
except ValueError:
    st.sidebar.error("❌ Format invalide. Utilisez jj/mm/aaaa")
    st.stop()

if 'periodes' not in st.session_state:
    st.session_state.periodes = generer_periodes_afd(date_debut_periode, date_fin_periode, 10)

st.title("🧮 Simulateur de prêt de préfinancement de subvention")
st.header("📋 Taux par période (manuels)")

for i, periode in enumerate(st.session_state.periodes):
    col_g, col_d = st.columns([3, 1])
    with col_g:
        st.markdown(f"**Période {periode['n°']} : {format_date_fr(periode['debut'])} au {format_date_fr(periode['fin'])}**")
    with col_d:
        taux = st.number_input(f"Taux période {periode['n°']} (%)", min_value=0.000, max_value=10.000, value=periode['taux'], step=0.001, format="%.3f")
        st.session_state.periodes[i]['taux'] = taux

if st.button("🔄 Recalculer les périodes"):
    st.session_state.periodes = generer_periodes_afd(date_debut_periode, date_fin_periode, 10)
    st.experimental_rerun()

st.success("✅ Périodes générées et taux saisis !")
