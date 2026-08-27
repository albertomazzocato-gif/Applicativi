from datetime import datetime, timezone
import math
import os
import pandas as pd
import streamlit as st

# Configurazione della pagina
st.set_page_config(page_title="Logbook Radioamatori", page_icon="📻", layout="wide")

LOG_FILE = "radio_log.csv"


# Funzioni per il calcolo Maidenhead Locator (Distanza e Azimut)
def locator_to_latlon(locator):
    locator = locator.strip().upper()
    if not (4 <= len(locator) <= 6):
        return None, None
    try:
        lon = (ord(locator[0]) - ord("A")) * 20 - 180
        lat = (ord(locator[1]) - ord("A")) * 10 - 90
        lon += int(locator[2]) * 2
        lat += int(locator[3]) * 1

        if len(locator) == 6:
            lon += (ord(locator[4]) - ord("A") + 0.5) / 12
            lat += (ord(locator[5]) - ord("A") + 0.5) / 24
        else:
            lon += 1.0
            lat += 0.5
        return lat, lon
    except Exception:
        return None, None


def calculate_distance_and_azimuth(loc1, loc2):
    lat1, lon1 = locator_to_latlon(loc1)
    lat2, lon2 = locator_to_latlon(loc2)

    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return None, None

    phi1, lambda1 = math.radians(lat1), math.radians(lon1)
    phi2, lambda2 = math.radians(lat2), math.radians(lon2)

    dlambda = lambda2 - lambda1
    dphi = phi2 - phi1
    a = (
        math.sin(dphi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    distance = 6371.0 * c

    y = math.sin(dlambda) * math.cos(phi2)
    x = math.cos(phi1) * math.sin(phi2) - math.sin(phi1) * math.cos(
        phi2
    ) * math.cos(dlambda)
    azimuth = (math.degrees(math.atan2(y, x)) + 360) % 360

    return round(distance, 1), round(azimuth, 1)


def salva_qso(
    station_call,
    nominativo,
    banda,
    modo,
    rst_in,
    rst_out,
    wwloc_miei,
    wwloc_dx,
    distanza,
    azimuth,
    note,
):
    data = {
        "Data/Ora (UTC)": [datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")],
        "La mia Stazione": [station_call.upper()],
        "Nominativo": [nominativo.upper()],
        "Banda": [banda],
        "Modo": [modo],
        "RST In": [rst_in],
        "RST Out": [rst_out],
        "Mio WWLOC": [wwloc_miei.upper() if wwloc_miei else "-"],
        "WWLOC DX": [wwloc_dx.upper() if wwloc_dx else "-"],
        "Distanza": [f"{distanza} km" if distanza is not None else "-"],
        "Azimuth": [f"{azimuth}°" if azimuth is not None else "-"],
        "Note": [note],
    }
    nuovo_qso = pd.DataFrame(data)
    if os.path.exists(LOG_FILE):
        log = pd.read_csv(LOG_FILE)
        log = pd.concat([log, nuovo_qso], ignore_index=True)
    else:
        log = nuovo_qso
    log.to_csv(LOG_FILE, index=False)


st.title("📻 Logbook Radioamatori - Stazione")
st.write("Registra i tuoi QSO e consulta lo storico in tempo reale.")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("➕ Nuovo QSO")

    # Selezione banda e modo fuori dal form per la reattività dell'RST
    banda = st.selectbox(
        "Banda",
        [
            "160m",
            "80m",
            "40m",
            "30m",
            "20m",
            "17m",
            "15m",
            "12m",
            "10m",
            "6m",
            "4m",
            "2m",
            "70cm",
            "23cm",
            "13cm",
            "9cm",
            "6cm",
            "3cm",
            "1.25cm",
            "6mm",
            "4mm",
            "2.5mm",
            "2mm",
            "1mm",
            "47 GHz",
        ],
        index=4,
    )
    modo = st.selectbox(
        "Modo",
        ["SSB", "CW", "FT8", "FT4", "AM", "FM", "RTTY"],
        key="modo_selezionato",
    )

    # RST dinamico richiesto dal presidente
    if modo == "CW":
        default_rst = "599"
    elif modo in ["FT8", "FT4"]:
        default_rst = "00"
    else:
        default_rst = "59"

    # Campi dei locatori posizionati FUORI dal form per calcolare la distanza in tempo reale
    st.markdown("---")
    st.write("📍 **Rilevamento Posizione & Orientamento**")
    col_l1, col_l2 = st.columns(2)
    with col_l1:
        wwloc_miei = st.text_input(
            "Mio WWLOC", value="JN65rt", placeholder="es. JN65rt"
        ).strip()
    with col_l2:
        wwloc_dx = st.text_input(
            "WWLOC Corrispondente", placeholder="es. JN55"
        ).strip()

    # Calcolo in tempo reale della distanza e dell'azimut
    live_dist, live_az = None, None
    if wwloc_miei and wwloc_dx:
        live_dist, live_az = calculate_distance_and_azimuth(wwloc_miei, wwloc_dx)
        if live_dist is not None:
            st.info(
                f"🎯 **Distanza:** {live_dist} km  |  🧭 **Direzione (Azimut):** {live_az}°"
            )
        else:
            st.warning("⚠️ Formato locatori non valido (usa es. JN65rt o JN55)")

    st.markdown("---")

    # Form per il salvataggio dei dati del QSO
    with st.form("qso_form", clear_on_submit=True):
        station = st.text_input(
            "Il mio Nominativo (Stazione)", value="IW3XXX"
        ).strip()
        nominativo = st.text_input(
            "Nominativo Corrispondente", placeholder="es. IZ3XXX"
        ).strip()

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            rst_in = st.text_input("RST In", value=default_rst)
        with col_r2:
            rst_out = st.text_input("RST Out", value=default_rst)

        note = st.text_input(
            "Note (QTH / Nome)", placeholder="es. Roma / Mario"
        ).strip()

        submitted = st.form_submit_button("💾 Salva QSO", use_container_width=True)

        if submitted:
            if station and nominativo:
                salva_qso(
                    station,
                    nominativo,
                    banda,
                    modo,
                    rst_in,
                    rst_out,
                    wwloc_miei,
                    wwloc_dx,
                    live_dist,
                    live_az,
                    note,
                )
                st.success(f"QSO con {nominativo.upper()} salvato con successo!")
                st.rerun()
            else:
                st.error(
                    "Inserisci sia il tuo nominativo che quello del corrispondente!"
                )

    # Gestione log / pulizia
    st.markdown("---")
    st.subheader("⚙️ Gestione Log")
    with st.expander("Opzioni avanzate / Pulizia"):
        conferma_canc = st.checkbox("Conferma eliminazione log")
        if st.button("🗑️ Svuota Storico", use_container_width=True):
            if conferma_canc:
                if os.path.exists(LOG_FILE):
                    os.remove(LOG_FILE)
                st.success("Storico azzerato con successo!")
                st.rerun()
            else:
                st.warning(
                    "Spunta la casella 'Conferma eliminazione log' per procedere."
                )

with col2:
    st.subheader("📜 Storico Contatti")

    if os.path.exists(LOG_FILE):
        df = pd.read_csv(LOG_FILE)
        df_ordinato = df.iloc[::-1]
        st.dataframe(df_ordinato, use_container_width=True)

        with open(LOG_FILE, "rb") as f:
            st.download_button(
                label="📥 Scarica Log (CSV)",
                data=f,
                file_name="radio_log.csv",
                mime="text/csv",
            )
    else:
        st.info(
            "Nessun QSO registrato. Inserisci il primo contatto dal pannello a sinistra."
        )