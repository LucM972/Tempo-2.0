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
    .main {
        background-color: #1e1e2f;
        color: #ffffff;
    }
    .stButton>button, .stDownloadButton>button {
        background-color: #3366cc;
        color: white;
        border: None;
        border-radius: 8px;
        padding: 0.5em 1em;
    }
    .stButton>button:hover, .stDownloadButton>button:hover {
        background-color: #264d99;
        color: #ffffff;
    }
    .stNumberInput>div>div>input {
        background-color: #262639;
        color: #ffffff;
    }
    .stTextInput>div>div>input, .stDateInput>div>div>input {
        background-color: #262639;
        color: #ffffff;
    }
    </style>
""", unsafe_allow_html=True)

# Le reste du code reste inchangé

# === Fonctions ===
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

def generer_periodes(date_debut, nb_periodes):
    periodes = []
    courant = parse_date(date_debut)
    for i in range(nb_periodes):
        fin = courant + timedelta(days=182)
        periodes.append({
            "n°": i + 1,
            "debut": courant,
            "fin": fin,
            "taux": 0.0
        })
        courant = fin
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
            "Taux (%)": f"{taux:.3f}".replace(".", ","),
            "Intérêts": format_euro(interets)
        })

    return pd.DataFrame(resultats)

# === Interface ===
st.title("🧮 Simulateur de prêt de préfinancement de subvention")

st.sidebar.header("📌 Informations sur le prêt")
numero_pret = st.sidebar.text_input("Numéro du prêt")
nom_collectivite = st.sidebar.text_input("Nom de la collectivité")
new_date_signature = st.sidebar.date_input("Date de signature du prêt", datetime.today().date())
montant_initial = st.sidebar.number_input("Montant initial du prêt (€)", min_value=0.0, step=100.0)
duree = st.sidebar.number_input("Durée du prêt (en années)", value=5, step=1)

if 'date_signature' not in st.session_state or st.session_state.date_signature != new_date_signature:
    st.session_state.date_signature = new_date_signature
    st.session_state.periodes = generer_periodes(new_date_signature, len(st.session_state.periodes) if 'periodes' in st.session_state else 2)

st.header("📋 Taux par période")
if st.button("➕ Ajouter une période"):
    derniere_periode = st.session_state.periodes[-1]
    nouvelle_periode = generer_periodes(derniere_periode['fin'], 1)[0]
    nouvelle_periode['n°'] = len(st.session_state.periodes) + 1
    st.session_state.periodes.append(nouvelle_periode)

for periode in st.session_state.periodes:
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown(f"**Période {periode['n°']} : {format_date_fr(periode['debut'])} au {format_date_fr(periode['fin'])}**")
    with col2:
        periode['taux'] = st.number_input(f"Taux période {periode['n°']} (%)", value=periode['taux'], format="%.3f", key=f"taux_{periode['n°']}")

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

    if st.button("🗑 Supprimer le dernier flux") and st.session_state.flux_data:
        st.session_state.flux_data.pop()

    total_verse = sum(f['montant'] for f in st.session_state.flux_data if f['type'] == 'Versement')
    total_rembourse = sum(f['montant'] for f in st.session_state.flux_data if f['type'] == 'Remboursement')
    reste_a_verser = montant_initial - total_verse
    capital_restant_du = total_verse - total_rembourse

    st.subheader("📊 Informations générales")
    st.markdown(f"**Nom de la collectivité :** {nom_collectivite if nom_collectivite else 'Non renseigné'}")
    st.markdown(f"**Montant initial du prêt :** {format_euro(montant_initial)}")
    st.markdown(f"**Montant total versé :** {format_euro(total_verse)}")
    st.markdown(f"**Remboursement réalisé :** {format_euro(total_rembourse)}")
    st.markdown(f"**Reste à verser :** {format_euro(reste_a_verser)}")
    st.markdown(f"**Capital restandu à date :** {format_euro(capital_restant_du)}")

    st.header("📈 Échéancier détaillé")
    df_resultats = calcul_echeancier(st.session_state.flux_data, st.session_state.periodes)
    st.dataframe(df_resultats, use_container_width=True, hide_index=True)

    st.download_button(
        label="📥 Télécharger l'échéancier (Excel)",
        data=df_resultats.to_csv(index=False).encode('utf-8'),
        file_name="echeancier.csv",
        mime="text/csv"
    )
