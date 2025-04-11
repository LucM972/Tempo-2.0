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
# Gestion des flux
st.header("📥 Saisie des flux")
if "flux_data" not in st.session_state:
    st.session_state.flux_data = []

with st.form("form_flux"):
    date_flux_str = st.text_input("Date du flux (jj/mm/aaaa)", value="01/01/2025")
    try:
        date_flux = datetime.strptime(date_flux_str, "%d/%m/%Y").date()
    except ValueError:
        st.error("❌ Format invalide. Utilisez jj/mm/aaaa")
        date_flux = None

    type_flux = st.selectbox("Type de flux", ["Versement", "Remboursement"])
    montant = st.number_input("Montant (€)", min_value=0.0, step=100.0)
    ajouter = st.form_submit_button("Ajouter le flux")

    if ajouter and date_flux:
        flux_date = parse_date(date_flux)
        while flux_date > parse_date(st.session_state.periodes[-1]['fin']):
            st.session_state.periodes += generer_periodes_afd(
                parse_date(st.session_state.periodes[-1]['fin']) + timedelta(days=1),
                dernier_jour_mois_6_mois_apres(parse_date(st.session_state.periodes[-1]['fin']) + timedelta(days=1)),
                1
            )
        st.session_state.flux_data.append({"date": str(date_flux), "type": type_flux, "montant": montant})

# Affichage et suppression des flux
if st.session_state.flux_data:
    st.subheader("📑 Historique des flux")
    index_to_delete = None
    for i, f in enumerate(st.session_state.flux_data):
        col1, col2, col3, col4 = st.columns([2, 2, 2, 1])
        with col1:
            st.write(f"{format_date_fr(parse_date(f['date']))}")
        with col2:
            st.write(f["type"])
        with col3:
            st.write(format_euro(f["montant"]))
        with col4:
            if st.button("❌", key=f"delete_{i}"):
                index_to_delete = i

    if index_to_delete is not None:
        st.session_state.flux_data.pop(index_to_delete)
        st.experimental_rerun()

    # Calcul des intérêts
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

    # Récapitulatif
    st.subheader("📊 Informations générales")
    total_verse = sum(f['montant'] for f in st.session_state.flux_data if f['type'] == 'Versement')
    total_rembourse = sum(f['montant'] for f in st.session_state.flux_data if f['type'] == 'Remboursement')
    reste_a_verser = montant_initial - total_verse
    capital_restant_du = total_verse - total_rembourse

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
