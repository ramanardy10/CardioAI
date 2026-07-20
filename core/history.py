"""Prediction history and audit logging for CardioAI.

Stored in Streamlit session state - no database is required, which keeps the
app deployable on Streamlit Community Cloud and avoids persisting any health
data (a deliberate GDPR-minimising design for a research prototype).
"""

import datetime as _dt
import uuid

import pandas as pd
import streamlit as st

_HIST = "cardioai_history"
_AUDIT = "cardioai_audit"


def _init():
    st.session_state.setdefault(_HIST, [])
    st.session_state.setdefault(_AUDIT, [])


def _now():
    return _dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def log_audit(action: str, mode: str, detail: str = ""):
    _init()
    st.session_state[_AUDIT].append({
        "timestamp": _now(),
        "mode": mode,
        "action": action,
        "detail": detail,
    })


def add_prediction(mode: str, patient: dict, prob: float, band: str,
                   top_factors=None):
    _init()
    rec = {
        "id": str(uuid.uuid4())[:8],
        "timestamp": _now(),
        "mode": mode,
        "risk_probability": round(prob, 4),
        "risk_band": band,
        "top_factors": "; ".join(top_factors or []),
        "inputs": dict(patient),
    }
    st.session_state[_HIST].append(rec)
    log_audit("prediction", mode, f"{band} ({prob:.1%})")
    return rec


def history_df() -> pd.DataFrame:
    _init()
    rows = []
    for r in st.session_state[_HIST]:
        row = {k: v for k, v in r.items() if k != "inputs"}
        rows.append(row)
    return pd.DataFrame(rows)


def history_full():
    _init()
    return list(st.session_state[_HIST])


def audit_df() -> pd.DataFrame:
    _init()
    return pd.DataFrame(st.session_state[_AUDIT])


def clear_all():
    st.session_state[_HIST] = []
    log_audit("history_cleared", "Admin")
