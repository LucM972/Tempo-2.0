import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

st.set_page_config(
    page_title="Simulateur AFD",
    page_icon="🧮",
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
    return datetime.strptime(date_str, "%Y-%m-%d")

def days_between(d1, d2):
    return (d2 - d1).days

def format_euro(val):
    return f"{val:,.2f} €".replace(",", "X").replace(".", ",").replace("X", " ")

def format_date_fr(dt):
    return dt.strftime("%d/%m/%Y")

def generer_periodes_afd(date_signature, nb_periodes):
    from dateutil.relativedelta import relativedelta

    periodes = []
    annee = date_signature.year

    if date_signature <= datetime(annee, 7, 31).date():
        debut = datetime(annee, 1, 15)
    else:
        debut = datetime(annee, 8, 1)

    for i in range(nb_periodes):
        if debut.month == 1:
            fin = datetime(debut.year, 7, 31)
        elif debut.month == 8:
            fin = datetime(debut.year + 1, 1, 31)
        else:
            raise ValueError("Mois de début invalide")

        periodes.append({
            "n°": i + 1,
            "debut": debut,
            "fin": fin,
            "taux": 0.0
        })

        debut = fin + timedelta(days=1)

    return periodes

def calcul_echeancier(flux, periodes):
    solde = 0.0
    resultats = []

    for periode in periodes:
        debut, fin = parse_date(periode['debut']), parse_date(periode['fin'])
        taux = periode['taux']
        courant = debut
        interets = 0.0
        montant_prete = 0.0
        montant_rembourse = 0.0

        flux_periode = [f for f in flux if debut <= parse_date(f['date']) <= fin]
        flux_periode.sort(key=lambda x: parse_date(x['date']))

        for f in flux_periode:
            date_flux = parse_date(f['date'])
            jours = days_between(courant, date_flux)
            interets += solde * (jours / 365) * (taux / 100)
            courant = date_flux

            if f['type'] == 'Versement':
                solde += f['montant']
                montant_prete += f['montant']
            elif f['type'] == 'Remboursement':
                solde -= f['montant']
                montant_rembourse += f['montant']

        jours = days_between(courant, fin)
        interets += solde * (jours / 365) * (taux / 100)

        resultats.append({
            "N°": periode['n°'],
            "Période": f"{format_date_fr(debut)} au {format_date_fr(fin)}",
            "Montant prêté": format_euro(montant_prete),
            "Montant remboursé": format_euro(montant_rembourse),
            "Solde": format_euro(solde),
            "Durée (j)": days_between(debut, fin),
            "Taux (%)": f"{taux:.3f}".replace(".", ","),
            "Intérêts": format_euro(interets)
        })

    return pd.DataFrame(resultats)

# Le reste du code reste inchangé ici, car l'amélioration demandée était visuelle et de mise en forme des nombres
# Cette partie inclut les st.sidebar, les formulaires et l'affichage du tableau
# Elle reste identique sauf si tu veux aussi un refactoring fonctionnel ou des améliorations UX supplémentaires
