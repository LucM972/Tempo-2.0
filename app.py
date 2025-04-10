import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta

def parse_date(date_str):
    if isinstance(date_str, (datetime, date)):
        return datetime.combine(date_str, datetime.min.time())
    return datetime.strptime(date_str, "%Y-%m-%d")

def days_between(d1, d2):
    return (d2 - d1).days

def format_euro(val):
    return f"{val:,.2f} €".replace(",", "X").replace(".", ",").replace("X", " ")

def format_date_fr(dt):
    return dt.strftime("%d/%m/%Y")

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
            "Période": f"{format_date_fr(debut)} au {format_date_fr(fin)}",
            "Intérêts dus": format_euro(interets),
            "Solde final": format_euro(solde)
        })

    return pd.DataFrame(resultats)

st.title("🧮 Simulateur de prêt de préfinancement de subvention")

st.sidebar.header("Paramètres du prêt")
nom_partenaire = st.sidebar.text_input("Nom du partenaire")
date_signature = st.sidebar.date_input("Date de signature du prêt", datetime.today().date())
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
    df_flux['date'] = pd.to_datetime(df_flux['date']).dt.strftime('%d/%m/%Y')
    st.table(df_flux)

    st.header("📊 Informations générales")
    montant_initial = sum(f['montant'] for f in st.session_state.flux_data if f['type'] == 'Versement')
    remboursements = sum(f['montant'] for f in st.session_state.flux_data if f['type'] == 'Remboursement')
    reste_a_verser = montant_initial - remboursements

    st.markdown(f"**Nom du partenaire :** {nom_partenaire if nom_partenaire else 'Non renseigné'}")
    st.markdown(f"**Montant total versé :** {format_euro(montant_initial)}")
    st.markdown(f"**Remboursé par le subventionneur :** {format_euro(remboursements)}")
    st.markdown(f"**Reste à rembourser :** {format_euro(reste_a_verser)}")

    st.header("📊 Calcul des intérêts")
    df_resultats = calcul_interets(st.session_state.flux_data, date_signature, taux, int(duree))
    st.dataframe(df_resultats)

    st.download_button(
        label="📥 Télécharger les résultats (Excel)",
        data=df_resultats.to_csv(index=False).encode('utf-8'),
        file_name="interets.csv",
        mime="text/csv"
    )
