"""CardioAI - explainable heart disease risk prediction.

MSc Applied AI research prototype. Streamlit Community Cloud ready.

Run locally:   streamlit run app.py
Entry point for deployment: app.py
"""

import streamlit as st

from core import config, history
from core.model import artifacts_present, missing_files
from ui import theme

st.set_page_config(
    page_title=f"{config.APP_NAME} - Heart Risk AI",
    page_icon="\u2764\ufe0f",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---- session defaults ----
st.session_state.setdefault("dark_mode", True)
st.session_state.setdefault("mode", "Patient")

theme.inject_css()

# ---- guard: artifacts present? ----
if not artifacts_present():
    theme.hero("CardioAI", "Model artifacts not found.", "Setup needed")
    st.error("Missing artifact files: " + ", ".join(missing_files()))
    st.markdown(
        "Place your trained files in the **artifacts/** folder:\n\n"
        "- `best_model.pkl`\n- `preprocessor_params.json`\n"
        "- `metadata.json` (optional)\n- `shap_feature_importance.csv` (optional)\n\n"
        "Or run `python build_demo_artifacts.py` to generate a demo set.")
    st.stop()

# ---------------------------------------------------------------------------
# Sidebar navigation
# ---------------------------------------------------------------------------
MODES = {
    "Patient": ("user", "Simple personal risk check"),
    "Clinical": ("stethoscope", "Full clinical decision support"),
    "Research": ("flask", "Batch scoring & simulation"),
    "Analytics": ("chart", "Population dashboard"),
    "History": ("list", "Prediction history"),
    "Guidelines": ("book", "ESC evidence base"),
    "Admin": ("gear", "Audit & governance"),
}

with st.sidebar:
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:10px;'
        f'padding:6px 2px 14px">{theme.icon("heart",30,theme.ROSE)}'
        f'<div><div style="font-weight:800;font-size:1.25rem;'
        f'color:var(--text)">{config.APP_NAME}</div>'
        f'<div class="cai-muted" style="font-size:.75rem">'
        f'v{config.VERSION} - research prototype</div></div></div>',
        unsafe_allow_html=True)

    st.markdown('<div class="cai-muted" style="font-size:.72rem;'
                'text-transform:uppercase;letter-spacing:.6px;margin:4px 0">'
                'Workspace</div>', unsafe_allow_html=True)

    for name, (ic, desc) in MODES.items():
        active = st.session_state["mode"] == name
        if st.button(f"{name}", key=f"nav_{name}",
                     use_container_width=True,
                     type="primary" if active else "secondary"):
            st.session_state["mode"] = name
            history.log_audit("navigate", name)
            st.rerun()

    st.divider()
    dark = st.toggle("Dark mode", value=st.session_state["dark_mode"])
    if dark != st.session_state["dark_mode"]:
        st.session_state["dark_mode"] = dark
        st.rerun()

    st.markdown(
        f'<div class="cai-muted" style="font-size:.72rem;margin-top:14px;'
        f'line-height:1.5">{config.DISCLAIMER}</div>', unsafe_allow_html=True)

# ---------------------------------------------------------------------------
# Route
# ---------------------------------------------------------------------------
from modes import assessment, dashboards  # noqa: E402  (after css/session setup)

mode = st.session_state["mode"]
if mode == "Patient":
    assessment.patient_mode()
elif mode == "Clinical":
    assessment.clinical_mode()
elif mode == "Research":
    assessment.research_mode()
elif mode == "Analytics":
    dashboards.analytics_dashboard()
elif mode == "History":
    dashboards.history_page()
elif mode == "Guidelines":
    dashboards.guidelines_library()
elif mode == "Admin":
    dashboards.admin_mode()

st.write("")
st.markdown(
    f'<div class="cai-muted" style="text-align:center;font-size:.75rem;'
    f'padding:18px 0 6px">{theme.icon("heart",13,theme.ROSE)} '
    f'{config.APP_NAME} v{config.VERSION} - {config.INSTITUTION} - '
    f'not for clinical use</div>', unsafe_allow_html=True)
