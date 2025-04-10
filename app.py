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

def generer_periodes(date_debut, nb_periodes):
    periodes = []
    courant = date_debut
    for i in range(nb_periodes):
        fin = courant + timedelta(days=182)
        periodes.append({
            "n°": i + 1,
            "debut": courant,
            "fin": fin,
            "taux": 0.0  # Valeur initiale, à saisir manuellement
        })
        courant = fin
    return periodes

def calcul_echeancier(flux, periodes):
    solde = 0.0
    resultats = []

    for periode in periodes:
        debut, fin = periode['debut'], periode['fin']
        taux = periode['taux']
        courant = debut
        interets = 0.0
        montant_prete = 0.0
        montant_rembourse = 0.0

        flux_periode = [f for f in flux if debut <= parse_date(f['date']) < fin]
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
            "Taux (%)": f"{taux:.2f}".replace(".", ","),
            "Intérêts": format_euro(interets)
        })

    return pd.DataFrame(resultats)

st.title("🧮 Simulateur de prêt de préfinancement de subvention")

st.sidebar.header("Informations sur le prêt")
numero_pret = st.sidebar.text_input("Numéro du prêt")
nom_collectivite = st.sidebar.text_input("Nom de la collectivité")
date_signature = st.sidebar.date_input("Date de signature du prêt", datetime.today().date())
montant_initial = st.sidebar.number_input("Montant initial du prêt (€)", min_value=0.0, step=100.0)
duree = st.sidebar.number_input("Durée du prêt (en années)", value=5, step=1)

st.header("📋 Taux par période (manuels)")
nb_periodes = int(duree * 2)
if "periodes" not in st.session_state:
    st.session_state.periodes = generer_periodes(date_signature, nb_periodes)

for periode in st.session_state.periodes:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**Période {periode['n°']} : {format_date_fr(periode['debut'])} au {format_date_fr(periode['fin'])}**")
    with col2:
        periode['taux'] = st.number_input(f"Taux période {periode['n°']} (%)", value=0.0, key=f"taux_{periode['n°']}")

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
    df_flux['montant'] = df_flux['montant'].apply(format_euro)
    st.subheader("📑 Historique des flux")
    st.table(df_flux)

    st.header("📊 Échéancier détaillé")
    df_resultats = calcul_echeancier(st.session_state.flux_data, st.session_state.periodes)
    st.dataframe(df_resultats)

    st.download_button(
        label="📥 Télécharger l'échéancier (Excel)",
        data=df_resultats.to_csv(index=False).encode('utf-8'),
        file_name="echeancier.csv",
        mime="text/csv"
    )
