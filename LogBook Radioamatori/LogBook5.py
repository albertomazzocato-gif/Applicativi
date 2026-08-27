import math
import streamlit as st

st.set_page_config(
    page_title="Logbook ARI Montebelluna", page_icon="📻", layout="centered"
)


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


# Inizializzazione della memoria dei QSO nella sessione
if "log_entries" not in st.session_state:
    st.session_state.log_entries = []

st.title("📻 Logbook di Stazione - ARI Montebelluna")

with st.form("qso_form", clear_on_submit=False):
    st.subheader("Inseriscici i Dati del QSO")

    col1, col2 = st.columns(2)

    with col1:
        my_callsign = st.text_input(
            "Tuo Nominativo", value="", placeholder="es. IZ3XXX"
        )
        my_locator = st.text_input(
            "Tuo Locatore", value="", placeholder="es. JN65rt"
        )
        callsign = st.text_input(
            "Nominativo Corrispondente", value="", placeholder="es. IK2YYY"
        ).upper()

    with col2:
        band = st.selectbox(
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
        )
        mode = st.selectbox("Modo", ["SSB", "CW", "FT8", "FT4", "AM", "FM", "RTTY"])

    # Gestione automatica dell'RST in base al modo scelto
    default_rst = "59"
    if mode == "CW":
        default_rst = "599"
    elif mode in ["FT8", "FT4"]:
        default_rst = "-10"
    elif mode in ["SSB", "AM", "FM"]:
        default_rst = "59"

    col3, col4 = st.columns(2)
    with col3:
        rst_sent = st.text_input("RST Inviato", value=default_rst)
    with col4:
        rst_rcvd = st.text_input("RST Ricevuto", value=default_rst)

    dx_locator = st.text_input(
        "Locatore Corrispondente", value="", placeholder="es. JN55"
    ).upper()

    submitted = st.form_submit_button("Registra QSO")

    if submitted:
        if not callsign:
            st.error("Inserisci il nominativo del corrispondente!")
        else:
            # Calcolo distanza e azimut se entrambi i locatori sono valorizzati
            dist, az = None, None
            if my_locator and dx_locator:
                dist, az = calculate_distance_and_azimuth(my_locator, dx_locator)

            qso_data = {
                "Operatore": my_callsign if my_callsign else "N/D",
                "Callsign": callsign,
                "Banda": band,
                "Modo": mode,
                "RST Inv": rst_sent,
                "RST Rcv": rst_rcvd,
                "Locatore DX": dx_locator if dx_locator else "-",
                "Distanza": f"{dist} km" if dist is not None else "-",
                "Azimut": f"{az}°" if az is not None else "-",
            }

            st.session_state.log_entries.insert(0, qso_data)
            st.success(f"QSO con {callsign} registrato correttamente!")

# Tabella riepilogativa dei QSO inseriti
if st.session_state.log_entries:
    st.divider()
    st.subheader(f"📋 Lista QSO Registrati ({len(st.session_state.log_entries)})")
    st.dataframe(st.session_state.log_entries, use_container_width=True)