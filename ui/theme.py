"""Visual system for CardioAI: palette, CSS, icons, animated components.

Brand: dark plum (#4A1942) to match the dissertation deck, with a rose accent
for risk emphasis. Supports dark and light modes. All motion respects
prefers-reduced-motion.
"""

import streamlit as st

# ---- palette -------------------------------------------------------------
PLUM = "#4A1942"
PLUM_LIGHT = "#6E2A5F"
ROSE = "#D64560"
ROSE_SOFT = "#E8849A"
GOLD = "#C48A18"
GREEN = "#22935E"

DARK = {
    "bg": "#14101A", "panel": "#1E1826", "panel2": "#271F31",
    "text": "#F4EEF6", "muted": "#B9AEC4", "border": "#3A2E48",
    "accent": ROSE, "plum": PLUM_LIGHT,
}
LIGHT = {
    "bg": "#F7F3F8", "panel": "#FFFFFF", "panel2": "#F1E9F2",
    "text": "#231E28", "muted": "#6E6478", "border": "#E4D8E7",
    "accent": ROSE, "plum": PLUM,
}


def palette():
    return DARK if st.session_state.get("dark_mode", True) else LIGHT


# ---- professional inline SVG icons (stroke, currentColor) ----------------
_ICONS = {
    "heart": '<path d="M12 21s-7.5-4.9-10-9.3C.4 8.6 2 5 5.5 5c2 0 3.3 1.1 4.5 2.6C11.2 6.1 12.5 5 14.5 5 18 5 19.6 8.6 22 11.7 19.5 16.1 12 21 12 21z"/>',
    "pulse": '<path d="M2 12h4l2-6 4 12 2-6h6"/>',
    "shield": '<path d="M12 2l8 3v6c0 5-3.5 8.5-8 11-4.5-2.5-8-6-8-11V5l8-3z"/>',
    "chart": '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    "user": '<circle cx="12" cy="8" r="4"/><path d="M4 21c0-4 3.6-6 8-6s8 2 8 6"/>',
    "stethoscope": '<path d="M4 3v6a5 5 0 0010 0V3M9 3H3M15 3h-6M14 14a4 4 0 108 0v-3"/><circle cx="18" cy="11" r="1"/>',
    "flask": '<path d="M9 3h6M10 3v6l-6 10a2 2 0 002 3h12a2 2 0 002-3l-6-10V3"/>',
    "gear": '<circle cx="12" cy="12" r="3"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3M5 5l2 2M17 17l2 2M19 5l-2 2M7 17l-2 2"/>',
    "clock": '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    "list": '<path d="M8 6h13M8 12h13M8 18h13M3 6h.01M3 12h.01M3 18h.01"/>',
    "download": '<path d="M12 3v12M7 10l5 5 5-5M4 21h16"/>',
    "book": '<path d="M4 5a2 2 0 012-2h13v16H6a2 2 0 00-2 2V5z"/><path d="M19 3v18"/>',
    "pill": '<rect x="3" y="8" width="18" height="8" rx="4" transform="rotate(45 12 12)"/><path d="M8.5 8.5l7 7"/>',
    "leaf": '<path d="M11 20A7 7 0 014 13c0-6 8-9 16-9 0 8-3 16-9 16z"/><path d="M4 20c4-4 6-6 9-8"/>',
    "alert": '<path d="M12 3l10 17H2L12 3z"/><path d="M12 10v4M12 17h.01"/>',
    "sparkle": '<path d="M12 3l1.8 5.2L19 10l-5.2 1.8L12 17l-1.8-5.2L5 10l5.2-1.8z"/>',
}


def icon(name, size=18, color=None):
    color = color or "currentColor"
    body = _ICONS.get(name, _ICONS["heart"])
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" '
            f'fill="none" stroke="{color}" stroke-width="1.9" '
            f'stroke-linecap="round" stroke-linejoin="round" '
            f'style="vertical-align:middle">{body}</svg>')


def inject_css():
    c = palette()
    st.markdown(f"""
<style>
:root {{
  --bg:{c['bg']}; --panel:{c['panel']}; --panel2:{c['panel2']};
  --text:{c['text']}; --muted:{c['muted']}; --border:{c['border']};
  --accent:{c['accent']}; --plum:{c['plum']}; --rose:{ROSE};
  --gold:{GOLD}; --green:{GREEN};
}}
html, body, [class*="css"] {{ font-family:'Inter',system-ui,sans-serif; }}
.stApp {{ background:
   radial-gradient(1200px 600px at 80% -10%, {c['plum']}22, transparent 60%),
   var(--bg); color:var(--text); }}
#MainMenu, footer {{ visibility:hidden; }}

/* --- brand header --- */
.cai-hero {{
  background:linear-gradient(135deg,{PLUM} 0%,{PLUM_LIGHT} 55%,{ROSE} 140%);
  border-radius:20px; padding:26px 30px; color:#fff; position:relative;
  overflow:hidden; box-shadow:0 18px 44px -20px {PLUM}cc;
  animation:cai-rise .6s ease both;
}}
.cai-hero::after {{
  content:""; position:absolute; right:-40px; top:-40px; width:220px;
  height:220px; border-radius:50%;
  background:radial-gradient(circle,#ffffff22,transparent 70%);
}}
.cai-hero h1 {{ margin:0; font-size:1.9rem; font-weight:800; letter-spacing:-.5px; }}
.cai-hero p {{ margin:.35rem 0 0; opacity:.9; font-size:1rem; }}
.cai-hero .tag {{
  display:inline-block; margin-top:12px; padding:4px 12px; font-size:.74rem;
  font-weight:700; letter-spacing:.6px; text-transform:uppercase;
  background:#ffffff26; border-radius:999px; }}

/* --- cards --- */
.cai-card {{
  background:var(--panel); border:1px solid var(--border); border-radius:16px;
  padding:20px 22px; box-shadow:0 10px 30px -22px #00000099;
  animation:cai-rise .5s ease both;
}}
.cai-card h3 {{ margin:.1rem 0 .6rem; font-size:1.05rem; color:var(--text);
  display:flex; align-items:center; gap:9px; }}
.cai-muted {{ color:var(--muted); font-size:.9rem; line-height:1.5; }}

/* --- metric tiles --- */
.cai-metrics {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(150px,1fr));
  gap:14px; margin:6px 0; }}
.cai-metric {{ background:var(--panel); border:1px solid var(--border);
  border-radius:14px; padding:16px 18px; animation:cai-rise .5s ease both; }}
.cai-metric .v {{ font-size:1.7rem; font-weight:800; color:var(--text);
  line-height:1; }}
.cai-metric .l {{ font-size:.78rem; color:var(--muted); margin-top:6px;
  text-transform:uppercase; letter-spacing:.5px; }}
.cai-metric .i {{ color:var(--accent); }}

/* --- risk gauge label --- */
.cai-band {{ display:inline-flex; align-items:center; gap:8px; font-weight:700;
  padding:7px 16px; border-radius:999px; font-size:.95rem; }}
.band-low {{ background:{GREEN}22; color:{GREEN}; border:1px solid {GREEN}66; }}
.band-elevated {{ background:{GOLD}22; color:{GOLD}; border:1px solid {GOLD}66; }}
.band-high {{ background:{ROSE}22; color:{ROSE}; border:1px solid {ROSE}66; }}

/* --- pills / chips --- */
.cai-chip {{ display:inline-block; padding:3px 10px; border-radius:999px;
  font-size:.74rem; font-weight:600; background:var(--panel2);
  border:1px solid var(--border); color:var(--muted); margin:2px; }}

/* --- rec / ref blocks --- */
.cai-rec {{ border-left:3px solid var(--accent); background:var(--panel2);
  padding:12px 16px; border-radius:0 12px 12px 0; margin:8px 0;
  animation:cai-slide .45s ease both; }}
.cai-rec b {{ color:var(--text); }}
.cai-ref {{ font-size:.78rem; color:var(--muted); margin-top:6px;
  font-style:italic; }}

/* --- buttons --- */
.stButton>button {{
  border-radius:12px; border:1px solid var(--border); font-weight:600;
  transition:transform .12s ease, box-shadow .2s ease; }}
.stButton>button:hover {{ transform:translateY(-1px);
  box-shadow:0 8px 20px -12px {ROSE}; border-color:{ROSE}; }}
div[data-testid="stFormSubmitButton"]>button, .cai-primary .stButton>button {{
  background:linear-gradient(135deg,{PLUM},{ROSE}); color:#fff; border:none; }}

/* --- loading dots --- */
.cai-loader {{ display:flex; gap:8px; align-items:center; color:var(--muted);
  padding:8px 0; }}
.cai-loader .d {{ width:10px; height:10px; border-radius:50%;
  background:var(--accent); animation:cai-bounce 1s infinite ease-in-out; }}
.cai-loader .d:nth-child(2) {{ animation-delay:.15s; }}
.cai-loader .d:nth-child(3) {{ animation-delay:.3s; }}
.cai-beat {{ display:inline-block; animation:cai-beat 1.1s infinite; color:{ROSE}; }}

/* --- tables --- */
[data-testid="stDataFrame"] {{ border-radius:12px; overflow:hidden;
  border:1px solid var(--border); }}

/* --- sidebar --- */
section[data-testid="stSidebar"] {{ background:var(--panel);
  border-right:1px solid var(--border); }}

/* --- keyframes --- */
@keyframes cai-rise {{ from{{opacity:0;transform:translateY(10px)}}
  to{{opacity:1;transform:none}} }}
@keyframes cai-slide {{ from{{opacity:0;transform:translateX(-8px)}}
  to{{opacity:1;transform:none}} }}
@keyframes cai-bounce {{ 0%,80%,100%{{transform:scale(.5);opacity:.5}}
  40%{{transform:scale(1);opacity:1}} }}
@keyframes cai-beat {{ 0%,100%{{transform:scale(1)}} 15%{{transform:scale(1.25)}}
  30%{{transform:scale(1)}} 45%{{transform:scale(1.18)}} }}

@media (prefers-reduced-motion: reduce) {{
  *, *::before, *::after {{ animation:none !important; transition:none !important; }}
}}
:focus-visible {{ outline:3px solid {ROSE_SOFT}; outline-offset:2px; }}
</style>
""", unsafe_allow_html=True)


# ---- component helpers ---------------------------------------------------
def hero(title, subtitle, tag):
    st.markdown(
        f'<div class="cai-hero"><h1>{icon("heart",26,"#fff")} {title}</h1>'
        f'<p>{subtitle}</p><span class="tag">{tag}</span></div>',
        unsafe_allow_html=True)
    st.write("")


def metric_row(items):
    """items: list of (icon_name, value, label)."""
    cells = "".join(
        f'<div class="cai-metric"><div class="i">{icon(i,20)}</div>'
        f'<div class="v">{v}</div><div class="l">{l}</div></div>'
        for i, v, l in items)
    st.markdown(f'<div class="cai-metrics">{cells}</div>', unsafe_allow_html=True)


def card_open(title, icon_name="heart"):
    st.markdown(f'<div class="cai-card"><h3>{icon(icon_name,20)} {title}</h3>',
                unsafe_allow_html=True)


def card_close():
    st.markdown("</div>", unsafe_allow_html=True)


def band_badge(band):
    cls = {"Low": "band-low", "Elevated": "band-elevated", "High": "band-high"}[band]
    ic = {"Low": "shield", "Elevated": "alert", "High": "alert"}[band]
    return f'<span class="cai-band {cls}">{icon(ic,16)} {band} risk</span>'


def loader(text="Running the model"):
    return st.markdown(
        f'<div class="cai-loader"><span class="d"></span><span class="d"></span>'
        f'<span class="d"></span> {text}...</div>', unsafe_allow_html=True)


def rec_block(title, body, ref=None):
    html = f'<div class="cai-rec"><b>{title}</b><div class="cai-muted">{body}</div>'
    if ref:
        html += f'<div class="cai-ref">Reference: {ref}</div>'
    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)
