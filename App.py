import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import PchipInterpolator
from datetime import date
import streamlit_authenticator as stauth
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.utils import ImageReader
import sqlite3
def genereer_vergelijking_pdf_sidebar(naam, fig, rows):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    main_blue = colors.HexColor("#1E88E5")
    
    # Header
    c.setFillColor(main_blue); c.rect(0, 740, 600, 110, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 24)
    c.drawCentredString(300, 798, "VERGELIJKINGSRAPPORT") 

    c.setFont("Helvetica", 12); c.drawString(50, 765, f"Atleet: {naam} | Datum: {date.today().strftime('%d-%m-%Y')}")
    
    # Grafiek uit de vergelijking
    img_buf = BytesIO()
    fig.savefig(img_buf, format='png', dpi=250, bbox_inches='tight')
    img_buf.seek(0)
    c.drawImage(ImageReader(img_buf), 50, 450, width=500, height=250)
    
    # Tabel
    y = 420
    c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 14); c.drawString(50, y, "DREMPEL ANALYSE"); y -= 30
    c.setFont("Helvetica-Bold", 10); c.drawString(60, y, "Test / Datum"); c.drawString(280, y, "LT1"); c.drawString(360, y, "LT2"); c.drawString(440, y, "Max Lac"); y -= 5
    c.line(50, y, 550, y); y -= 20
    
    c.setFont("Helvetica", 10)
    for r in rows:
        c.drawString(60, y, f"{r['Atleet']} ({r['Datum']})")
        c.drawString(280, y, f"{r['LT1 (W)']}W")
        c.drawString(360, y, f"{r['LT2 (W)']}W")
        c.drawString(440, y, f"{r['Max Lac']} mmol")
        y -= 20
        
    c.save(); buffer.seek(0)
    return buffer

def genereer_apart_vergelijkings_rapport(naam, fig, rows):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    # Header
    c.setFillColor(colors.HexColor("#1E88E5"))
    c.rect(0, 740, 600, 110, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 24)
    c.drawString(50, 790, "VERGELIJKINGSRAPPORT")
    c.setFont("Helvetica", 12)
    c.drawString(50, 765, f"Atleet: {naam} | Rapport gegenereerd op: {date.today()}")
    
    # Grafiek
    img_buf = BytesIO()
    fig.savefig(img_buf, format='png', dpi=200, bbox_inches='tight')
    img_buf.seek(0)
    c.drawImage(ImageReader(img_buf), 50, 450, width=500, height=250)
    
    # Tabel
    y = 420
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(60, y, "Test Historiek")
    c.line(50, y-5, 550, y-5)
    y -= 25
    c.setFont("Helvetica", 10)
    for r in rows:
        c.drawString(60, y, f"• {r['Atleet']} ({r['Datum']}):")
        c.drawString(250, y, f"LT1: {r['LT1 (W)']}W")
        c.drawString(350, y, f"LT2: {r['LT2 (W)']}W")
        c.drawString(450, y, f"Max: {r['Max Lac']} mmol")
        y -= 20
        if y < 50: c.showPage(); y = 800
        
    c.save()
    buffer.seek(0)
    return buffer

def genereer_vergelijkings_pdf(atleet_naam, comp_fig, comp_rows):
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas
    from reportlab.lib.utils import ImageReader
    from reportlab.lib import colors
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    c.setFillColor(colors.HexColor("#1E88E5")); c.rect(0, 740, 600, 110, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 24); c.drawString(50, 790, "VERGELIJKINGSRAPPORT")
    img_comp = BytesIO(); comp_fig.savefig(img_comp, format='png', dpi=200); img_comp.seek(0)
    c.drawImage(ImageReader(img_comp), 50, 460, width=500, height=250)
    y = 420; c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 12)
    for r in comp_rows:
        c.drawString(60, y, f"{r['Atleet']} ({r['Datum']}): LT1 {r['LT1 (W)']}W | LT2 {r['LT2 (W)']}W | Max {r['Max Lac']}"); y -= 20
    c.save(); buffer.seek(0); return buffer

# --- DATABASE LOGICA (NIEUW) ---
def init_db():
    conn = sqlite3.connect('sportlab_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS tests 
                 (id INTEGER PRIMARY KEY, naam TEXT, datum TEXT, watt TEXT, lac TEXT)''')
    conn.commit()
    conn.close()

def save_test(naam, datum, df):
    conn = sqlite3.connect('sportlab_data.db')
    c = conn.cursor()
    # Converteer kolommen naar string voor eenvoudige opslag
    watt_str = ",".join(df['Watt'].astype(str).tolist())
    lac_str = ",".join(df['Lac'].astype(str).tolist())
    c.execute("INSERT INTO tests (naam, datum, watt, lac) VALUES (?, ?, ?, ?)", 
              (naam, str(datum), watt_str, lac_str))
    conn.commit()
    conn.close()

init_db()

# --- 1. BEVEILIGING ---
credentials = {"usernames": {"sportlab": {"name": "Sportlab Admin", "password": "welkom_sportlab"}}}
authenticator = stauth.Authenticate(credentials, "sportlab_cookie", "sportlab_key", cookie_expiry_days=30)
authenticator.login(location='main')

if st.session_state.get("authentication_status"):
    # --- 2. STYLING APP ---
    st.markdown("""
        <style>
        .app-branding { position: absolute; top: -60px; right: 10px; font-size: 32px; font-weight: 900; color: #1E88E5; font-family: 'Arial Black', sans-serif; }
        .biometry-box { background-color: #f8f9fa; padding: 20px; border-radius: 12px; border-left: 6px solid #1E88E5; box-shadow: 2px 2px 10px rgba(0,0,0,0.05); margin-bottom: 20px;}
        </style>
        <div class="app-branding">LacTan+</div>
    """, unsafe_allow_html=True)

    def interp_val(x_target, x_data, y_data):
        if len(x_data) < 2: return 0.0
        try:
            val = PchipInterpolator(x_data, y_data)(x_target)
            return float(np.atleast_1d(val)[0])
        except: return 0.0

    def genereer_pdf_sportlab(naam, datum, gew, leng, leeft, gesl, bmi, vo2, tdee, sum_df, zones_df, test_df, max_vals, fig):
        buffer = BytesIO()
        c = canvas.Canvas(buffer, pagesize=A4)
        main_blue = colors.HexColor("#1E88E5")
        
        def draw_header(canvas_obj, pagenum):
            canvas_obj.setFillColor(main_blue); canvas_obj.rect(0, 740, 600, 110, fill=1, stroke=0)
            canvas_obj.setFillColor(colors.white); canvas_obj.setFont("Helvetica-Bold", 26)
            canvas_obj.drawString(50, 795, "INSPANNINGSANALYSE")
            canvas_obj.setFont("Helvetica", 12); canvas_obj.drawString(50, 770, f"Atleet: {naam} | Datum: {datum} | Pagina {pagenum}")

        # PAGINA 1
        draw_header(c, 1)
        y = 710
        c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 14); c.drawString(50, y, "BIOMETRIE & MAXIMA"); y -= 5; c.setStrokeColor(main_blue); c.line(50, y, 550, y); y -= 25
        c.setFont("Helvetica", 12); c.drawString(50, y, f"Geslacht: {gesl} | Leeftijd: {leeft} jr | Lengte: {leng} cm | Gewicht: {gew} kg"); y -= 20
        c.setFont("Helvetica-Bold", 12); c.drawString(50, y, f"BMI: {bmi:.1f} | VO2max: {vo2:.1f} | TDEE: {int(tdee)} kcal"); y -= 20
        c.setFillColor(main_blue); c.drawString(50, y, f"MAX TESTWAARDEN: {max_vals['Watt']}W | {max_vals['HR']} bpm | {max_vals['Lac']} mmol/L"); c.setFillColor(colors.black)

        y -= 35; c.setFont("Helvetica-Bold", 14); c.drawString(50, y, "ANALYSE DREMPELS"); y -= 5; c.line(50, y, 550, y); y -= 25
        for _, row in sum_df.iterrows():
            c.setFont("Helvetica", 12); c.drawString(60, y, f"• {row['Drempel']}:"); c.setFont("Helvetica-Bold", 12); c.drawString(220, y, f"{row['Waarde']} bij {row['HR']}"); y -= 20

        y -= 20; c.setFont("Helvetica-Bold", 14); c.drawString(50, y, "TRAININGSZONES"); y -= 5; c.line(50, y, 550, y); y -= 25
        for _, row in zones_df.iterrows():
            c.setFillColor(colors.HexColor(row['color'])); c.rect(50, y-2, 10, 10, fill=1, stroke=0)
            c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 11); c.drawString(70, y, f"{row['Zone']}:")
            c.setFont("Helvetica", 12); c.drawString(180, y, f"{row['Watt']} | {row['Hartslag']} | Borg: {row['Borg']}"); y -= 18

        img_buf = BytesIO(); fig.savefig(img_buf, format='png', dpi=250, bbox_inches='tight'); img_buf.seek(0)
        c.drawImage(ImageReader(img_buf), 50, 40, width=500, height=220)

        # PAGINA 2
        c.showPage(); draw_header(c, 2)
        y = 710; c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 14); c.drawString(50, y, "GEDETAILLEERDE TESTGEGEVENS"); y -= 5; c.line(50, y, 550, y); y -= 30
        c.setFont("Helvetica-Bold", 11); c.drawString(70, y, "Stap"); c.drawString(150, y, "Vermogen (W)"); c.drawString(280, y, "Hartslag (bpm)"); c.drawString(420, y, "Lactaat (mmol)"); y -= 20
        c.setFont("Helvetica", 11)
        for i, row in test_df.iterrows():
            c.drawString(70, y, f"Stap {i+1}"); c.drawString(150, y, f"{int(row['Watt'])} W"); c.drawString(280, y, f"{int(row['HR'])} bpm"); c.drawString(420, y, f"{row['Lac']:.1f}"); y -= 18
            if y < 100: c.showPage(); draw_header(c, 2); y = 700
        
        c.save(); 
        buffer.seek(0); 
        return buffer
    
    # --- SIDEBAR ---
    st.sidebar.header("manuele aanpassingen lactaat en trainingzones")
    pal = st.sidebar.select_slider("PAL", options=[1.2, 1.4, 1.6, 1.8, 2.0], value=1.4)
    m_lt1 = st.sidebar.radio("LT1 Methode", ["Baseline + 1.0", "Handmatig"])
    m_lt2 = st.sidebar.radio("LT2 Methode", ["Modified Dmax", "Handmatig"])

    default_z = [
        {"Zone": "Z1", "Naam": "Herstel", "W% LT2 Van": 0, "W% LT2 Tot": 55, "HR% Max Van": 0, "HR% Max Tot": 65, "Borg": "6-9", "color": "#E8F5E9"},
        {"Zone": "Z2", "Naam": "Duur", "W% LT2 Van": 56, "W% LT2 Tot": 75, "HR% Max Van": 66, "HR% Max Tot": 80, "Borg": "10-12", "color": "#C8E6C9"},
        {"Zone": "Z3", "Naam": "Tempo", "W% LT2 Van": 76, "W% LT2 Tot": 90, "HR% Max Van": 81, "HR% Max Tot": 87, "Borg": "13-14", "color": "#FFF9C4"},
        {"Zone": "Z4", "Naam": "Drempel", "W% LT2 Van": 91, "W% LT2 Tot": 105, "HR% Max Van": 88, "HR% Max Tot": 94, "Borg": "15-16", "color": "#FFE0B2"},
        {"Zone": "Z5", "Naam": "VO2max", "W% LT2 Van": 106, "W% LT2 Tot": 150, "HR% Max Van": 95, "HR% Max Tot": 100, "Borg": "17-20", "color": "#FFCDD2"}
    ]
    df_z_cfg = st.sidebar.data_editor(pd.DataFrame(default_z), key="z_edit").dropna()

    # --- INPUT ---
    st.title("Rapport inspanningstest")
    c1, c2, c3 = st.columns(3)
    with c1: n_atl = st.text_input("Naam Atleet", "Voornaam Achternaam"); leeft = st.number_input("Leeftijd", 10, 90, 30)
    with c2: gew = st.number_input("Gewicht (kg)", 30.0, 150.0, 75.0); leng = st.number_input("Lengte (cm)", 120, 220, 180)
    with c3: gesl = st.selectbox("Geslacht", ["Man", "Vrouw"]); test_d = st.date_input("Datum", date.today())

    df_in = st.data_editor(pd.DataFrame({"Watt": [100.0, 150.0, 200.0, 250.0, 300.0, 350.0], "HR": [110.0, 125.0, 140.0, 155.0, 170.0, 185.0], "Lac": [1.0, 1.2, 2.2, 4.5, 9.5, 12.0]}), num_rows="dynamic", width="stretch")

    c_df = df_in.dropna()
    if len(c_df) >= 3:
        x_v, hr_v, lac_v = c_df["Watt"].values, c_df["HR"].values, c_df["Lac"].values
        max_vals = {"Watt": int(x_v.max()), "HR": int(hr_v.max()), "Lac": lac_v.max()}
        xf = np.linspace(x_v.min(), x_v.max(), 1000); yf = PchipInterpolator(x_v, lac_v)(xf)

        # --- DREMPEL FIX VOOR SCALAR ERROR ---
        lt1_idx = np.where(yf >= (np.mean(lac_v[:1]) + 1.0))[0]
        lt1_w = float(xf[lt1_idx[0]]) if lt1_idx.size > 0 else float(x_v[0])
        if m_lt1 == "Handmatig": lt1_w = st.sidebar.slider("Handmatig LT1", int(x_v.min()), int(x_v.max()), int(lt1_w))

        s_idx_f = np.where(yf >= (np.mean(lac_v[:1]) + 0.4))[0]
        s_base = s_idx_f[0] if s_idx_f.size > 0 else 0
        dist = np.abs((yf[-1] - yf[s_base]) * xf[s_base:] - (xf[-1] - xf[s_base]) * yf[s_base:] + xf[-1] * yf[s_base] - yf[-1] * xf[s_base])
        lt2_w = float(xf[s_base + np.argmax(dist)])
        if m_lt2 == "Handmatig": lt2_w = st.sidebar.slider("Handmatig LT2", int(x_v.min()), int(x_v.max()), int(lt2_w))
        lt2_h = interp_val(lt2_w, x_v, hr_v)

        bmi = gew/((leng/100)**2); bmr = (10*gew)+(6.25*leng)-(5*leeft)+(5 if gesl=="Man" else -161); vo2 = ((10.8*x_v.max()/gew)+7)
        st.markdown(f'<div class="biometry-box"><b>Resultaten:</b> LT1: {int(lt1_w)}W | LT2: {int(lt2_w)}W <br> <b>Maxima:</b> {max_vals["Watt"]}W | {max_vals["HR"]}bpm | {max_vals["Lac"]}mmol</div>', unsafe_allow_html=True)

        fig, ax1 = plt.subplots(figsize=(10, 5)); ax2 = ax1.twinx()
        for _, z in df_z_cfg.iterrows():
            ax1.axvspan(lt2_w * z["W% LT2 Van"]/100, lt2_w * z["W% LT2 Tot"]/100, color=z["color"], alpha=0.4)
        ax1.plot(xf, yf, color='#1E88E5', linewidth=3); ax1.scatter(x_v, lac_v, color='#0D47A1', s=60, zorder=5)
        ax2.plot(x_v, hr_v, color='#e53935', linestyle='--', linewidth=2); ax2.scatter(x_v, hr_v, color='#e53935', marker='x', s=40)
        ax1.axvline(lt1_w, color='green', linestyle='--'); ax1.text(lt1_w, yf.max()*0.4, ' LT1', color='green', fontweight='bold', bbox=dict(facecolor='white', alpha=0.8))
        ax1.axvline(lt2_w, color='red', linestyle='--'); ax1.text(lt2_w, yf.max()*0.4, ' LT2', color='red', fontweight='bold', bbox=dict(facecolor='white', alpha=0.8))
        ax1.set_xlim(x_v.min(), x_v.max()); st.pyplot(fig)

        z_tab = []
        for _, r in df_z_cfg.iterrows():
            z_tab.append({"Zone": r['Zone'], "Watt": f"{int(lt2_w*r['W% LT2 Van']/100)}-{int(lt2_w*r['W% LT2 Tot']/100)}W", "Hartslag": f"{int(hr_v.max()*r['HR% Max Van']/100)}-{int(hr_v.max()*r['HR% Max Tot']/100)}bpm", "Borg": r['Borg'], "color": r['color']})
            st.markdown(f'<div style="background-color:{r["color"]}; padding:10px; margin-bottom:5px; border-radius:5px; font-size:16px;"><b>{r["Zone"]}</b> | {z_tab[-1]["Watt"]} | {z_tab[-1]["Hartslag"]} | Borg: {r["Borg"]}</div>', unsafe_allow_html=True)

        sum_data = pd.DataFrame([{"Drempel": "LT1 (Aerobe drempel)", "Waarde": f"{int(lt1_w)}W", "HR": f"{int(interp_val(lt1_w, x_v, hr_v))}bpm"}, {"Drempel": "LT2 (Anaerobe drempel)", "Waarde": f"{int(lt2_w)}W", "HR": f"{int(lt2_h)}bpm"}])
        pdf = genereer_pdf_sportlab(n_atl, test_d, gew, leng, leeft, gesl, bmi, vo2, bmr*pal, sum_data, pd.DataFrame(z_tab), c_df, max_vals, fig)
        st.download_button("📄 Download PDF Rapport", pdf, f"Sportlab_Analyse_{n_atl}.pdf", "application/pdf")    
try:
    # Controleer of er een vergelijking is gemaakt (variabelen fig_c en rows_comp)
    if 'fig_c' in locals() and 'rows_comp' in locals():
        st.sidebar.divider()
        st.sidebar.subheader("Rapportage")
        
        pdf_data = genereer_vergelijking_pdf_sidebar(n_atl, fig_c, rows_comp)
        
        st.sidebar.download_button(
            label="📥 Afdrukken Vergelijking (PDF)",
            data=pdf_data,
            file_name=f"Vergelijking_{n_atl}.pdf",
            mime="application/pdf",
            key="sidebar_pdf_btn"
        )
except Exception as e:
    # Als er nog geen vergelijking is, doe niets
    pass
# --- PROFESSIONEEL VERGELIJKINGSBLOK LacTan+ ---
try:
    if 'c_df' in locals() and not c_df.empty:
        st.divider()
        st.subheader("📊 Vergelijken lactaatanalyses")
        
        # 1. Database Opslag
                # 1. Database Opslag (GEFIKST)
        if st.button("💾 Sla deze meting op ", key="save_db_pro"):
            conn = sqlite3.connect('sportlab_data.db')
            c = conn.cursor()
            # Zorg dat de tabel de juiste kolommen heeft
            c.execute("CREATE TABLE IF NOT EXISTS tests (naam TEXT, datum TEXT, watt TEXT, lac TEXT)")
            
            w_s = ",".join(c_df['Watt'].astype(str).tolist())
            l_s = ",".join(c_df['Lac'].astype(str).tolist())
            
            # Geef expliciet de kolomnamen op om fouten met 'id' of extra kolommen te voorkomen
            c.execute("INSERT INTO tests (naam, datum, watt, lac) VALUES (?, ?, ?, ?)", 
                      (n_atl, str(test_d), w_s, l_s))
            
            conn.commit()
            conn.close()
            st.success("Meting succesvol toegevoegd aan database!"); st.rerun()

        # 2. Data ophalen
        conn = sqlite3.connect('sportlab_data.db')
        db_data = pd.read_sql("SELECT * FROM tests", conn)
        conn.close()

        if not db_data.empty:
            keuze = st.multiselect("Selecteer historische testen voor vergelijking:", db_data.index, 
                                   format_func=lambda x: f"{db_data.iloc[x]['naam']} ({db_data.iloc[x]['datum']})")
            
            if keuze:
                fig_v, ax_v = plt.subplots(figsize=(10, 6))
                tabel_rows = []
                
                for i in keuze:
                    r = db_data.iloc[i]
                    xw = np.array([float(x) for x in r['watt'].split(',')])
                    yl = np.array([float(x) for x in r['lac'].split(',')])
                    xfine = np.linspace(xw.min(), xw.max(), 500)
                    yfine = PchipInterpolator(xw, yl)(xfine)
                    
                    # Drempels berekenen voor tabel
                    i1 = np.where(yfine >= (np.mean(yl[:1]) + 1.0))[0]
                    lt1_v = int(xfine[i1[0]]) if len(i1) > 0 else int(xw[0])
                    i2 = np.where(yfine >= (np.mean(yl[:1]) + 0.4))[0]
                    # Modified Dmax logica
                    s_b = i2[0] if len(i2) > 0 else 0
                    dist = np.abs((yfine[-1]-yfine[s_b])*xfine[s_b:] - (xfine[-1]-xfine[s_b])*yfine[s_b:] + xfine[-1]*yfine[s_b] - yfine[-1]*xfine[s_b])
                    lt2_v = int(xfine[s_b + np.argmax(dist)])

                    line, = ax_v.plot(xfine, yfine, label=f"{r['naam']} ({r['datum']})", linewidth=2.5)
                    color = line.get_color()
                    ax_v.scatter([lt1_v, lt2_v], [interp_val(lt1_v, xw, yl), interp_val(lt2_v, xw, yl)], color=color, edgecolors='white', s=80, zorder=5)
                    
                    tabel_rows.append({"Datum": r['datum'], "Atleet": r['naam'], "LT1 (W)": lt1_v, "LT2 (W)": lt2_v, "Max Lac": f"{yl.max():.1f}"})

                ax_v.set_title("LacTan+ Vergelijkende Lactaatcurve", fontsize=14, fontweight='bold', color='#1E88E5')
                ax_v.set_xlabel("Vermogen (Watt)"); ax_v.set_ylabel("Lactaat (mmol/L)")
                ax_v.legend(); ax_v.grid(True, alpha=0.3)
                st.pyplot(fig_v)
                
                st.write("### 📝 Vergelijkingstabel")
                st.table(pd.DataFrame(tabel_rows))

                # 3. PROFESSIONELE PDF IN SIDEBAR
                with st.sidebar:
                    st.divider()
                    st.markdown("### 📄 LacTan+ Export")
                    buf = BytesIO()
                    c = canvas.Canvas(buf, pagesize=A4)
                    
                    # Blauwe Header
                    c.setFillColor(colors.HexColor("#1E88E5"))
                    c.rect(0, 750, 600, 100, fill=1, stroke=0)
                    c.setFillColor(colors.white)
                    c.setFont("Helvetica-Bold", 28); c.drawString(50, 790, "LacTan+ RAPPORT")
                    c.setFont("Helvetica", 12); c.drawString(50, 770, f"Vergelijkende Analyse - Sportlab Achterbos")
                    
                    # Grafiek invoegen
                    img_v = BytesIO(); fig_v.savefig(img_v, format='png', dpi=250); img_v.seek(0)
                    c.drawImage(ImageReader(img_v), 50, 480, width=500, height=250)
                    
                    # Tabel in PDF
                    y = 440
                    c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 14); c.drawString(50, y, "ANALYSE DATA"); y -= 10
                    c.setStrokeColor(colors.HexColor("#1E88E5")); c.line(50, y, 550, y); y -= 25
                    
                    c.setFont("Helvetica-Bold", 10)
                    c.drawString(60, y, "Datum"); c.drawString(150, y, "Atleet"); c.drawString(280, y, "LT1 (W)"); c.drawString(360, y, "LT2 (W)"); c.drawString(460, y, "Max Lac")
                    y -= 8; c.line(50, y, 550, y); y -= 20
                    
                    c.setFont("Helvetica", 10)
                    for r in tabel_rows:
                        c.drawString(60, y, r['Datum']); c.drawString(150, y, r['Atleet']); c.drawString(280, y, str(r['LT1 (W)'])); c.drawString(360, y, str(r['LT2 (W)'])); c.drawString(460, y, r['Max Lac'])
                        y -= 20
                    
                    c.save()
                    st.download_button("📥 Download LacTan+ Vergelijking", data=buf.getvalue(), file_name=f"LacTan_Vergelijking_{n_atl}.pdf", key="dl_pro")

except Exception as e:
    st.error(f"Er is een fout opgetreden: {e}")

st.subheader("Interpretatie & Opmerkingen")
opmerkingen = st.text_area("Vrije tekstveld voor testobservaties (bijv. vermoeidheid, materiaal, omstandigheden):", 
                          placeholder="Typ hier de observaties van de coach...")
def genereer_pdf_sportlab(naam, datum, gew, leng, leeft, gesl, bmi, vo2, tdee, sum_df, zones_df, test_df, max_vals, fig, logo_file, opmerkingen):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    main_color = colors.HexColor("#0F172A") # Navy Blue
    
    # 1. Blauwe Header met Logo
    c.setFillColor(main_color); c.rect(0, 740, 600, 110, fill=1, stroke=0)
    if logo_file:
        try:
            logo_file.seek(0)
            c.drawImage(ImageReader(logo_file), 480, 755, width=80, height=80, preserveAspectRatio=True, mask='auto')
        except: pass
    
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 24)
    c.drawString(50, 795, "FYSIOLOGISCH TESTRAPPORT")
    c.setFont("Helvetica", 12); c.drawString(50, 770, f"Atleet: {naam} | Datum: {datum}")

    # 2. Persoonsgegevens
    y = 710
    c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 14); c.drawString(50, y, "ANTROPOMETRISCHE DATA"); y -= 20
    c.setFont("Helvetica", 11); c.drawString(50, y, f"Gewicht: {gew}kg | Lengte: {leng}cm | Leeftijd: {leeft}jr | BMI: {bmi:.1f}"); y -= 30

    # 3. Drempels (LT1 & LT2)
    c.setFont("Helvetica-Bold", 14); c.drawString(50, y, "METABOLE DREMPELS"); y -= 20
    c.setFont("Helvetica", 11)
    for _, row in sum_df.iterrows():
        c.drawString(60, y, f"• {row['Drempel']}: {row['Waarde']} ({row['HR']})"); y -= 20
    y -= 10

    # 4. Grafiek (iets kleiner voor ruimte)
    img_buf = BytesIO()
    fig.savefig(img_buf, format='png', dpi=200); img_buf.seek(0)
    c.drawImage(ImageReader(img_buf), 50, 250, width=450, height=200)

    # 5. Eenvoudige Opmerkingen (Onderaan)
    y = 220
    c.setStrokeColor(colors.black); c.line(50, y, 550, y); y -= 20
    c.setFont("Helvetica-Bold", 12); c.drawString(50, y, "OPMERKINGEN COACH:"); y -= 20
    c.setFont("Helvetica", 11)
    
    # Splitst tekst in regels om te voorkomen dat het van de pagina loopt
    for line in opmerkingen.split('\n')[:5]: # Max 5 regels
        c.drawString(60, y, line[:95])
        y -= 15

    c.showPage(); c.save(); buffer.seek(0)
    return buffer
def genereer_pdf_sportlab(naam, datum, gew, leng, leeft, gesl, bmi, vo2, tdee, sum_df, zones_df, test_df, max_vals, fig, logo_file, opmerkingen):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    main_color = colors.HexColor("#0F172A")
    
    # --- PAGINA 1: DASHBOARD & GRAFIEK ---
    c.setFillColor(main_color); c.rect(0, 740, 600, 110, fill=1, stroke=0)
    if logo_file:
        try:
            logo_file.seek(0)
            c.drawImage(ImageReader(logo_file), 480, 755, width=80, height=80, preserveAspectRatio=True, mask='auto')
        except: pass
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 24); c.drawString(50, 795, "FYSIOLOGISCH DASHBOARD")
    c.setFont("Helvetica", 12); c.drawString(50, 770, f"Atleet: {naam} | Datum: {datum}")

    y = 710
    c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 14); c.drawString(50, y, "SAMENVATTING & DREMPELS"); y -= 25
    c.setFont("Helvetica", 11); c.drawString(50, y, f"Gewicht: {gew}kg | BMI: {bmi:.1f} | Max Vermogen: {max_vals['Watt']}W"); y -= 30
    for _, row in sum_df.iterrows():
        c.drawString(60, y, f"• {row['Drempel']}: {row['Waarde']} ({row['HR']})"); y -= 20
    
    img_buf = BytesIO(); fig.savefig(img_buf, format='png', dpi=200, bbox_inches='tight'); img_buf.seek(0)
    c.drawImage(ImageReader(img_buf), 50, 80, width=480, height=280)

    # --- PAGINA 2: GEDETAILLEERDE TESTRESULTATEN ---
    c.showPage()
    c.setFillColor(main_color); c.rect(0, 740, 600, 110, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 20); c.drawString(50, 785, "MEETWAARDEN PER TRAP")

    y_tab = 700
    c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 12); c.drawString(50, y_tab, "RUWE DATA"); y_tab -= 25
    c.setFont("Helvetica-Bold", 10); c.drawString(60, y_tab, "Belasting (Watt)"); c.drawString(200, y_tab, "Lactaat (mmol/L)"); c.drawString(350, y_tab, "Hartslag (bpm)"); y_tab -= 5
    c.line(50, y_tab, 500, y_tab); y_tab -= 20
    c.setFont("Helvetica", 10)
    for _, row in test_df.iterrows():
        c.drawString(60, y_tab, f"{row['Watt']} W"); c.drawString(200, y_tab, f"{row['Lac']} mmol/L"); c.drawString(350, y_tab, f"{row.get('HR', '-')} bpm"); y_tab -= 18
        if y_tab < 50: c.showPage(); y_tab = 800 # Extra pagina bij heel veel data

    # --- PAGINA 3: UITGEBREIDE COACH ANALYSE ---
    c.showPage()
    c.setFillColor(main_color); c.rect(0, 740, 600, 110, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 20); c.drawString(50, 785, "ANALYSES & INTERPRETATIE")

    y_note = 700
    c.setFillColor(colors.black); c.setFont("Helvetica-Bold", 14); c.drawString(50, y_note, "OPMERKINGEN & ADVIES"); y_note -= 30
    c.setFont("Helvetica", 11); text_obj = c.beginText(60, y_note); text_obj.setLeading(16)
    if opmerkingen:
        for line in opmerkingen.split('\n'):
            # Eenvoudige word wrap
            if len(line) > 90:
                text_obj.textLine(line[:90] + "-")
                text_obj.textLine(line[90:180])
            else:
                text_obj.textLine(line)
    else:
        text_obj.textLine("Geen extra opmerkingen geformuleerd.")
    c.drawText(text_obj)

    # --- AFSLUITING ---
       # --- AFSLUITING ---
    c.save()
    buffer.seek(0)  # Zorg dat deze regel op hetzelfde niveau staat als c.save()
    return buffer

