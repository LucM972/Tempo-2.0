import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def parse_date(date_str):
    if isinstance(date_str, datetime):
        return date_str
    return datetime.strptime(date_str, "%Y-%m-%d")

def days_between(d1, d2):
    return (d2 - d1).days

def calcul_interets(flux, date_signature, taux, duree_annees=5):
    date_debut = parse_date(date_signature)
    resultats = []

    periodes = []
    courant = date_debut
    for _ in range(duree_annees * 2):
        fin = courant + timedelta(days=182)
        periodes.append((courant, fin))
        courant = fin

    solde = 0.0
    for debut, fin in periodes:
        interets = 0.0
        courant = debut
        flux_periode = [f for f in flux if debut <= parse_date(f['date']) < fin]
        flux_periode.sort(key=lambda x: parse_date(x['date']))

        for f in flux_periode:
            date_flux = parse_date(f['date'])
            jours = days_between(courant, date_flux)
            interets += solde * (jours / 365) * (taux / 100)
            courant = date_flux

            if f['type'] == 'Versement':
                solde += f['montant']
            elif f['type'] == 'Remboursement':
                solde -= f['montant']

        jours = days_between(courant, fin)
        interets += solde * (jours / 365) * (taux / 100)

        resultats.append({
            "Période": f"{debut.date()} au {fin.date()}",
            "Intérêts dus": round(interets, 2),
            "Solde final": round(solde, 2)
        })

    return pd.DataFrame(resultats)

st.title("🧮 Simulateur de prêt de préfinancement de subvention")

st.sidebar.header("Paramètres du prêt")
date_signature = st.sidebar.date_input("Date de signature du prêt", datetime.today())
taux = st.sidebar.number_input("Taux d'intérêt (%)", value=2.0)
duree = st.sidebar.number_input("Durée du prêt (en années)", value=5, step=1)

st.header("📥 Saisie des flux")
if "flux_data" not in st.session_state:
    st.session_state.flux_data = []

with st.form("form_flux"):
    date_flux = st.date_input("Date du flux")
    type_flux = st.selectbox("Type de flux", ["Versement", "Remboursement"])
    montant = st.number_input("Montant (€)", min_value=0.0, step=100.0)
    ajouter = st.form_submit_button("Ajouter le flux")

    if ajouter:
        st.session_state.flux_data.append({"date": str(date_flux), "type": type_flux, "montant": montant})

if st.session_state.flux_data:
    df_flux = pd.DataFrame(st.session_state.flux_data)
    st.table(df_flux)

    st.header("📊 Calcul des intérêts")
    df_resultats = calcul_interets(st.session_state.flux_data, date_signature, taux, int(duree))
    st.dataframe(df_resultats)

    st.download_button(
        label="📥 Télécharger les résultats (Excel)",
        data=df_resultats.to_csv(index=False).encode('utf-8'),
        file_name="interets.csv",
        mime="text/csv"
    )
