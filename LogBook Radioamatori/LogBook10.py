from datetime import datetime, timezone
import math
import os
import pandas as pd
import streamlit as st

# Import per la generazione del PDF con ReportLab
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors

# Configurazione della pagina Streamlit
st.set_page_config(page_title="Logbook Radioamatori", page_icon="📻", layout="wide")

PDF_FILE = "radio_log.pdf"


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


# Funzione per generare il PDF formattato
def genera_pdf(df, filename):
    doc = SimpleDocTemplate(
        filename,
        pagesize=landscape(A4),
        rightMargin=30,
        leftMargin=30,
        topMargin=30,
        bottomMargin=30,
    )
    elements = []
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        'TitleStyle',
        parent=styles['Heading1'],
        fontSize=18,
        textColor=colors.HexColor("#1f4e79"),
        spaceAfter=15,
        alignment=1
    )
    elements.append(Paragraph("<b>Logbook Radioamatori - ARI Montebelluna</b>", title_style))
    elements.append(Spacer(1, 10))

    table_data = [list(df.columns)]
    for _, row in df.iterrows():
        table_data.append([str(val) for val in row.values])

    t = Table(table_data, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#1f4e79")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor("#f9f9f9")),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#d3d3d3")),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 9),
        ('TOPPADDING', (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
    ]))

    elements.append(t)
    doc.build(elements)


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
    note_pulite = note.strip() if note and str(note).strip() != "" else "-"

    data = {
        "Data/Ora (UTC)": datetime.now(timezone.utc).strftime("%d-%m-%Y %H:%M"),  # Formato Giorno-Mese-Anno
        "Stazione": station_call.upper(),
        "DX": nominativo.upper(),
        "Banda": banda,
        "Modo": modo,
        "RST In": rst_in,
        "RST Out": rst_out,
        "Mio Loc": wwloc_miei.upper() if wwloc_miei else "-",
        "DX Loc": wwloc_dx.upper() if wwloc_dx else "-",
        "Distanza": f"{distanza} km" if distanza is not None else "-",
        "Azimut": f"{azimuth}°" if azimuth is not None else "-",
        "Note": note_pulite,
    }
    
    csv_temp = "temp_log.csv"
    nuovo_qso = pd.DataFrame([data])
    
    if os.path.exists(csv_temp):
        log = pd.read_csv(csv_temp)
        log["Note"] = log["Note"].fillna("-")
        log = pd.concat([log, nuovo_qso], ignore_index=True)
    else:
        log = nuovo_qso
        
    log.to_csv(csv_temp, index=False)
    genera_pdf(log, PDF_FILE)


st.title("📻 Logbook Radioamatori")
st.write("Registra i tuoi QSO e genera il report PDF ufficiale in tempo reale.")

col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("➕ Nuovo QSO")

    banda = st.selectbox(
        "Banda",
        [
            "160m", "80m", "40m", "30m", "20m", "17m", "15m", "12m", "10m",
            "6m", "4m", "2m", "70cm", "23cm", "13cm", "9cm", "6cm", "3cm",
            "1.25cm", "6mm", "4mm", "2.5mm", "2mm", "1mm", "47 GHz"
        ],
        index=4,
    )
    modo = st.selectbox(
        "Modo",
        ["SSB", "CW", "FT8", "FT4", "AM", "FM", "RTTY", "RS"],
        key="modo_selezionato",
    )

    if modo == "CW":
        default_rst = "599"
    elif modo in ["FT8", "FT4"]:
        default_rst = "00"
    elif modo == "RS":
        default_rst = "59S"
    else:
        default_rst = "59"

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

    submitted = st.button("💾 Salva QSO & Aggiorna PDF", use_container_width=True)

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
            st.success(f"QSO con {nominativo.upper()} salvato e PDF aggiornato!")
            st.rerun()
        else:
            st.error(
                "Inserisci sia il tuo nominativo che quello del corrispondente!"
            )

    st.markdown("---")
    st.subheader("⚙️ Gestione Log")
    with st.expander("Opzioni avanzate / Pulizia"):
        conferma_canc = st.checkbox("Conferma eliminazione log")
        if st.button("🗑️ Svuota Storico", use_container_width=True):
            if conferma_canc:
                if os.path.exists("temp_log.csv"):
                    os.remove("temp_log.csv")
                if os.path.exists(PDF_FILE):
                    os.remove(PDF_FILE)
                st.success("Storico e PDF azzerati con successo!")
                st.rerun()
            else:
                st.warning(
                    "Spunta la casella 'Conferma eliminazione log' per procedere."
                )

with col2:
    st.subheader("📜 Storico Contatti & Export PDF")

    if os.path.exists("temp_log.csv"):
        df = pd.read_csv("temp_log.csv")
        df["Note"] = df["Note"].fillna("-")
        df_ordinato = df.iloc[::-1]
        st.dataframe(df_ordinato, use_container_width=True)

        if os.path.exists(PDF_FILE):
            with open(PDF_FILE, "rb") as f:
                st.download_button(
                    label="📥 Scarica Storico in formato PDF",
                    data=f,
                    file_name="radio_log.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
    else:
        st.info(
            "Nessun QSO registrato. Inserisci il primo contatto per generare il PDF."
        )