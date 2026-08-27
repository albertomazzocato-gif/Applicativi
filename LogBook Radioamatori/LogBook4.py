import streamlit as st
import pandas as pd
import os
from datetime import datetime, timezone

# Configurazione della pagina
st.set_page_config(page_title="Logbook Radioamatori", page_icon="📻", layout="wide")

LOG_FILE = "radio_log.csv"

def salva_qso(station_call, nominativo, banda, modo, rst_in, rst_out, wwloc, note):
    data = {
        "Data/Ora (UTC)": [datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")],
        "La mia Stazione": [station_call.upper()],
        "Nominativo": [nominativo.upper()],
        "Banda": [banda],
        "Modo": [modo],
        "RST In": [rst_in],
        "RST Out": [rst_out],
        "WWLOC": [wwloc.upper()],
        "Note": [note]
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

# Creiamo due colonne: a sinistra il form di inserimento, a destra lo storico
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("➕ Nuovo QSO")
    
    # Form per l'inserimento dei dati
    with st.form("qso_form", clear_on_submit=True):
        station = st.text_input("Il mio Nominativo (Stazione)", value="IW3XXX").strip()
        nominativo = st.text_input("Nominativo Corrispondente", placeholder="es. IZ3XXX").strip()
        
        col_b, col_m = st.columns(2)
        with col_b:
            banda = st.selectbox("Banda", ["160m", "80m", "40m", "30m", "20m", "17m", "15m", "12m", "10m", "6m", "2m", "70cm"], index=2)
        with col_m:
            modo = st.selectbox("Modo", ["FT8", "CW", "SSB", "FT4", "FM", "AM", "RTTY"])

        # Logica RST intelligente in base al modo selezionato
        if modo == "CW":
            default_rst = "599"
        elif modo in ["FT8", "FT4"]:
            default_rst = "00"
        else:
            default_rst = "59"

        col_r1, col_r2 = st.columns(2)
        with col_r1:
            rst_in = st.text_input("RST In", value=default_rst)
        with col_r2:
            rst_out = st.text_input("RST Out", value=default_rst)

        wwloc = st.text_input("WWLOC (Locator)", placeholder="es. JN65").strip()
        note = st.text_input("Note (QTH / Nome)", placeholder="es. Roma / Mario").strip()

        submitted = st.form_submit_button("💾 Salva QSO", use_container_width=True)

        if submitted:
            if station and nominativo:
                salva_qso(station, nominativo, banda, modo, rst_in, rst_out, wwloc, note)
                st.success(f"QSO con {nominativo.upper()} salvato con successo!")
                st.rerun()
            else:
                st.error("Inserisci sia il tuo nominativo che quello del corrispondente!")

    # Sezione di manutenzione / pulizia log nella barra laterale
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
                st.warning("Spunta la casella 'Conferma eliminazione log' per procedere.")

with col2:
    st.subheader("📜 Storico Contatti")
    
    if os.path.exists(LOG_FILE):
        df = pd.read_csv(LOG_FILE)
        # Mostra i contatti più recenti in cima
        df_ordinato = df.iloc[::-1]
        st.dataframe(df_ordinato, use_container_width=True)
        
        # Pulsante per scaricare il log in CSV
        with open(LOG_FILE, "rb") as f:
            st.download_button(
                label="📥 Scarica Log (CSV)",
                data=f,
                file_name="radio_log.csv",
                mime="text/csv"
            )
    else:
        st.info("Nessun QSO registrato. Inserisci il primo contatto dal pannello a sinistra.")