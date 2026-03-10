import streamlit as st
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from scipy.interpolate import PchipInterpolator
from datetime import date, datetime
from io import BytesIO

try:
    from supabase import create_client, Client
    SUPABASE_OK = True
except ImportError:
    SUPABASE_OK = False

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.pdfgen import canvas as rl_canvas
    from reportlab.lib import colors
    from reportlab.lib.utils import ImageReader
    REPORTLAB_OK = True
except ImportError:
    REPORTLAB_OK = False

# ─────────────────────────────────────────────
#  PAGINA CONFIG
# ─────────────────────────────────────────────
st.set_page_config(page_title="LacTan+", page_icon="🚴", layout="wide")

# ─────────────────────────────────────────────
#  LOGIN
# ─────────────────────────────────────────────
# ─────────────────────────────────────────────
# Laad gebruikers uit Streamlit Secrets of gebruik standaard
try:
    USERS = dict(st.secrets["users"])
except Exception:
    USERS = {"sportlab": "welkom_sportlab", "admin": "lactan2024"}

def check_login():
    if "logged_in" not in st.session_state:
        st.session_state.logged_in = False
    if st.session_state.logged_in:
        return True
    st.markdown("""
        <style>
        [data-testid="stAppViewContainer"] {
            background: linear-gradient(135deg, #0F172A 0%, #1E3A5F 100%) !important;
        }
        [data-testid="stMain"] { background: transparent !important; }
        [data-testid="stHeader"] { background: transparent !important; }
        .block-container { padding-top: 0 !important; }
        .login-outer {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 80vh;
            padding-top: 40px;
        }
        .login-title {
            font-size: 52px;
            font-weight: 900;
            color: white !important;
            text-align: center;
            letter-spacing: -1px;
            margin-bottom: 6px;
        }
        .login-plus {
            color: #1E88E5;
        }
        .login-sub {
            text-align: center;
            font-size: 16px;
            color: #93C5FD;
            margin-bottom: 36px;
        }
        .login-card {
            background: white;
            border-radius: 16px;
            padding: 36px 40px 32px 40px;
            width: 100%;
            max-width: 420px;
            box-shadow: 0 24px 60px rgba(0,0,0,0.5);
        }
        label { color: #1E293B !important; font-weight: 600 !important; font-size: 14px !important; }
        .stTextInput label { display: none !important; }
        .stTextInput > div > div > input {
            border: 1.5px solid rgba(255,255,255,0.25) !important;
            border-radius: 10px !important;
            color: #0F172A !important;
            background: rgba(255,255,255,0.92) !important;
            font-size: 15px !important;
            padding: 12px 16px !important;
        }
        .stTextInput > div > div > input::placeholder {
            color: #94A3B8 !important;
        }
        .stButton > button {
            background: linear-gradient(90deg, #1E88E5, #1565C0) !important;
            color: white !important;
            border-radius: 10px !important;
            font-size: 16px !important;
            font-weight: 700 !important;
            padding: 12px !important;
            border: none !important;
            margin-top: 8px !important;
            width: 100% !important;
        }
        .login-footer {
            text-align: center;
            font-size: 11px;
            color: #64748B;
            margin-top: 18px;
        }
        </style>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown('<div class="login-title">LacTan<span class="login-plus">+</span></div>', unsafe_allow_html=True)
        st.markdown('<div class="login-sub">Inspanningstest Platform</div>', unsafe_allow_html=True)
        username = st.text_input("Gebruikersnaam", placeholder="Voer gebruikersnaam in", label_visibility="hidden")
        password = st.text_input("Wachtwoord", type="password", placeholder="Voer wachtwoord in", label_visibility="hidden")
        if st.button("Inloggen", type="primary", use_container_width=True):
            if username in USERS and USERS[username] == password:
                st.session_state.logged_in = True
                st.session_state.username = username
                st.rerun()
            else:
                st.error("❌ Ongeldige gebruikersnaam of wachtwoord")
        st.markdown('<div class="login-footer">© 2026 LacTan+ · Vertrouwelijk platform voor sportlaboratoria</div>', unsafe_allow_html=True)
    return False

if not check_login():
    st.stop()

# ─────────────────────────────────────────────
#  DATABASE (Supabase met session_state fallback)
# ─────────────────────────────────────────────
def get_supabase():
    """Maak Supabase client aan via Streamlit secrets."""
    try:
        url = st.secrets["SUPABASE_URL"]
        key = st.secrets["SUPABASE_KEY"]
        return create_client(url, key) if SUPABASE_OK else None
    except Exception:
        return None

def init_db():
    """Initialiseer lokale fallback opslag."""
    if "db_tests" not in st.session_state:
        st.session_state.db_tests = []
    if "db_next_id" not in st.session_state:
        st.session_state.db_next_id = 1

def save_test(naam, datum, watt_list, lac_list, hr_list):
    init_db()
    gebruiker = st.session_state.get("username", "onbekend")
    watt_str = ",".join([str(float(v)) for v in watt_list])
    lac_str  = ",".join([str(float(v)) for v in lac_list])
    hr_str   = ",".join([str(float(v)) for v in hr_list])

    sb = get_supabase()
    if sb:
        try:
            sb.table("tests").insert({
                "naam":      naam,
                "datum":     str(datum),
                "watt":      watt_str,
                "lac":       lac_str,
                "hr":        hr_str,
                "gebruiker": gebruiker,
            }).execute()
            return
        except Exception as e:
            st.warning(f"Supabase opslaan mislukt, lokaal opgeslagen: {e}")

    # Fallback: session_state
    st.session_state.db_tests.insert(0, {
        "id":        st.session_state.db_next_id,
        "naam":      naam,
        "datum":     str(datum),
        "watt":      watt_str,
        "lac":       lac_str,
        "hr":        hr_str,
        "gebruiker": gebruiker,
    })
    st.session_state.db_next_id += 1

def load_tests():
    init_db()
    gebruiker = st.session_state.get("username", "onbekend")
    sb = get_supabase()
    if sb:
        try:
            res = (sb.table("tests")
                     .select("*")
                     .eq("gebruiker", gebruiker)
                     .order("id", desc=True)
                     .execute())
            if res.data:
                return pd.DataFrame(res.data)
            return pd.DataFrame()
        except Exception:
            pass

    # Fallback: session_state (filter op gebruiker)
    gefilterd = [r for r in st.session_state.db_tests
                 if r.get("gebruiker", "onbekend") == gebruiker]
    if not gefilterd:
        return pd.DataFrame()
    return pd.DataFrame(gefilterd)

def delete_test(test_id):
    init_db()
    gebruiker = st.session_state.get("username", "onbekend")
    sb = get_supabase()
    if sb:
        try:
            sb.table("tests").delete().eq("id", int(test_id)).eq("gebruiker", gebruiker).execute()
            return
        except Exception:
            pass

    # Fallback: session_state
    st.session_state.db_tests = [
        r for r in st.session_state.db_tests
        if not (r["id"] == int(test_id) and r.get("gebruiker") == gebruiker)
    ]

init_db()

# ─────────────────────────────────────────────
#  HELPERS
# ─────────────────────────────────────────────
def interp_val(x_target, x_data, y_data):
    try:
        val = PchipInterpolator(x_data, y_data)(x_target)
        return float(np.atleast_1d(val)[0])
    except Exception:
        return 0.0

def bereken_leeftijd(geboortedatum):
    today = date.today()
    return today.year - geboortedatum.year - ((today.month, today.day) < (geboortedatum.month, geboortedatum.day))

def bereken_drempels(x_v, lac_v, lt1_methode, lt2_methode,
                     lt1_handmatig=None, lt2_handmatig=None):
    xf = np.linspace(x_v.min(), x_v.max(), 1000)
    yf = PchipInterpolator(x_v, lac_v)(xf)
    baseline = float(np.mean(lac_v[:2]))
    lt1_idx = np.where(yf >= baseline + 1.0)[0]
    lt1_w = float(xf[lt1_idx[0]]) if lt1_idx.size > 0 else float(x_v[0])
    if lt1_methode == "Handmatig" and lt1_handmatig is not None:
        lt1_w = float(lt1_handmatig)
    s_idx  = np.where(yf >= baseline + 0.4)[0]
    s_base = s_idx[0] if s_idx.size > 0 else 0
    dist = np.abs(
        (yf[-1] - yf[s_base]) * xf[s_base:] -
        (xf[-1] - xf[s_base]) * yf[s_base:] +
        xf[-1] * yf[s_base] - yf[-1] * xf[s_base]
    )
    lt2_w = float(xf[s_base + np.argmax(dist)])
    if lt2_methode == "Handmatig" and lt2_handmatig is not None:
        lt2_w = float(lt2_handmatig)
    return lt1_w, lt2_w, xf, yf

def bereken_vo2max(watt_max, gew, hr_max, hr_rust=60):
    """VO2max fietsen: Storer + Legge & Banister, gemiddelde."""
    vo2_storer = (10.8 * watt_max / gew) + 7.0
    vo2_lb_lmin = (0.01141 * watt_max) + (0.01206 * gew) - 0.9090
    vo2_lb = (vo2_lb_lmin * 1000) / gew
    vo2_gem = (vo2_storer + vo2_lb) / 2
    return round(vo2_gem, 1), round(vo2_storer, 1), round(vo2_lb, 1)

def bereken_vo2max_lopen(snelheid_max, hr_max, hr_rust=60, leeft=30):
    """
    VO2max lopen via twee methoden, gemiddelde als eindwaarde.
    1. Léger & Bouchard (loopband): VO2max = 3.5 * v (km/u) bij maximale snelheid
       Verfijnd: VO2 = -4.60 + 0.182258 * v * 60 + 0.000104 * (v*60)^2  (Bruce protocol)
       Praktisch voor traptest: VO2max = 3.5 * vmax (ml/kg/min)
    2. Hartslag methode (Fox): VO2max = 15 * HRmax / HRrust
    """
    # Methode 1: Léger loopband formule (vmax in km/u)
    vo2_leger = 3.5 * snelheid_max

    # Methode 2: Hartslag reservemethode (Fox & Haskell)
    hr_rust_schat = hr_rust if hr_rust > 40 else 60
    vo2_hr = 15.0 * hr_max / hr_rust_schat

    vo2_gem = (vo2_leger + vo2_hr) / 2
    return round(vo2_gem, 1), round(vo2_leger, 1), round(vo2_hr, 1)

def energie_verdeling(tdee, lt1_w, lt2_w, lt2_w_ref):
    """Schat energieverdeling per zone op basis van TDEE en drempelverhouding."""
    pct_z1 = 0.30; pct_z2 = 0.35; pct_z3 = 0.20; pct_z4 = 0.10; pct_z5 = 0.05
    return {
        "Basaalmetabolisme (BMR)": int(tdee / 1.4),
        "Totaal dagelijks (TDEE)": int(tdee),
        "Z1 Herstel (geschat)":    int(tdee * pct_z1),
        "Z2 Duur (geschat)":       int(tdee * pct_z2),
        "Z3 Tempo (geschat)":      int(tdee * pct_z3),
        "Z4 Drempel (geschat)":    int(tdee * pct_z4),
        "Z5 VO2max (geschat)":     int(tdee * pct_z5),
    }

# ─────────────────────────────────────────────
#  PDF GENERATIE
# ─────────────────────────────────────────────
def genereer_pdf(naam, geboortedatum, sport, doelen, datum,
                 gew, leng, leeft, gesl,
                 bmi, vo2_gem, vo2_storer, vo2_lb, tdee, bmr,
                 lt1_w, lt2_w, max_vals,
                 fig, zones_lijst, test_df,
                 logo_file, opmerkingen, labo_naam="Sportlab Achterbos", is_lopen=False):
    if not REPORTLAB_OK:
        return None

    buffer = BytesIO()
    c = rl_canvas.Canvas(buffer, pagesize=A4)
    W, H = A4
    navy     = colors.HexColor("#0F172A")
    blue     = colors.HexColor("#1E88E5")
    blue_mid = colors.HexColor("#1565C0")
    light    = colors.HexColor("#EFF6FF")
    grey_bg  = colors.HexColor("#F8FAFC")
    grey_ln  = colors.HexColor("#CBD5E1")
    green    = colors.HexColor("#16A34A")
    red_c    = colors.HexColor("#DC2626")

    # ── Sub-functies ────────────────────────────
    def draw_header(titel, sub, pagina, totaal):
        # Achtergrond
        c.setFillColor(navy)
        c.rect(0, H-112, W, 112, fill=1, stroke=0)
        # Blauwe accentlijn
        c.setFillColor(blue)
        c.rect(0, H-115, W, 3, fill=1, stroke=0)
        # Logo
        if logo_file:
            try:
                logo_file.seek(0)
                c.drawImage(ImageReader(logo_file), W-115, H-100,
                            width=85, height=75, preserveAspectRatio=True, mask='auto')
            except Exception:
                pass
        # Titel
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 24)
        c.drawString(45, H-48, titel)
        c.setFont("Helvetica", 11)
        c.setFillColor(colors.HexColor("#93C5FD"))
        c.drawString(45, H-66, sub)
        c.setFillColor(colors.HexColor("#64748B"))
        c.setFont("Helvetica", 9)
        c.drawString(45, H-82, f"{labo_naam}  —  LacTan+  |  {date.today().strftime('%d %B %Y')}  |  Pagina {pagina} / {totaal}")
        # Rechts: atleet info
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawRightString(W-130 if logo_file else W-45, H-48, naam)
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.HexColor("#93C5FD"))
        c.drawRightString(W-130 if logo_file else W-45, H-62, f"Testdatum: {datum}")
        c.drawRightString(W-130 if logo_file else W-45, H-75, f"{sport}  |  {gesl}")

    def section(tekst, y, icon=""):
        c.setFillColor(blue)
        c.rect(45, y, W-90, 22, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#93C5FD"))
        c.rect(45, y, 5, 22, fill=1, stroke=0)
        c.setFillColor(colors.white)
        c.setFont("Helvetica-Bold", 10)
        c.drawString(58, y+6, f"{icon}  {tekst}" if icon else tekst)
        return y - 16   # extra ruimte onder sectietitel

    def vo2_label(x, y, fontsize=10, bold=False):
        """Schrijft VO2max met kleine subscript 2, zonder unicode"""
        font = "Helvetica-Bold" if bold else "Helvetica"
        c.setFont(font, fontsize)
        c.drawString(x, y, "VO")
        tw = c.stringWidth("VO", font, fontsize)
        c.setFont(font, fontsize * 0.65)
        c.drawString(x + tw, y - 2, "2")
        tw2 = c.stringWidth("2", font, fontsize * 0.65)
        c.setFont(font, fontsize)
        c.drawString(x + tw + tw2, y, "max")

    def vo2_label_centered(cx, y, fontsize=10, bold=False):
        """Gecentreerde VO2max met subscript"""
        font = "Helvetica-Bold" if bold else "Helvetica"
        w_vo = c.stringWidth("VO", font, fontsize)
        w_2  = c.stringWidth("2", font, fontsize * 0.65)
        w_mx = c.stringWidth("max", font, fontsize)
        total = w_vo + w_2 + w_mx
        x = cx - total / 2
        c.setFont(font, fontsize); c.drawString(x, y, "VO")
        c.setFont(font, fontsize * 0.65); c.drawString(x + w_vo, y - 2, "2")
        c.setFont(font, fontsize); c.drawString(x + w_vo + w_2, y, "max")

    def pill(label, value, unit, x, y, w=118, h=52, color=None):
        bg = color if color else light
        c.setFillColor(bg)
        c.roundRect(x, y, w, h, 7, fill=1, stroke=0)
        c.setFillColor(grey_ln)
        c.roundRect(x, y, w, h, 7, fill=0, stroke=1)
        c.setFillColor(blue)
        c.setFont("Helvetica-Bold", 8)
        c.drawCentredString(x+w/2, y+h-14, label.upper())
        c.setFillColor(navy)
        c.setFont("Helvetica-Bold", 15)
        c.drawCentredString(x+w/2, y+18, str(value))
        c.setFillColor(colors.HexColor("#64748B"))
        c.setFont("Helvetica", 7.5)
        c.drawCentredString(x+w/2, y+7, unit)

    def row_line(y, shade=False):
        if shade:
            c.setFillColor(grey_bg)
            c.rect(45, y-3, W-90, 16, fill=1, stroke=0)

    def footer():
        c.setFillColor(grey_ln)
        c.rect(0, 0, W, 28, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#64748B"))
        c.setFont("Helvetica", 7.5)
        c.drawString(45, 10, f"LacTan+ Inspanningsanalyse  |  {naam}  |  {datum}  |  Vertrouwelijk document")
        c.drawRightString(W-45, 10, f"{labo_naam}  |  © {date.today().year} LacTan+")

    lt1_hr = interp_val(lt1_w, test_df["Watt"].values.astype(float), test_df["HR"].values.astype(float))
    lt2_hr = interp_val(lt2_w, test_df["Watt"].values.astype(float), test_df["HR"].values.astype(float))

    # ════════════════════════════════════════════
    #  PAGINA 1  –  Overzicht & Grafiek
    # ════════════════════════════════════════════
    draw_header("INSPANNINGSTEST", f"Fysiologisch Testrapport  |  {sport}", 1, 4)
    y = H - 130

    # ── Pills rij 1: antropometrie ──
    pw = 118; gap = 10; pill_h = 56
    px = 45
    pill("Gewicht",  f"{gew}",   "kg",     px,        y - pill_h); px += pw+gap
    pill("Lengte",   f"{leng}",  "cm",     px,        y - pill_h); px += pw+gap
    pill("Leeftijd", f"{leeft}", "jaar",   px,        y - pill_h); px += pw+gap
    pill("Geslacht", gesl,       "",       px,        y - pill_h)

    y = y - pill_h - 18   # ruimte tussen de twee rijen pills

    # ── Hulpfunctie tempo ──
    def pdf_tempo(kmh):
        if kmh <= 0: return "-"
        sec = 3600 / kmh
        return f"{int(sec//60)}:{int(sec%60):02d}/km"

    # ── Pills rij 2: fysiologie ──
    px = 45
    pill("BMI",       f"{bmi:.1f}",         "kg/m\u00b2",  px, y - pill_h); px += pw+gap
    pill("VO2max",    f"{vo2_gem}",          "ml/kg/min",  px, y - pill_h); px += pw+gap
    if is_lopen:
        pill("Max. km/u", f"{max_vals['Watt']:.1f}", "km/u", px, y - pill_h); px += pw+gap
    else:
        pill("Max. Watt", f"{max_vals['Watt']}", "W",       px, y - pill_h); px += pw+gap
    pill("Max. HR",   f"{max_vals['HR']}",   "bpm",        px, y - pill_h)

    y = y - pill_h - 30

    y = section("METABOLE DREMPELS", y)
    y -= 16

    # LT1 blok
    blok_h = 58
    blok_w = (W - 100) / 2 - 5
    c.setFillColor(colors.HexColor("#DCFCE7"))
    c.roundRect(45, y - blok_h, blok_w, blok_h, 7, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#BBF7D0"))
    c.roundRect(45, y - blok_h, blok_w, blok_h, 7, fill=0, stroke=1)
    c.setFillColor(green)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(58, y - 14, "LT1  –  Aerobe drempel")
    c.setFillColor(navy)
    c.setFont("Helvetica-Bold", 20)
    if is_lopen:
        c.drawString(58, y - 36, f"{lt1_w:.1f} km/u")
        c.setFillColor(colors.HexColor("#374151"))
        c.setFont("Helvetica", 9)
        c.drawString(58, y - 50, f"{pdf_tempo(lt1_w)}  @  {int(lt1_hr)} bpm")
    else:
        c.drawString(58, y - 36, f"{int(lt1_w)} W")
        c.setFillColor(colors.HexColor("#374151"))
        c.setFont("Helvetica", 10)
        c.drawString(58 + 80, y - 36, f"@ {int(lt1_hr)} bpm")

    # LT2 blok
    x2 = 45 + blok_w + 10
    c.setFillColor(colors.HexColor("#FEE2E2"))
    c.roundRect(x2, y - blok_h, blok_w, blok_h, 7, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#FECACA"))
    c.roundRect(x2, y - blok_h, blok_w, blok_h, 7, fill=0, stroke=1)
    c.setFillColor(red_c)
    c.setFont("Helvetica-Bold", 9)
    c.drawString(x2 + 13, y - 14, "LT2  –  Anaerobe drempel")
    c.setFillColor(navy)
    c.setFont("Helvetica-Bold", 20)
    if is_lopen:
        c.drawString(x2 + 13, y - 36, f"{lt2_w:.1f} km/u")
        c.setFillColor(colors.HexColor("#374151"))
        c.setFont("Helvetica", 9)
        c.drawString(x2 + 13, y - 50, f"{pdf_tempo(lt2_w)}  @  {int(lt2_hr)} bpm")
    else:
        c.drawString(x2 + 13, y - 36, f"{int(lt2_w)} W")
        c.setFillColor(colors.HexColor("#374151"))
        c.setFont("Helvetica", 10)
        c.drawString(x2 + 13 + 80, y - 36, f"@ {int(lt2_hr)} bpm")

    y = y - blok_h - 32   # ruimte onder drempelblokken

    y = section("LACTAAT- EN HARTSLAGCURVE", y)
    y -= 14
    img_buf = BytesIO()
    fig.savefig(img_buf, format='png', dpi=200, bbox_inches='tight')
    img_buf.seek(0)
    graph_h = max(190, min(230, y - 45))
    c.drawImage(ImageReader(img_buf), 45, y - graph_h, width=W-90, height=graph_h)

    footer()

    # ════════════════════════════════════════════
    #  PAGINA 2  –  Zones + Data + Energie
    # ════════════════════════════════════════════
    c.showPage()
    draw_header("INSPANNINGSTEST", "Trainingszones & Meetdata", 2, 4)
    y = H - 130

    y = section("TRAININGSZONES", y)
    y -= 14   # ruimte onder sectietitel

    RZ = 26   # rij-hoogte zones
    RT = 25   # rij-hoogte testdata
    RE = 25   # rij-hoogte energie

    # Tabelheader zones
    c.setFillColor(navy); c.setFont("Helvetica-Bold", 9.5)
    if is_lopen:
        cols_z = [45, 95, 158, 268, 378, 458]
        hdrs_z = ["Zone", "Naam", "Snelheid (km/u)", "Tempo (min/km)", "Hartslag (bpm)", "Borg"]
    else:
        cols_z = [45, 95, 158, 290, 400, 478]
        hdrs_z = ["Zone", "Naam", "Vermogen (W)", "Hartslag (bpm)", "Borg", "% LT2"]
    for cx, hdr in zip(cols_z, hdrs_z):
        c.drawString(cx, y, hdr)
    y -= 8
    c.setStrokeColor(blue); c.setLineWidth(0.8); c.line(45, y, W-45, y); y -= RZ

    c.setFont("Helvetica", 10)
    for idx_z, z in enumerate(zones_lijst):
        w_van = lt2_w * z["W_van"] / 100
        w_tot = lt2_w * z["W_tot"] / 100
        h_van = int(max_vals["HR"] * z["HR_van"] / 100)
        h_tot = int(max_vals["HR"] * z["HR_tot"] / 100)
        try:
            zc = colors.HexColor(z["color"])
        except Exception:
            zc = colors.lightblue
        if idx_z % 2 == 0:
            c.setFillColor(grey_bg)
            c.rect(45, y-6, W-90, RZ, fill=1, stroke=0)
        c.setFillColor(zc)
        c.roundRect(cols_z[0], y-3, 42, 17, 3, fill=1, stroke=0)
        c.setFillColor(navy); c.setFont("Helvetica-Bold", 9)
        c.drawCentredString(cols_z[0]+21, y+3, z["Zone"])
        c.setFont("Helvetica", 10); c.setFillColor(colors.black)
        c.drawString(cols_z[1], y+3, str(z["Naam"]))
        if is_lopen:
            c.drawString(cols_z[2], y+3, f"{w_van:.1f} – {w_tot:.1f}")
            c.drawString(cols_z[3], y+3, f"{pdf_tempo(w_van)} – {pdf_tempo(w_tot)}")
            c.drawString(cols_z[4], y+3, f"{h_van} – {h_tot}")
            c.drawString(cols_z[5], y+3, str(z["Borg"]))
        else:
            c.drawString(cols_z[2], y+3, f"{int(w_van)} – {int(w_tot)}")
            c.drawString(cols_z[3], y+3, f"{h_van} – {h_tot}")
            c.drawString(cols_z[4], y+3, str(z["Borg"]))
            c.drawString(cols_z[5], y+3, f"{z['W_van']}–{z['W_tot']}%")
        y -= RZ
        if y < 90:
            break

    y -= 22
    y = section("RUWE TESTGEGEVENS PER TRAP", y)
    y -= 14

    if is_lopen:
        col_t  = [50, 130, 248, 348, 448]
        hdrs_t = ["Trap", "Snelheid (km/u)", "Tempo (min/km)", "Hartslag (bpm)", "Lactaat (mmol/L)"]
    else:
        col_t  = [50, 130, 248, 365, 465]
        hdrs_t = ["Trap", "Vermogen (W)", "Hartslag (bpm)", "Lactaat (mmol/L)", "Borg"]
    c.setFillColor(navy); c.setFont("Helvetica-Bold", 9.5)
    for cx, hdr in zip(col_t, hdrs_t):
        c.drawString(cx, y, hdr)
    y -= 8; c.setStrokeColor(blue); c.line(45, y, W-45, y); y -= RT

    c.setFont("Helvetica", 10)
    for i, row in test_df.reset_index(drop=True).iterrows():
        if i % 2 == 0:
            c.setFillColor(grey_bg)
            c.rect(45, y-6, W-90, RT, fill=1, stroke=0)
        c.setFillColor(colors.black)
        watt_val = float(row['Watt'])
        c.drawString(col_t[0], y+3, f"Trap {i+1}")
        if is_lopen:
            c.drawString(col_t[1], y+3, f"{watt_val:.1f} km/u")
            c.drawString(col_t[2], y+3, pdf_tempo(watt_val))
            c.drawString(col_t[3], y+3, f"{int(float(row['HR']))} bpm")
            c.drawString(col_t[4], y+3, f"{float(row['Lac']):.2f}")
        else:
            c.drawString(col_t[1], y+3, f"{int(watt_val)} W")
            c.drawString(col_t[2], y+3, f"{int(float(row['HR']))} bpm")
            c.drawString(col_t[3], y+3, f"{float(row['Lac']):.2f}")
            borg_val = row.get('Borg', '-')
            c.drawString(col_t[4], y+3, str(borg_val) if str(borg_val) != 'nan' else "–")
        y -= RT
        if y < 90:
            c.showPage()
            draw_header("INSPANNINGSTEST", "Trainingszones & Meetdata", 2, 4)
            y = H - 130

    # Energieoverzicht
    y -= 22
    if y > 160:
        y = section("GESCHATTE DAGELIJKSE ENERGIEBEHOEFTE", y)
        y -= 10

        energie = {
            "Basaalmetabolisme (BMR)": (int(bmr), "kcal/dag – ruststofwisseling"),
            "Totaal dagelijks (TDEE)": (int(tdee), f"kcal/dag – PAL factor {pal:.1f}"),
        }
        c.setFont("Helvetica-Bold", 9.5); c.setFillColor(navy)
        c.drawString(55, y, "Component"); c.drawString(295, y, "Waarde"); c.drawString(390, y, "Toelichting")
        y -= 8; c.setStrokeColor(blue); c.line(45, y, W-45, y); y -= RE

        c.setFont("Helvetica", 10)
        for ei, (label, (val, toel)) in enumerate(energie.items()):
            if ei % 2 == 0:
                c.setFillColor(grey_bg); c.rect(45, y-6, W-90, RE, fill=1, stroke=0)
            c.setFillColor(colors.black)
            c.drawString(55, y+4, label)
            c.setFont("Helvetica-Bold", 10); c.drawString(295, y+4, f"{val} kcal")
            c.setFont("Helvetica", 9.5);     c.drawString(390, y+4, toel)
            y -= RE

    footer()

    # ════════════════════════════════════════════
    #  PAGINA 3  –  VO2max + Profiel
    # ════════════════════════════════════════════
    c.showPage()
    draw_header("INSPANNINGSTEST", "VO2max Analyse & Atletenprofiel", 3, 4)
    y = H - 130

    # Atleet profiel
    y = section("ATLETENPROFIEL", y)
    y -= 14
    RP = 24
    profiel = [
        ("Naam",               naam),
        ("Geboortedatum",      geboortedatum.strftime("%d/%m/%Y") if hasattr(geboortedatum, 'strftime') else str(geboortedatum)),
        ("Leeftijd",           f"{leeft} jaar"),
        ("Geslacht",           gesl),
        ("Sport / Discipline", sport if sport else "-"),
        ("Trainingsdoelen",    doelen if doelen else "-"),
        ("Testdatum",          str(datum)),
        ("Gewicht / Lengte",   f"{gew} kg  /  {leng} cm"),
        ("BMI",                f"{bmi:.1f} kg/m2"),
    ]
    for pi, (lbl, val) in enumerate(profiel):
        if pi % 2 == 0:
            c.setFillColor(grey_bg); c.rect(45, y-6, W-90, RP, fill=1, stroke=0)
        c.setFillColor(blue); c.setFont("Helvetica-Bold", 10); c.drawString(55, y+4, lbl)
        c.setFillColor(navy); c.setFont("Helvetica", 10);      c.drawString(245, y+4, val)
        y -= RP

    y -= 24

    # ── VO2MAX ANALYSE sectietitel handmatig (geen unicode) ──
    c.setFillColor(blue); c.rect(45, y, W-90, 22, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#93C5FD")); c.rect(45, y, 5, 22, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 10)
    c.drawString(58, y+6, "VO2MAX ANALYSE")
    y -= 16 + 16

    blok_h2 = 82
    c.setFillColor(light); c.roundRect(45, y - blok_h2, W-90, blok_h2, 7, fill=1, stroke=0)
    c.setFillColor(grey_ln); c.roundRect(45, y - blok_h2, W-90, blok_h2, 7, fill=0, stroke=1)

    col_l = 58
    col_r = W - 58

    # Header
    c.setFillColor(navy); c.setFont("Helvetica-Bold", 9.5)
    c.drawString(col_l, y - 12, "Methode")
    c.drawRightString(col_r, y - 12, "VO2max (ml/kg/min)")
    c.setStrokeColor(grey_ln); c.setLineWidth(0.5)
    c.line(col_l, y - 16, col_r, y - 16)

    # Rij 1
    c.setFont("Helvetica", 10); c.setFillColor(colors.HexColor("#374151"))
    m1_naam = "Léger & Bouchard (loopband — vmax × 3.5)" if is_lopen else "Storer et al. (fietsergometer)"
    c.drawString(col_l, y - 30, m1_naam)
    c.setFont("Helvetica-Bold", 10); c.setFillColor(navy)
    c.drawRightString(col_r, y - 30, f"{vo2_storer} ml/kg/min")

    # Rij 2 (shaded)
    c.setFillColor(grey_bg); c.rect(46, y - 49, W - 93, 17, fill=1, stroke=0)
    c.setFont("Helvetica", 10); c.setFillColor(colors.HexColor("#374151"))
    m2_naam = "Fox & Haskell (hartslagreserve — 15 × HRmax / HRrust)" if is_lopen else "Legge & Banister (vermogen/gewicht)"
    c.drawString(col_l, y - 45, m2_naam)
    c.setFont("Helvetica-Bold", 10); c.setFillColor(navy)
    c.drawRightString(col_r, y - 45, f"{vo2_lb} ml/kg/min")

    # Rij 3 (highlighted blauw)
    c.setFillColor(colors.HexColor("#DBEAFE")); c.rect(46, y - 68, W - 93, 17, fill=1, stroke=0)
    c.setFont("Helvetica-Bold", 10); c.setFillColor(blue)
    c.drawString(col_l, y - 63, "Gemiddelde (aanbevolen waarde)")
    c.drawRightString(col_r, y - 63, f"{vo2_gem} ml/kg/min")

    y -= blok_h2 + 24

    # ── VO2MAX REFERENTIEWAARDEN sectietitel ──
    c.setFillColor(blue); c.rect(45, y, W-90, 22, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#93C5FD")); c.rect(45, y, 5, 22, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 10)
    c.drawString(58, y+6, "VO2MAX REFERENTIEWAARDEN  (ml/kg/min)")
    y -= 16 + 16

    # Normtabel: recreatief / competitief / topsport, man of vrouw
    if gesl == "Man":
        normen = [
            ("Recreatief",   "< 35",   "35 - 44",  "45 - 52",  "> 52"),
            ("Competitief",  "< 50",   "50 - 57",  "58 - 64",  "> 64"),
            ("Topsport",     "< 60",   "60 - 68",  "69 - 75",  "> 75"),
        ]
    else:
        normen = [
            ("Recreatief",   "< 28",   "28 - 35",  "36 - 42",  "> 42"),
            ("Competitief",  "< 40",   "40 - 47",  "48 - 54",  "> 54"),
            ("Topsport",     "< 50",   "50 - 57",  "58 - 65",  "> 65"),
        ]

    RN = 26
    nrm_cols = [55, 175, 295, 385, 470]
    nrm_hdrs = ["Niveau", "Matig", "Gemiddeld", "Goed", "Uitstekend"]
    nrm_clrs = [navy, colors.HexColor("#F97316"), colors.HexColor("#EAB308"),
                colors.HexColor("#22C55E"), colors.HexColor("#10B981")]
    c.setFont("Helvetica-Bold", 10)
    for cx, hdr, cl in zip(nrm_cols, nrm_hdrs, nrm_clrs):
        c.setFillColor(cl); c.drawString(cx, y, hdr)
    y -= 9; c.setStrokeColor(blue); c.line(45, y, W-45, y); y -= RN

    c.setFont("Helvetica", 10)
    for ni, rij in enumerate(normen):
        if ni % 2 == 0:
            c.setFillColor(grey_bg); c.rect(45, y-6, W-90, RN, fill=1, stroke=0)
        for cx, val in zip(nrm_cols, rij):
            c.setFillColor(navy); c.drawString(cx, y+6, val)
        y -= RN

    # Gemeten waarde markering
    y -= 14
    c.setFillColor(colors.HexColor("#EFF6FF"))
    c.roundRect(45, y - 30, W-90, 30, 5, fill=1, stroke=0)
    c.setFillColor(blue); c.setFont("Helvetica-Bold", 10)
    c.drawString(58, y - 19, f"Gemeten VO2max: {vo2_gem} ml/kg/min  |  {naam}  |  {leeft} jaar  |  {gesl}")

    footer()

    # ════════════════════════════════════════════
    #  PAGINA 4  –  Opmerkingen & Advies Coach
    # ════════════════════════════════════════════
    c.showPage()
    draw_header("INSPANNINGSTEST", "Opmerkingen & Advies Coach", 4, 4)
    y = H - 130

    y = section("OPMERKINGEN & ADVIES COACH", y)
    y -= 20

    tekst = opmerkingen.strip() if opmerkingen and opmerkingen.strip() else "Geen extra opmerkingen geformuleerd."

    # Groot tekstvak voor opmerkingen
    tekstvak_h = 340
    c.setFillColor(colors.HexColor("#F8FAFC"))
    c.roundRect(45, y - tekstvak_h, W - 90, tekstvak_h, 7, fill=1, stroke=0)
    c.setFillColor(grey_ln)
    c.roundRect(45, y - tekstvak_h, W - 90, tekstvak_h, 7, fill=0, stroke=1)

    tekst_y = y - 18
    c.setFont("Helvetica", 11); c.setFillColor(navy)
    for line in tekst.split('\n'):
        words = line if line.strip() else " "
        while len(words) > 80:
            c.drawString(60, tekst_y, words[:80])
            tekst_y -= 20; words = words[80:]
        c.drawString(60, tekst_y, words)
        tekst_y -= 20
        if tekst_y < y - tekstvak_h + 15:
            break

    y = y - tekstvak_h - 40

    # Handtekeningen
    c.setStrokeColor(grey_ln); c.setLineWidth(0.8)
    c.line(55, y, 245, y); c.line(320, y, 515, y)
    c.setFillColor(colors.HexColor("#94A3B8")); c.setFont("Helvetica", 9)
    c.drawString(55, y - 16, "Handtekening coach")
    c.drawString(320, y - 16, "Handtekening atleet")

    footer()
    c.save()
    buffer.seek(0)
    return buffer


def genereer_vergelijking_pdf(naam, fig, rows, opmerkingen=""):
    if not REPORTLAB_OK:
        return None
    buffer = BytesIO()
    c = rl_canvas.Canvas(buffer, pagesize=A4)
    W, H = A4
    navy    = colors.HexColor("#0F172A"); blue = colors.HexColor("#1E88E5")
    grey_bg = colors.HexColor("#F8FAFC"); grey_ln = colors.HexColor("#CBD5E1")
    light   = colors.HexColor("#EFF6FF")

    # Header
    c.setFillColor(navy); c.rect(0, H-100, W, 100, fill=1, stroke=0)
    c.setFillColor(blue); c.rect(0, H-103, W, 3, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 22)
    c.drawString(45, H-50, "VERGELIJKINGSRAPPORT")
    c.setFont("Helvetica", 10); c.setFillColor(colors.HexColor("#93C5FD"))
    c.drawString(45, H-68, f"Atleet: {naam}  |  {date.today().strftime('%d %B %Y')}  |  LacTan+")

    # Grafiek
    img_buf = BytesIO()
    fig.savefig(img_buf, format='png', dpi=200, bbox_inches='tight'); img_buf.seek(0)
    c.drawImage(ImageReader(img_buf), 45, 400, width=W-90, height=260)

    # Drempelanalyse tabel
    y = 378
    c.setFillColor(blue); c.rect(45, y, W-90, 22, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#93C5FD")); c.rect(45, y, 5, 22, fill=1, stroke=0)
    c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 10)
    c.drawString(58, y+6, "DREMPELANALYSE OVERZICHT")
    y -= 14

    hdrs = ["Atleet", "Datum", "LT1 (W)", "LT2 (W)", "Max Lac"]
    cols = [55, 180, 305, 385, 462]
    c.setFont("Helvetica-Bold", 9); c.setFillColor(navy)
    for cx, hdr in zip(cols, hdrs): c.drawString(cx, y, hdr)
    y -= 6; c.setStrokeColor(blue); c.line(45, y, W-45, y); y -= 16

    c.setFont("Helvetica", 9.5)
    for ri, r in enumerate(rows):
        if ri % 2 == 0:
            c.setFillColor(grey_bg); c.rect(45, y-4, W-90, 16, fill=1, stroke=0)
        c.setFillColor(colors.black)
        for cx, val in zip(cols, [r['Atleet'], r['Datum'],
                                   f"{r['LT1 (W)']} W", f"{r['LT2 (W)']} W", r['Max Lac']]):
            c.drawString(cx, y+2, str(val))
        y -= 18

    # Opmerkingen sectie
    y -= 10
    if y > 80:
        c.setFillColor(blue); c.rect(45, y, W-90, 22, fill=1, stroke=0)
        c.setFillColor(colors.HexColor("#93C5FD")); c.rect(45, y, 5, 22, fill=1, stroke=0)
        c.setFillColor(colors.white); c.setFont("Helvetica-Bold", 10)
        c.drawString(58, y+6, "OPMERKINGEN & ADVIES COACH")
        y -= 16

        tekst = opmerkingen.strip() if opmerkingen and opmerkingen.strip() else "Geen opmerkingen."
        vak_h = max(60, min(y - 40, 160))
        c.setFillColor(light); c.roundRect(45, y - vak_h, W-90, vak_h, 5, fill=1, stroke=0)
        c.setFillColor(grey_ln); c.roundRect(45, y - vak_h, W-90, vak_h, 5, fill=0, stroke=1)

        ty = y - 14
        c.setFont("Helvetica", 10); c.setFillColor(navy)
        for line in tekst.split('\n'):
            while len(line) > 85:
                c.drawString(58, ty, line[:85]); ty -= 16; line = line[85:]
            c.drawString(58, ty, line); ty -= 16
            if ty < y - vak_h + 8:
                break

    # Footer
    c.setFillColor(grey_ln); c.rect(0, 0, W, 25, fill=1, stroke=0)
    c.setFillColor(colors.HexColor("#64748B")); c.setFont("Helvetica", 7.5)
    c.drawString(45, 8, f"LacTan+ Vergelijkingsrapport  |  {date.today().strftime('%d-%m-%Y')}  |  Vertrouwelijk")
    c.drawRightString(W-45, 8, f"© {date.today().year} LacTan+")
    c.save(); buffer.seek(0)
    return buffer


# ─────────────────────────────────────────────
#  CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
.block-container{padding-top:1rem;}
.biometry-box{background:linear-gradient(135deg,#EFF6FF,#DBEAFE);padding:14px 20px;
    border-radius:10px;border-left:5px solid #1E88E5;margin-bottom:16px;font-size:14px;}
.zone-card{padding:8px 14px;margin-bottom:4px;border-radius:7px;font-size:13.5px;
    border-left:5px solid #0F172A;font-weight:500;}
.energie-box{background:#F0FDF4;padding:14px 18px;border-radius:10px;
    border-left:5px solid #16A34A;margin-top:12px;font-size:13.5px;}
h1{color:#0F172A !important;}
</style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("# 🚴 LacTan+")
    if st.button("Uitloggen", use_container_width=True):
        # Bewaar database bij uitloggen — NIET wissen
        st.session_state.logged_in = False
        st.rerun()
    st.divider()
    st.subheader("Labo instellingen")
    labo_naam = st.text_input("Naam sportlab / organisatie", value="Sportlab Achterbos",
                               help="Deze naam verschijnt in de header en voetnoot van het PDF rapport")
    st.divider()
    st.subheader("Analyse instellingen")
    pal   = st.select_slider("PAL factor", [1.2, 1.4, 1.6, 1.8, 2.0], value=1.4)
    m_lt1 = st.radio("LT1 methode", ["Baseline + 1.0", "Handmatig"])
    m_lt2 = st.radio("LT2 methode", ["Modified Dmax", "Handmatig"])
    st.divider()

    st.subheader("Trainingszones")
    if "zones" not in st.session_state:
        st.session_state.zones = [
            {"Zone":"Z1","Naam":"Herstel",  "W_van":0,  "W_tot":55, "HR_van":0,  "HR_tot":65, "Borg":"6-9",   "color":"#E8F5E9"},
            {"Zone":"Z2","Naam":"Duur",     "W_van":56, "W_tot":75, "HR_van":66, "HR_tot":80, "Borg":"10-12", "color":"#C8E6C9"},
            {"Zone":"Z3","Naam":"Tempo",    "W_van":76, "W_tot":90, "HR_van":81, "HR_tot":87, "Borg":"13-14", "color":"#FFF9C4"},
            {"Zone":"Z4","Naam":"Drempel",  "W_van":91, "W_tot":105,"HR_van":88, "HR_tot":94, "Borg":"15-16", "color":"#FFE0B2"},
            {"Zone":"Z5","Naam":"VO2max",   "W_van":106,"W_tot":150,"HR_van":95, "HR_tot":100,"Borg":"17-20", "color":"#FFCDD2"},
        ]

    to_delete = []
    for idx, z in enumerate(st.session_state.zones):
        with st.expander(f"{z['Zone']} – {z['Naam']}", expanded=False):
            z["Zone"]  = st.text_input("Code",    z["Zone"],  key=f"zc_{idx}")
            z["Naam"]  = st.text_input("Naam",    z["Naam"],  key=f"zn_{idx}")
            z["color"] = st.color_picker("Kleur", z["color"], key=f"zk_{idx}")
            c1s, c2s   = st.columns(2)
            z["W_van"]  = c1s.number_input("W% van",  0,300,int(z["W_van"]),  key=f"wv_{idx}")
            z["W_tot"]  = c2s.number_input("W% tot",  0,300,int(z["W_tot"]),  key=f"wt_{idx}")
            z["HR_van"] = c1s.number_input("HR% van", 0,100,int(z["HR_van"]), key=f"hv_{idx}")
            z["HR_tot"] = c2s.number_input("HR% tot", 0,100,int(z["HR_tot"]), key=f"ht_{idx}")
            z["Borg"]   = st.text_input("Borg",    z["Borg"],  key=f"bg_{idx}")
            if st.button("Verwijder zone", key=f"del_{idx}"):
                to_delete.append(idx)

    for i in sorted(to_delete, reverse=True):
        st.session_state.zones.pop(i)
    if to_delete:
        st.rerun()

    st.divider()
    with st.expander("Nieuwe zone toevoegen"):
        nz_code  = st.text_input("Code",    "Z6",      key="nz_c")
        nz_naam  = st.text_input("Naam",    "Sprint",  key="nz_n")
        nz_color = st.color_picker("Kleur", "#F8BBD9", key="nz_k")
        c1n, c2n = st.columns(2)
        nz_wv    = c1n.number_input("W% van",  0,300,151, key="nz_wv")
        nz_wt    = c2n.number_input("W% tot",  0,300,200, key="nz_wt")
        nz_hv    = c1n.number_input("HR% van", 0,100,95,  key="nz_hv")
        nz_ht    = c2n.number_input("HR% tot", 0,100,100, key="nz_ht")
        nz_borg  = st.text_input("Borg",    "19-20",   key="nz_b")
        if st.button("Zone toevoegen", key="nz_add"):
            st.session_state.zones.append({
                "Zone":nz_code,"Naam":nz_naam,"color":nz_color,
                "W_van":nz_wv,"W_tot":nz_wt,"HR_van":nz_hv,"HR_tot":nz_ht,"Borg":nz_borg
            })
            st.rerun()

# ─────────────────────────────────────────────
#  HOOFDPAGINA  –  INVOER
# ─────────────────────────────────────────────
st.title("Inspanningstest")
st.markdown("---")

# Rij 1: persoonlijke gegevens
st.markdown("#### Persoonlijke gegevens")
c1, c2, c3, c4 = st.columns(4)
with c1:
    n_atl  = st.text_input("Naam atleet", "Voornaam Achternaam")
    gebdat = st.date_input("Geboortedatum", value=date(1990, 1, 1),
                           min_value=date(1930,1,1), max_value=date.today())
with c2:
    gew    = st.number_input("Gewicht (kg)", 30.0, 150.0, 75.0)
    leng   = st.number_input("Lengte (cm)", 120, 220, 180)
with c3:
    gesl   = st.selectbox("Geslacht", ["Man", "Vrouw"])
    sport  = st.text_input("Sport / Discipline", "Wielrennen")
with c4:
    test_d = st.date_input("Testdatum", date.today())
    logo_f = st.file_uploader("Logo (optioneel)", type=["png","jpg","jpeg"])

doelen = st.text_input("Trainingsdoelen", placeholder="bijv. Sportief, Gewichtsreductie, Competitie...")

st.markdown("#### Testgegevens invoer")

# Sport type detectie
is_lopen = any(s in sport.lower() for s in ["loop", "run", "atletiek", "triatlon", "triathlon"])
sport_type = st.radio("Testtype", ["🚴 Fietsen (Watt)", "🏃 Lopen (km/u)"],
                       index=1 if is_lopen else 0, horizontal=True)
is_lopen = "Lopen" in sport_type

if is_lopen:
    df_in = st.data_editor(
        pd.DataFrame({
            "km/u": [8.0, 10.0, 12.0, 14.0, 16.0, 18.0],
            "HR":   [110., 125., 140., 155., 170., 185.],
            "Lac":  [1.0,  1.2,  2.2,  4.5,  9.5, 12.0],
            "Borg": [8.,   10.,  12.,  14.,  16.,  18.]
        }),
        num_rows="dynamic",
        use_container_width=True,
        key="data_editor"
    )
    c_df = df_in.dropna(subset=["km/u", "HR", "Lac"]).copy()
    c_df["Watt"] = c_df["km/u"]  # intern gebruiken we Watt kolom als x-as
else:
    df_in = st.data_editor(
        pd.DataFrame({
            "Watt": [100., 150., 200., 250., 300., 350.],
            "HR":   [110., 125., 140., 155., 170., 185.],
            "Lac":  [1.0,  1.2,  2.2,  4.5,  9.5, 12.0],
            "Borg": [8.,   10.,  12.,  14.,  16.,  18.]
        }),
        num_rows="dynamic",
        use_container_width=True,
        key="data_editor"
    )
    c_df = df_in.dropna(subset=["Watt", "HR", "Lac"]).copy()

if len(c_df) < 3:
    st.info("Voer minimaal 3 meetpunten in om de analyse te starten.")
    st.stop()

x_v   = c_df["Watt"].values.astype(float)
hr_v  = c_df["HR"].values.astype(float)
lac_v = c_df["Lac"].values.astype(float)

# Eenheid labels
x_eenheid  = "km/u" if is_lopen else "W"
x_label    = "Snelheid (km/u)" if is_lopen else "Vermogen (Watt)"
x_kort     = "km/u" if is_lopen else "W"

def tempo_str(kmh):
    """Zet km/u om naar min/km tempo string"""
    if kmh <= 0: return "-"
    sec = 3600 / kmh
    return f"{int(sec//60)}:{int(sec%60):02d} min/km"

max_vals = {
    "Watt": int(x_v.max()),
    "HR":   int(hr_v.max()),
    "Lac":  float(lac_v.max())
}

# Leeftijd uit geboortedatum
leeft = bereken_leeftijd(gebdat)

# Handmatige LT schuivers
lt1_hand = lt2_hand = None
if m_lt1 == "Handmatig":
    lt1_hand = st.sidebar.slider(f"LT1 ({x_kort})", float(x_v.min()), float(x_v.max()), float(x_v.mean()))
if m_lt2 == "Handmatig":
    lt2_hand = st.sidebar.slider(f"LT2 ({x_kort})", float(x_v.min()), float(x_v.max()), float(x_v.mean()))

lt1_w, lt2_w, xf, yf = bereken_drempels(x_v, lac_v, m_lt1, m_lt2, lt1_hand, lt2_hand)
lt1_hr = interp_val(lt1_w, x_v, hr_v)
lt2_hr = interp_val(lt2_w, x_v, hr_v)

# Biometrie & energie
bmi  = gew / ((leng / 100) ** 2)
bmr  = (10*gew) + (6.25*leng) - (5*leeft) + (5 if gesl == "Man" else -161)
tdee = bmr * pal
vo2_gem, vo2_storer, vo2_lb = bereken_vo2max(x_v.max(), gew, hr_v.max())
if is_lopen:
    vo2_gem, vo2_storer, vo2_lb = bereken_vo2max_lopen(x_v.max(), hr_v.max())

# Resultatenbox
if is_lopen:
    st.markdown(
        f'<div class="biometry-box">'
        f'<b>LT1:</b> {lt1_w:.1f} km/u ({tempo_str(lt1_w)}) @ {int(lt1_hr)} bpm &nbsp;&nbsp;|&nbsp;&nbsp; '
        f'<b>LT2:</b> {lt2_w:.1f} km/u ({tempo_str(lt2_w)}) @ {int(lt2_hr)} bpm &nbsp;&nbsp;|&nbsp;&nbsp; '
        f'<b>Max:</b> {x_v.max():.1f} km/u &middot; {max_vals["HR"]} bpm &middot; {max_vals["Lac"]:.1f} mmol/L'
        f'<br><b>VO₂max:</b> {vo2_gem} ml/kg/min &nbsp;(Storer: {vo2_storer} | Legge: {vo2_lb})'
        f'&nbsp;&nbsp;|&nbsp;&nbsp; <b>BMI:</b> {bmi:.1f} &nbsp;&nbsp;|&nbsp;&nbsp; <b>TDEE:</b> {int(tdee)} kcal/dag'
        f'</div>', unsafe_allow_html=True
    )
else:
    st.markdown(
        f'<div class="biometry-box">'
        f'<b>LT1:</b> {int(lt1_w)} W @ {int(lt1_hr)} bpm &nbsp;&nbsp;|&nbsp;&nbsp; '
        f'<b>LT2:</b> {int(lt2_w)} W @ {int(lt2_hr)} bpm &nbsp;&nbsp;|&nbsp;&nbsp; '
        f'<b>Max:</b> {max_vals["Watt"]} W &middot; {max_vals["HR"]} bpm &middot; {max_vals["Lac"]:.1f} mmol/L'
        f'<br><b>VO₂max:</b> {vo2_gem} ml/kg/min &nbsp;(Storer: {vo2_storer} | Legge: {vo2_lb})'
        f'&nbsp;&nbsp;|&nbsp;&nbsp; <b>BMI:</b> {bmi:.1f} &nbsp;&nbsp;|&nbsp;&nbsp; <b>TDEE:</b> {int(tdee)} kcal/dag'
        f'</div>', unsafe_allow_html=True
    )

# Energieoverzicht
st.markdown(
    f'<div class="energie-box">'
    f'<b>Energiebehoefte:</b> &nbsp; BMR: <b>{int(bmr)} kcal</b> &nbsp;|&nbsp; '
    f'TDEE (PAL {pal}): <b>{int(tdee)} kcal</b> &nbsp;|&nbsp; '
    f'Z1-Z2 (lage intensiteit): <b>{int(tdee*0.60)} kcal</b> &nbsp;|&nbsp; '
    f'Z3-Z4 (hoge intensiteit): <b>{int(tdee*0.28)} kcal</b> &nbsp;|&nbsp; '
    f'Z5 (max): <b>{int(tdee*0.12)} kcal</b>'
    f'</div>', unsafe_allow_html=True
)

# ─────────────────────────────────────────────
#  GRAFIEK
# ─────────────────────────────────────────────
fig, ax1 = plt.subplots(figsize=(11, 5))
ax2 = ax1.twinx()

for z in st.session_state.zones:
    ax1.axvspan(lt2_w * z["W_van"] / 100, lt2_w * z["W_tot"] / 100,
                color=z["color"], alpha=0.5)

ax1.plot(xf, yf, color='#1E88E5', linewidth=3)
ax1.scatter(x_v, lac_v, color='#0D47A1', s=70, zorder=5)
ax2.plot(x_v, hr_v, color='#e53935', linestyle='--', linewidth=2)
ax2.scatter(x_v, hr_v, color='#e53935', marker='x', s=50)

ax1.axvline(lt1_w, color='#2e7d32', linestyle='--', linewidth=1.5)
ax1.text(lt1_w+2, yf.max()*0.35, 'LT1', color='#2e7d32', fontweight='bold',
         bbox=dict(facecolor='white', alpha=0.85, edgecolor='#2e7d32', boxstyle='round,pad=0.3'))
ax1.axvline(lt2_w, color='#c62828', linestyle='--', linewidth=1.5)
ax1.text(lt2_w+2, yf.max()*0.35, 'LT2', color='#c62828', fontweight='bold',
         bbox=dict(facecolor='white', alpha=0.85, edgecolor='#c62828', boxstyle='round,pad=0.3'))

patches = [mpatches.Patch(color=z["color"], label=f"{z['Zone']} – {z['Naam']}")
           for z in st.session_state.zones]
ax1.legend(handles=patches, loc='upper left', fontsize=8, framealpha=0.9)
ax1.set_xlabel(x_label, fontsize=11)
ax1.set_ylabel("Lactaat (mmol/L)", color='#1E88E5', fontsize=11)
ax2.set_ylabel("Hartslag (bpm)", color='#e53935', fontsize=11)
ax1.set_xlim(x_v.min(), x_v.max())
ax1.set_title("Lactaat & Hartslagcurve – LacTan+", fontsize=13, fontweight='bold', color='#0F172A')
ax1.grid(True, alpha=0.2)
fig.tight_layout()
st.pyplot(fig)

# ─────────────────────────────────────────────
#  TRAININGSZONES
# ─────────────────────────────────────────────
st.markdown("#### Trainingszones")
z_tab = []
for z in st.session_state.zones:
    w_van = lt2_w * z["W_van"] / 100
    w_tot = lt2_w * z["W_tot"] / 100
    h_van = int(hr_v.max() * z["HR_van"] / 100)
    h_tot = int(hr_v.max() * z["HR_tot"] / 100)

    if is_lopen:
        zone_label = f"⚡ {w_van:.1f}–{w_tot:.1f} km/u ({tempo_str(w_van)}–{tempo_str(w_tot)})"
        z_tab.append({
            "Zone": z["Zone"], "Naam": z["Naam"],
            "Snelheid": f"{w_van:.1f}–{w_tot:.1f} km/u",
            "Tempo": f"{tempo_str(w_van)}–{tempo_str(w_tot)}",
            "Hartslag": f"{h_van}–{h_tot} bpm",
            "Borg": z["Borg"], "color": z["color"]
        })
    else:
        zone_label = f"⚡ {int(w_van)}–{int(w_tot)} W"
        z_tab.append({
            "Zone": z["Zone"], "Naam": z["Naam"],
            "Watt": f"{int(w_van)}–{int(w_tot)} W",
            "Hartslag": f"{h_van}–{h_tot} bpm",
            "Borg": z["Borg"], "color": z["color"]
        })
    st.markdown(
        f'<div class="zone-card" style="background:{z["color"]};">'
        f'<b>{z["Zone"]} – {z["Naam"]}</b> &nbsp;&nbsp;'
        f'{zone_label} &nbsp;&nbsp;'
        f'❤️ {h_van}–{h_tot} bpm &nbsp;&nbsp;'
        f'Borg: {z["Borg"]}'
        f'</div>', unsafe_allow_html=True
    )

# ─────────────────────────────────────────────
#  OPMERKINGEN + PDF
# ─────────────────────────────────────────────
st.markdown("#### Opmerkingen coach")
opmerkingen = st.text_area("Observaties, aanbevelingen, omstandigheden:",
                            placeholder="Typ hier de observaties van de coach...", height=100)

st.markdown("#### Rapport genereren")
if not REPORTLAB_OK:
    st.warning("ReportLab niet geïnstalleerd. Voer uit: `pip install reportlab`")
else:
    if st.button("Genereer professioneel PDF-rapport", type="primary", use_container_width=True):
        with st.spinner("PDF wordt aangemaakt..."):
            pdf = genereer_pdf(
                naam=n_atl, geboortedatum=gebdat, sport=sport, doelen=doelen,
                datum=test_d, gew=gew, leng=leng, leeft=leeft, gesl=gesl,
                bmi=bmi, vo2_gem=vo2_gem, vo2_storer=vo2_storer, vo2_lb=vo2_lb,
                tdee=tdee, bmr=bmr,
                lt1_w=lt1_w, lt2_w=lt2_w, max_vals=max_vals,
                fig=fig, zones_lijst=st.session_state.zones,
                test_df=c_df, logo_file=logo_f, opmerkingen=opmerkingen,
                labo_naam=labo_naam, is_lopen=is_lopen
            )
        if pdf:
            st.download_button(
                "Download PDF Rapport",
                data=pdf,
                file_name=f"Inspanningstest_{n_atl}_{test_d}.pdf",
                mime="application/pdf",
                type="primary",
                use_container_width=True
            )

# ─────────────────────────────────────────────
#  VERGELIJKING & DATABASE
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<div style="display:flex;align-items:center;gap:12px;margin-bottom:4px;">
  <div style="width:5px;height:32px;background:linear-gradient(180deg,#1E88E5,#1565C0);border-radius:3px;"></div>
  <div>
    <div style="font-size:22px;font-weight:800;color:#0F172A;letter-spacing:-0.3px;">Vergelijken Lactaatanalyses</div>
    <div style="font-size:13px;color:#64748B;margin-top:1px;">Sla metingen op en vergelijk prestaties over meerdere testen</div>
  </div>
</div>
""", unsafe_allow_html=True)

st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)

# ── Opslaan + Supabase status in één balk ──
col_save, col_status = st.columns([2, 3])
with col_save:
    st.markdown("""<div style="font-size:13px;font-weight:600;color:#374151;margin-bottom:6px;">
        Huidige meting opslaan</div>""", unsafe_allow_html=True)
    if st.button("💾 Sla huidige meting op", use_container_width=True, type="primary"):
        try:
            save_test(n_atl, test_d,
                      c_df['Watt'].tolist(),
                      c_df['Lac'].tolist(),
                      c_df['HR'].tolist())
            st.success("✅ Meting opgeslagen!")
            st.rerun()
        except Exception as e:
            st.error(f"❌ Opslaan mislukt: {e}")

with col_status:
    with st.expander("🔌 Supabase connectie status", expanded=False):
        if not SUPABASE_OK:
            st.error("❌ supabase library niet geïnstalleerd")
        else:
            sb_test = get_supabase()
            if sb_test is None:
                st.error("❌ Secrets niet gevonden — controleer SUPABASE_URL en SUPABASE_KEY")
            else:
                try:
                    sb_test.table("tests").select("id").limit(1).execute()
                    st.success(f"✅ Verbonden als **{st.session_state.get('username', '?')}**")
                except Exception as e:
                    st.error(f"❌ Verbinding mislukt: {e}")

st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

db_data = load_tests()

if db_data.empty:
    st.markdown("""
    <div style="background:#F1F5F9;border-radius:12px;padding:24px 28px;
         border:1px solid #E2E8F0;text-align:center;color:#64748B;font-size:14px;">
        📂 &nbsp;Nog geen metingen opgeslagen. Sla een meting op via de knop hierboven.
    </div>
    """, unsafe_allow_html=True)
else:
    # ── Metingen overzicht + beheer ──
    st.markdown("""<div style="font-size:14px;font-weight:700;color:#0F172A;margin-bottom:8px;">
        📁 Opgeslagen metingen</div>""", unsafe_allow_html=True)

    with st.expander(f"🗂️ Beheer metingen  ({len(db_data)} opgeslagen)", expanded=False):
        st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
        for _, row in db_data.iterrows():
            col_a, col_b, col_c = st.columns([3, 2, 1])
            col_a.markdown(f"**{row['naam']}**")
            col_b.markdown(f"<span style='color:#64748B;font-size:13px;'>{row['datum']}</span>", unsafe_allow_html=True)
            if col_c.button("🗑️", key=f"rm_{row['id']}", help="Verwijder deze meting"):
                delete_test(row['id'])
                st.success(f"Meting van {row['naam']} ({row['datum']}) verwijderd.")
                st.rerun()

    # ── Selectie voor vergelijking ──
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown("""<div style="font-size:14px;font-weight:700;color:#0F172A;margin-bottom:6px;">
        📊 Selecteer testen voor vergelijking</div>""", unsafe_allow_html=True)

    opties = {i: f"{row['naam']}  —  {row['datum']}" for i, row in db_data.iterrows()}
    keuze  = st.multiselect("Testen",
                             list(opties.keys()),
                             format_func=lambda x: opties[x],
                             label_visibility="collapsed")

    if keuze:
        # ── Vergelijkingsgrafiek ──
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)

        KLEUREN = ['#1E88E5','#E53935','#43A047','#FB8C00','#8E24AA','#00ACC1','#F4511E']
        fig_v, ax_v = plt.subplots(figsize=(11, 5))
        fig_v.patch.set_facecolor('#F8FAFC')
        ax_v.set_facecolor('#F8FAFC')
        tabel_rows = []

        for idx, i in enumerate(keuze):
            r  = db_data.iloc[i]
            kleur = KLEUREN[idx % len(KLEUREN)]
            xw = np.array([float(v) for v in r['watt'].split(',')])
            yl = np.array([float(v) for v in r['lac'].split(',')])
            xfine = np.linspace(xw.min(), xw.max(), 500)
            yfine = PchipInterpolator(xw, yl)(xfine)

            i1    = np.where(yfine >= (float(np.mean(yl[:2])) + 1.0))[0]
            lt1_v = float(xfine[i1[0]]) if len(i1) > 0 else float(xw[0])
            i2    = np.where(yfine >= (float(np.mean(yl[:2])) + 0.4))[0]
            s_b   = i2[0] if len(i2) > 0 else 0
            dist  = np.abs(
                (yfine[-1]-yfine[s_b])*xfine[s_b:] -
                (xfine[-1]-xfine[s_b])*yfine[s_b:] +
                xfine[-1]*yfine[s_b] - yfine[-1]*xfine[s_b]
            )
            lt2_v = float(xfine[s_b + np.argmax(dist)])

            ax_v.plot(xfine, yfine, color=kleur,
                      label=f"{r['naam']}  ({r['datum']})", linewidth=2.5)
            ax_v.scatter([lt1_v], [interp_val(lt1_v, xw, yl)],
                         color=kleur, edgecolors='white', s=90, zorder=5,
                         marker='o', linewidths=1.5)
            ax_v.scatter([lt2_v], [interp_val(lt2_v, xw, yl)],
                         color=kleur, edgecolors='white', s=90, zorder=5,
                         marker='D', linewidths=1.5)
            ax_v.scatter(xw, yl, color=kleur, s=35, alpha=0.5, zorder=4)

            tabel_rows.append({
                "Atleet":   r['naam'],
                "Datum":    r['datum'],
                "LT1":      f"{lt1_v:.0f}",
                "LT2":      f"{lt2_v:.0f}",
                "Max Lac":  f"{yl.max():.1f} mmol/L",
                "Max":      f"{xw.max():.0f}",
            })

        ax_v.set_title("Vergelijkende Lactaatcurve – LacTan+", fontsize=13,
                       fontweight='bold', color='#0F172A', pad=14)
        ax_v.set_xlabel(x_label, fontsize=11, color='#374151')
        ax_v.set_ylabel("Lactaat (mmol/L)", fontsize=11, color='#1E88E5')
        ax_v.legend(fontsize=9, framealpha=0.95, edgecolor='#E2E8F0')
        ax_v.grid(True, alpha=0.25, linestyle='--')
        ax_v.spines['top'].set_visible(False)
        ax_v.spines['right'].set_visible(False)
        fig_v.tight_layout()
        st.pyplot(fig_v)

        # ── Vergelijkingstabel ──
        st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
        st.markdown("""<div style="font-size:14px;font-weight:700;color:#0F172A;margin-bottom:8px;">
            📋 Resultaten per test</div>""", unsafe_allow_html=True)

        eenheid = "km/u" if is_lopen else "W"
        df_verg = pd.DataFrame(tabel_rows).rename(columns={
            "LT1": f"LT1 ({eenheid})",
            "LT2": f"LT2 ({eenheid})",
            "Max": f"Max ({eenheid})",
        })

        # Stijl de tabel
        st.markdown("""
        <style>
        .verg-table { width:100%; border-collapse:collapse; font-size:14px; }
        .verg-table th { background:#0F172A; color:white; padding:10px 14px;
                         text-align:left; font-weight:600; font-size:13px; }
        .verg-table td { padding:9px 14px; border-bottom:1px solid #E2E8F0; color:#1E293B; }
        .verg-table tr:nth-child(even) td { background:#F8FAFC; }
        .verg-table tr:hover td { background:#EFF6FF; }
        </style>
        """, unsafe_allow_html=True)

        tabel_html = '<table class="verg-table"><thead><tr>'
        for col in df_verg.columns:
            tabel_html += f'<th>{col}</th>'
        tabel_html += '</tr></thead><tbody>'
        for _, rij in df_verg.iterrows():
            tabel_html += '<tr>'
            for val in rij:
                tabel_html += f'<td>{val}</td>'
            tabel_html += '</tr>'
        tabel_html += '</tbody></table>'
        st.markdown(tabel_html, unsafe_allow_html=True)

        # ── Opmerkingen coach ──
        st.markdown("<div style='height:20px'></div>", unsafe_allow_html=True)
        st.markdown("""
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">
          <div style="width:4px;height:22px;background:#1E88E5;border-radius:2px;"></div>
          <div style="font-size:14px;font-weight:700;color:#0F172A;">Opmerkingen coach</div>
        </div>
        """, unsafe_allow_html=True)
        opm_verg = st.text_area(
            "Observaties",
            placeholder="Beschrijf de evolutie, verbeteringen, aandachtspunten bij deze vergelijking...",
            height=130, key="opm_vergelijking", label_visibility="collapsed"
        )

        # ── PDF download ──
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if REPORTLAB_OK:
            pdf_verg = genereer_vergelijking_pdf(n_atl, fig_v, tabel_rows, opm_verg)
            if pdf_verg:
                st.download_button(
                    "📄  Download Vergelijking PDF",
                    data=pdf_verg,
                    file_name=f"LacTan_Vergelijking_{n_atl}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    type="primary"
                )
