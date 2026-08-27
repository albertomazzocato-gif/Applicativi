import customtkinter as ctk
import pandas as pd
import os
from datetime import datetime, timezone

# Configurazione grafica generale
ctk.set_appearance_mode("System")
ctk.set_default_color_theme("blue")

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

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Logbook Radioamatori - Stazione")
        self.geometry("1050x600")

        # Layout principale a due colonne
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # --- PANNELLO SINISTRO (INSERIMENTO DATI) ---
        self.sidebar = ctk.CTkFrame(self, width=300, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        
        ctk.CTkLabel(self.sidebar, text="➕ Nuovo QSO", font=ctk.CTkFont(size=16, weight="bold")).pack(pady=(15, 10))

        # Il mio Nominativo (Stazione)
        ctk.CTkLabel(self.sidebar, text="Il mio Nominativo (Stazione)").pack(anchor="w", padx=20)
        self.ent_station = ctk.CTkEntry(self.sidebar, placeholder_text="es. IW3XXX")
        self.ent_station.pack(fill="x", padx=20, pady=(0, 10))

        # Nominativo Corrispondente
        ctk.CTkLabel(self.sidebar, text="Nominativo Corrispondente").pack(anchor="w", padx=20)
        self.ent_call = ctk.CTkEntry(self.sidebar, placeholder_text="es. IZ3XXX")
        self.ent_call.pack(fill="x", padx=20, pady=(0, 10))

        # Banda e Modo
        row_bm = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        row_bm.pack(fill="x", padx=20, pady=(0, 10))
        row_bm.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(row_bm, text="Banda").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(row_bm, text="Modo").grid(row=0, column=1, sticky="w", padx=(5, 0))

        self.cmb_band = ctk.CTkComboBox(row_bm, values=["160m", "80m", "40m", "30m", "20m", "17m", "15m", "12m", "10m", "6m", "2m", "70cm"])
        self.cmb_band.grid(row=1, column=0, sticky="ew", pady=(2, 0))
        self.cmb_band.set("40m")

        self.cmb_mode = ctk.CTkComboBox(row_bm, values=["SSB", "CW", "FT8", "FT4", "FM", "AM", "RTTY"], command=self.aggiorna_rst_default)
        self.cmb_mode.grid(row=1, column=1, sticky="ew", pady=(2, 0), padx=(5, 0))
        self.cmb_mode.set("FT8")

        # RST In / Out
        row_rst = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        row_rst.pack(fill="x", padx=20, pady=(0, 10))
        row_rst.grid_columnconfigure((0, 1), weight=1)

        ctk.CTkLabel(row_rst, text="RST In").grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(row_rst, text="RST Out").grid(row=0, column=1, sticky="w", padx=(5, 0))

        self.ent_rst_in = ctk.CTkEntry(row_rst)
        self.ent_rst_in.insert(0, "00")
        self.ent_rst_in.grid(row=1, column=0, sticky="ew", pady=(2, 0))

        self.ent_rst_out = ctk.CTkEntry(row_rst)
        self.ent_rst_out.insert(0, "00")
        self.ent_rst_out.grid(row=1, column=1, sticky="ew", pady=(2, 0), padx=(5, 0))

        # WWLOC Corrispondente
        ctk.CTkLabel(self.sidebar, text="WWLOC (Locator)").pack(anchor="w", padx=20)
        self.ent_wwloc = ctk.CTkEntry(self.sidebar, placeholder_text="es. JN65")
        self.ent_wwloc.pack(fill="x", padx=20, pady=(0, 10))

        # Note
        ctk.CTkLabel(self.sidebar, text="Note (QTH / Nome)").pack(anchor="w", padx=20)
        self.ent_note = ctk.CTkEntry(self.sidebar, placeholder_text="es. Roma / Mario")
        self.ent_note.pack(fill="x", padx=20, pady=(0, 15))

        # Pulsante Salva
        self.btn_save = ctk.CTkButton(self.sidebar, text="💾 Salva QSO", fg_color="#2b8a3e", command=self.esegui_salvataggio)
        self.btn_save.pack(fill="x", padx=20)

        # --- PANNELLO DESTRA (TABELLA / STORICO) ---
        self.main_area = ctk.CTkFrame(self, fg_color="transparent")
        self.main_area.grid(row=0, column=1, sticky="nsew", padx=15, pady=15)
        self.main_area.grid_rowconfigure(1, weight=1)
        self.main_area.grid_columnconfigure(0, weight=1)

        self.lbl_stats = ctk.CTkLabel(self.main_area, text="📜 Storico Contatti", font=ctk.CTkFont(size=14, weight="bold"))
        self.lbl_stats.grid(row=0, column=0, sticky="w", pady=(0, 5))

        self.txt_log = ctk.CTkTextbox(self.main_area, font=("Consolas", 11))
        self.txt_log.grid(row=1, column=0, sticky="nsew")

        self.aggiorna_tabella()

    def aggiorna_rst_default(self, modo_selezionato):
        # Imposta i valori di default in base al modo scelto come suggerito da Mario Saretta
        self.ent_rst_in.delete(0, 'end')
        self.ent_rst_out.delete(0, 'end')
        
        if modo_selezionato == "CW":
            self.ent_rst_in.insert(0, "599")
            self.ent_rst_out.insert(0, "599")
        elif modo_selezionato in ["FT8", "FT4"]:
            self.ent_rst_in.insert(0, "00")
            self.ent_rst_out.insert(0, "00")
        else:
            self.ent_rst_in.insert(0, "59")
            self.ent_rst_out.insert(0, "59")

    def esegui_salvataggio(self):
        call = self.ent_call.get().strip()
        station = self.ent_station.get().strip()
        
        if call and station:
            salva_qso(
                station_call=station,
                nominativo=call,
                banda=self.cmb_band.get(),
                modo=self.cmb_mode.get(),
                rst_in=self.ent_rst_in.get(),
                rst_out=self.ent_rst_out.get(),
                wwloc=self.ent_wwloc.get(),
                note=self.ent_note.get()
            )
            self.ent_call.delete(0, 'end')
            self.ent_wwloc.delete(0, 'end')
            self.ent_note.delete(0, 'end')
            self.aggiorna_tabella()
        else:
            if not station:
                self.ent_station.configure(border_color="red")
            if not call:
                self.ent_call.configure(border_color="red")

    def aggiorna_tabella(self):
        self.txt_log.delete("1.0", "end")
        if os.path.exists(LOG_FILE):
            df = pd.read_csv(LOG_FILE)
            df_ordinato = df.iloc[::-1]
            self.txt_log.insert("1.0", df_ordinato.to_string(index=False))
        else:
            self.txt_log.insert("1.0", "Nessun QSO registrato. Inserisci il primo contatto a sinistra.")

if __name__ == "__main__":
    app = App()
    app.mainloop()