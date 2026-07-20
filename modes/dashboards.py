"""Dashboards & admin: analytics, history, audit logs, guideline library."""

import pandas as pd
import streamlit as st

from core import config, guidelines, history
from core.model import load_artifacts, model_metrics, tuned_threshold
from core.shap_engine import global_importance
from ui import charts, theme


def analytics_dashboard():
    theme.hero("Analytics dashboard",
               "Population-level view of every assessment run in this session.",
               "Analytics")
    hist = history.history_df()

    if hist.empty:
        _empty("No assessments yet",
               "Run a prediction in Patient, Clinical or Research mode and the "
               "analytics will populate here.")
        _global_importance_card()
        return

    _, _, metadata, _ = load_artifacts()
    tuned = tuned_threshold(metadata)
    probs = hist["risk_probability"].tolist()
    counts = hist["risk_band"].value_counts().to_dict()

    theme.metric_row([
        ("list", str(len(hist)), "Assessments"),
        ("alert", str(counts.get("High", 0)), "High risk"),
        ("chart", f"{sum(probs)/len(probs):.1%}", "Mean risk"),
        ("pulse", f"{max(probs):.1%}", "Peak risk"),
    ])
    st.write("")

    c1, c2 = st.columns([3, 2])
    with c1:
        theme.card_open("Risk distribution", "chart")
        st.plotly_chart(charts.distribution_hist(probs, tuned),
                        use_container_width=True, key="an_hist")
        theme.card_close()
    with c2:
        theme.card_open("Population statistics", "shield")
        st.plotly_chart(charts.band_donut(counts),
                        use_container_width=True, key="an_donut")
        theme.card_close()

    theme.card_open("Assessments by mode", "user")
    by_mode = hist.groupby("mode")["risk_probability"].agg(
        ["count", "mean", "max"]).round(3).reset_index()
    by_mode.columns = ["Mode", "Count", "Mean risk", "Max risk"]
    st.dataframe(by_mode, use_container_width=True, hide_index=True)
    theme.card_close()

    _global_importance_card()


def _global_importance_card():
    theme.card_open("Global feature importance", "sparkle")
    st.markdown('<div class="cai-muted">Which factors drive the model overall, '
                "aggregated from SHAP. Complements the per-patient explanations "
                "shown after each assessment.</div>", unsafe_allow_html=True)
    imp = global_importance()
    if not imp.empty:
        st.plotly_chart(charts.importance_bar(imp), use_container_width=True,
                        key="an_imp")
    theme.card_close()


def history_page():
    theme.hero("Prediction history",
               "Every assessment from this session, newest first.",
               "History")
    hist = history.history_df()
    if hist.empty:
        _empty("Nothing recorded yet",
               "Assessments you run will be listed here with their risk band "
               "and top contributing factors.")
        return

    view = hist.iloc[::-1].rename(columns={
        "timestamp": "Time", "mode": "Mode", "risk_probability": "Risk",
        "risk_band": "Band", "top_factors": "Top factors", "id": "ID"})
    view["Risk"] = (view["Risk"] * 100).round(1).astype(str) + "%"
    theme.card_open("Session assessments", "list")
    st.dataframe(view, use_container_width=True, hide_index=True)
    c1, c2 = st.columns(2)
    with c1:
        st.download_button("Export history (CSV)",
                           hist.to_csv(index=False).encode(),
                           "cardioai_history.csv", "text/csv",
                           use_container_width=True)
    with c2:
        if st.button("Clear history", use_container_width=True):
            history.clear_all()
            st.rerun()
    theme.card_close()


def guidelines_library():
    theme.hero("Evidence-based guidelines",
               "The European Society of Cardiology references that anchor "
               "CardioAI's recommendations.",
               "Guidelines")
    theme.card_open("Lifestyle recommendation rules", "leaf")
    st.markdown('<div class="cai-muted">Each rule fires from a modifiable risk '
                "factor in the model's inputs and cites its ESC source.</div>",
                unsafe_allow_html=True)
    for r in guidelines.LIFESTYLE_RULES:
        ref = next(x for x in guidelines.ESC_REFERENCES if x["id"] == r["ref"])
        theme.rec_block(r["title"], r["advice"], ref["citation"])
    theme.card_close()

    theme.card_open("Medication discussion topics (clinician-facing)", "pill")
    for m in guidelines.medication_discussion():
        theme.rec_block(m["topic"], m["point"], m["reference"]["citation"])
    theme.card_close()

    theme.card_open("Full ESC reference list", "book")
    for ref in guidelines.ESC_REFERENCES:
        st.markdown(
            f'<div class="cai-rec"><b>{ref["id"]}</b>'
            f'<div class="cai-muted">{ref["citation"]}</div>'
            f'<div class="cai-ref">DOI: {ref["doi"]}</div></div>',
            unsafe_allow_html=True)
    theme.card_close()


def admin_mode():
    theme.hero("Admin & audit",
               "Session audit trail, data governance and model provenance.",
               "Admin mode")

    if not st.session_state.get("admin_ok"):
        theme.card_open("Restricted area", "shield")
        st.markdown('<div class="cai-muted">Admin tools include the audit log '
                    "and data controls. Enter the prototype PIN to continue.</div>",
                    unsafe_allow_html=True)
        pin = st.text_input("Admin PIN", type="password")
        if st.button("Unlock", type="primary"):
            if pin == config.ADMIN_PIN:
                st.session_state["admin_ok"] = True
                history.log_audit("admin_unlock", "Admin")
                st.rerun()
            else:
                st.error("Incorrect PIN. Access denied.")
        st.caption("Prototype PIN for demonstration: cardio2026")
        theme.card_close()
        return

    audit = history.audit_df()
    theme.metric_row([
        ("list", str(len(audit)), "Audit events"),
        ("pulse", str(len(history.history_full())), "Predictions"),
        ("gear", config.VERSION, "App version"),
    ])
    st.write("")

    theme.card_open("Audit log", "list")
    st.markdown('<div class="cai-muted">Chronological record of actions in this '
                "session. No patient health data is persisted server-side.</div>",
                unsafe_allow_html=True)
    if audit.empty:
        st.info("No audit events yet.")
    else:
        st.dataframe(audit.iloc[::-1], use_container_width=True, hide_index=True)
        st.download_button("Export audit log (CSV)",
                           audit.to_csv(index=False).encode(),
                           "cardioai_audit.csv", "text/csv")
    theme.card_close()

    theme.card_open("Data governance", "shield")
    st.markdown(
        '<div class="cai-muted">'
        "<b>Storage:</b> assessments live only in the browser session and are "
        "lost on refresh - nothing is written to a server database.<br>"
        "<b>Minimisation:</b> no names or identifiers are collected.<br>"
        "<b>Positioning:</b> research prototype, not a CE-marked device; not "
        "clinically validated.<br>"
        f"<b>Data source:</b> {config.DATASET_SOURCE}"
        "</div>", unsafe_allow_html=True)
    theme.card_close()


def _empty(title, body):
    st.markdown(
        f'<div class="cai-card" style="text-align:center;padding:40px">'
        f'{theme.icon("chart",34)}<h3 style="justify-content:center">{title}</h3>'
        f'<div class="cai-muted">{body}</div></div>', unsafe_allow_html=True)
    st.write("")
